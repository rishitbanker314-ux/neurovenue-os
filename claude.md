# NeuroVenue OS — Project Constitution

> **Version:** 0.1.0  
> **Last Updated:** 2026-04-10  
> **Status:** Draft — Pre-Development

---

## 1. Project Identity

**NeuroVenue OS** is an AI-native operating layer for venue intelligence. It transforms raw venue data into actionable insights through neural pipelines, enabling operators, planners, and platforms to make smarter decisions about physical spaces.

---

## 2. Core Invariants

These rules are **non-negotiable** and must hold true across every phase of development:

| # | Invariant | Rationale |
|---|-----------|-----------|
| I-1 | **No application code shall be written before the architecture document is approved.** | Prevents rework and scope drift. |
| I-2 | **Every data model must have a corresponding JSON Schema definition in `gemini.md`.** | Single source of truth for all structured data. |
| I-3 | **All API contracts are schema-first.** Design the interface before the implementation. | Enables parallel frontend/backend development. |
| I-4 | **No direct database queries in route handlers.** All data access goes through a service layer. | Separation of concerns; testability. |
| I-5 | **Every feature must map to a task in `task_plan.md` before work begins.** | Traceability from requirement → implementation. |
| I-6 | **All environment secrets are loaded from `.env` files, never hardcoded.** | Security hygiene. |
| I-7 | **Commits must reference a task ID** (e.g., `[NV-012] Add venue scoring pipeline`). | Audit trail and traceability. |
| I-8 | **Progress and blockers are logged in `progress.md` at the end of every work session.** | Institutional memory; async collaboration. |

---

## 3. Coding Standards

### 3.1 Language & Runtime
- **Primary Language:** TypeScript (strict mode)
- **Runtime:** Node.js 20+ / Bun (to be decided in Phase 1)
- **Frontend:** React 19+ with Next.js App Router (if applicable)
- **Styling:** Vanilla CSS with design tokens — no utility-class frameworks unless explicitly approved

### 3.2 Naming Conventions
| Element | Convention | Example |
|---------|-----------|---------|
| Files (components) | PascalCase | `VenueCard.tsx` |
| Files (utilities) | camelCase | `scoreCalculator.ts` |
| Files (schemas) | camelCase + `.schema` | `venue.schema.ts` |
| Directories | kebab-case | `venue-intelligence/` |
| Constants | UPPER_SNAKE_CASE | `MAX_VENUE_CAPACITY` |
| Database tables | snake_case (plural) | `venue_scores` |
| API routes | kebab-case | `/api/v1/venue-scores` |

### 3.3 Error Handling
- All async functions must use explicit `try/catch` or `Result<T, E>` patterns.
- No swallowed errors. Every catch block must log or propagate.
- User-facing errors return structured JSON: `{ error: string, code: string, details?: object }`.

### 3.4 Testing
- Unit tests are **mandatory** for all service-layer functions.
- Integration tests are **mandatory** for all API endpoints.
- Minimum coverage target: **80%** (enforced in CI).

---

## 4. Documentation Rules

| Document | Purpose | Update Cadence |
|----------|---------|----------------|
| `claude.md` | Project constitution, rules, invariants | On architectural changes |
| `gemini.md` | JSON Schema definitions for all data models | On every model change |
| `task_plan.md` | Phases, milestones, task breakdown | On every planning session |
| `findings.md` | Research notes, competitive analysis, technical spikes | As discoveries are made |
| `progress.md` | Session logs, blockers, decisions | End of every session |

---

## 5. Git Workflow

```
main          ← production-ready, protected
  └── develop ← integration branch
       ├── feature/NV-XXX-description
       ├── fix/NV-XXX-description
       └── spike/NV-XXX-description
```

- **Branch Protection:** `main` and `develop` require PR reviews.
- **Merge Strategy:** Squash merges into `develop`; merge commits into `main`.
- **Commit Format:** `[NV-XXX] <type>: <description>` where type is `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.

---

## 6. Decision Log

> Record significant architectural or technical decisions here.

| Date | Decision | Context | Alternatives Considered |
|------|----------|---------|------------------------|
| 2026-04-10 | Initialize documentation-first approach | Prevent scope drift and ensure alignment before code | Jump straight to code (rejected) |

---

## 7. Guiding Principles

1. **Documentation before code.** If it isn't written down, it doesn't exist.
2. **Schema-first design.** Models are the foundation — build outward from data.
3. **Incremental complexity.** Start simple, add layers only when validated by need.
4. **Observable by default.** Every system component should expose health and metrics.
5. **Secure by default.** Authentication, authorization, and input validation are not afterthoughts.
