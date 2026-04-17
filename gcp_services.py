"""
NeuroVenue OS — Google Cloud Services
======================================
Singleton module that owns all GCP client initialization and exposes
structured helpers used by the Flask server layer.

Services:
  - Google Cloud Logging  (structured log ingestion via API)
  - Google Cloud Firestore (simulation run persistence)

Graceful degradation:
  When Application Default Credentials are unavailable (local dev without
  gcloud auth application-default login), logging falls back to stdout and
  Firestore writes are silently skipped with a one-time warning.
"""

import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Optional

# ──────────────────────────────────────────────
# Cloud Logging
# ──────────────────────────────────────────────

_cloud_logging_ready = False
_gcp_logger: Optional[logging.Logger] = None
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "neurovenue-os")
SERVICE_NAME = os.environ.get("K_SERVICE", "neurovenue-os-local")

def _init_cloud_logging() -> logging.Logger:
    """Attach the google-cloud-logging handler to the root Python logger.

    This routes all Python log records to Cloud Logging via the API,
    enriched with structured JSON payloads and resource labels.
    Returns a named child logger for NeuroVenue OS.
    """
    global _cloud_logging_ready

    try:
        import google.cloud.logging as gcp_logging
        from google.cloud.logging_v2.handlers import CloudLoggingHandler

        client = gcp_logging.Client(project=PROJECT_ID)

        # Attach Cloud Logging handler to the root logger — all log calls
        # in the process will be captured and shipped as structured entries.
        handler = CloudLoggingHandler(client, name="neurovenue-os")
        handler.setLevel(logging.DEBUG)

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        # Avoid duplicate handlers on hot-reload
        if not any(isinstance(h, CloudLoggingHandler) for h in root_logger.handlers):
            root_logger.addHandler(handler)

        _cloud_logging_ready = True
        logger = logging.getLogger("neurovenue-os")
        logger.info(
            "Cloud Logging initialized",
            extra={
                "json_fields": {
                    "service": SERVICE_NAME,
                    "project": PROJECT_ID,
                    "event": "startup",
                }
            },
        )
        return logger

    except Exception as exc:
        # Fallback: use plain stdout logger
        fallback = logging.getLogger("neurovenue-os")
        if not fallback.handlers:
            fallback.addHandler(logging.StreamHandler())
        fallback.setLevel(logging.INFO)
        fallback.warning(
            f"[gcp_services] Cloud Logging unavailable — falling back to stdout. "
            f"Run `gcloud auth application-default login` to enable. Reason: {exc}"
        )
        return fallback


def get_logger() -> logging.Logger:
    """Return the initialized NeuroVenue Cloud Logger (singleton)."""
    global _gcp_logger
    if _gcp_logger is None:
        _gcp_logger = _init_cloud_logging()
    return _gcp_logger


# ──────────────────────────────────────────────
# Firestore
# ──────────────────────────────────────────────

_firestore_client = None
_firestore_lock = threading.Lock()
_firestore_warned = False

COLLECTION_RUNS = "simulation_runs"
PERSIST_EVERY_N_TICKS = int(os.environ.get("FIRESTORE_PERSIST_EVERY_N_TICKS", "10"))


def _init_firestore():
    """Initialize and return the Firestore client (singleton)."""
    global _firestore_client, _firestore_warned

    if _firestore_client is not None:
        return _firestore_client

    with _firestore_lock:
        # Double-checked locking
        if _firestore_client is not None:
            return _firestore_client

        try:
            from google.cloud import firestore  # type: ignore

            client = firestore.Client(project=PROJECT_ID)
            _firestore_client = client
            get_logger().info(
                "Firestore client initialized",
                extra={
                    "json_fields": {
                        "project": PROJECT_ID,
                        "collection": COLLECTION_RUNS,
                        "event": "firestore_ready",
                    }
                },
            )
            return client

        except Exception as exc:
            if not _firestore_warned:
                _firestore_warned = True
                get_logger().warning(
                    f"[gcp_services] Firestore unavailable — persistence skipped. "
                    f"Reason: {exc}"
                )
            return None


# ──────────────────────────────────────────────
# Public helpers
# ──────────────────────────────────────────────


def log_simulation_run(
    tick: int,
    phase: str,
    zones: list,
    predictions: dict,
    route: Optional[dict] = None,
) -> None:
    """Persist a simulation snapshot to Firestore and emit a structured log.

    This runs on a background daemon thread so it never blocks the API response.

    Document schema:
        run_id          : str   — UUID v4
        timestamp       : str   — ISO-8601 UTC
        tick            : int
        phase           : str
        metrics         : dict  — aggregated KPIs
        zones_snapshot  : list  — full zone telemetry at this tick
        route           : dict  — optional routing context

    Only persists every PERSIST_EVERY_N_TICKS ticks (default: 10) to
    avoid unnecessary Firestore writes during rapid polling.
    """
    if tick % PERSIST_EVERY_N_TICKS != 0:
        return

    def _write():
        # ── Build metrics ────────────────────────────────────────────────
        congestion_scores = [z.get("congestion_score", 0) for z in zones]
        top_zones = sorted(zones, key=lambda z: z.get("congestion_score", 0), reverse=True)
        all_risk_zones = []
        for horizon in predictions.values() if predictions else []:
            all_risk_zones.extend(horizon)

        metrics = {
            "max_congestion_score": round(max(congestion_scores), 2) if congestion_scores else 0,
            "avg_congestion_score": round(
                sum(congestion_scores) / len(congestion_scores), 2
            ) if congestion_scores else 0,
            "top_congested_zones": [z["id"] for z in top_zones[:3] if z.get("congestion_score", 0) > 40],
            "predicted_risk_zones": list(set(all_risk_zones)),
            "zone_count": len(zones),
        }

        # ── Emit structured Cloud Log ────────────────────────────────────
        get_logger().info(
            f"[tick={tick}] phase={phase} max_congestion={metrics['max_congestion_score']}",
            extra={
                "json_fields": {
                    "event": "simulation_tick",
                    "tick": tick,
                    "phase": phase,
                    "metrics": metrics,
                }
            },
        )

        # ── Write to Firestore ───────────────────────────────────────────
        db = _init_firestore()
        if db is None:
            return

        run_id = str(uuid.uuid4())
        document = {
            "run_id": run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tick": tick,
            "phase": phase,
            "metrics": metrics,
            "zones_snapshot": zones,
            "route": route or {},
        }

        try:
            db.collection(COLLECTION_RUNS).document(run_id).set(document)
            get_logger().debug(
                f"Firestore write OK — run_id={run_id}",
                extra={"json_fields": {"event": "firestore_write", "run_id": run_id}},
            )
        except Exception as exc:
            get_logger().error(
                f"Firestore write failed: {exc}",
                extra={"json_fields": {"event": "firestore_error", "error": str(exc)}},
            )

    # Fire-and-forget on a daemon thread — never blocks the HTTP response
    thread = threading.Thread(target=_write, daemon=True)
    thread.start()


def get_recent_runs(limit: int = 20) -> list:
    """Fetch the most recent simulation run documents from Firestore.

    Returns an empty list if Firestore is unavailable or an error occurs.
    Documents are ordered by timestamp descending.
    """
    db = _init_firestore()
    if db is None:
        return []

    try:
        query = (
            db.collection(COLLECTION_RUNS)
            .order_by("timestamp", direction="DESCENDING")
            .limit(limit)
        )
        docs = query.stream()
        return [doc.to_dict() for doc in docs]

    except Exception as exc:
        get_logger().error(
            f"Firestore query failed: {exc}",
            extra={"json_fields": {"event": "firestore_query_error", "error": str(exc)}},
        )
        return []
