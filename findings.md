# NeuroVenue OS — Research Findings

> **Last Updated:** 2026-04-10  
> **Status:** Active — Ongoing Research

---

## Table of Contents

1. [Domain Analysis](#1-domain-analysis)
2. [Competitive Landscape](#2-competitive-landscape)
3. [Technical Spikes](#3-technical-spikes)
4. [Data Source Research](#4-data-source-research)
5. [Open Questions](#5-open-questions)

---

## 1. Domain Analysis

### 1.1 What is Venue Intelligence?

Venue intelligence refers to the practice of aggregating, analyzing, and scoring data about physical spaces to enable smarter decision-making for event planners, venue operators, and marketplace platforms. It sits at the intersection of:

- **Geospatial data** — location, accessibility, surrounding infrastructure
- **Operational data** — capacity, amenities, availability, pricing
- **Sentiment data** — reviews, ratings, social media mentions
- **Behavioral data** — booking patterns, occupancy rates, seasonal trends

### 1.2 Target Users

| Persona | Pain Point | What NeuroVenue OS Solves |
|---------|-----------|--------------------------|
| **Event Planner** | Comparing venues manually across scattered platforms | Unified scoring and comparison dashboard |
| **Venue Operator** | No visibility into competitive positioning | Benchmarking and actionable improvement insights |
| **Platform Builder** | Needs venue data API for their own product | Embeddable intelligence via API |

### 1.3 Key Domain Concepts

- **Venue** — A registered physical space with attributes (capacity, amenities, location).
- **Event** — A time-bound activity linked to a venue.
- **Score** — A multi-dimensional, AI-generated assessment of venue quality.
- **Pipeline** — An automated workflow that ingests data, processes it, and outputs scores.
- **Signal** — A single data point contributing to a score (e.g., a review, a safety report).

---

## 2. Competitive Landscape

> ⚠️ **Status:** Pending deep research (Task NV-006)

### 2.1 Known Players

| Platform | Focus | Differentiator | Gap |
|----------|-------|---------------|-----|
| Peerspace | Venue marketplace | Large inventory | No intelligence layer |
| Splacer | Unique venues | Curated, creative spaces | Manual curation; no scoring |
| VenueScanner | Venue search | UK-focused aggregation | Limited analytics |
| Tripleseat | Venue management | Ops + CRM for venue operators | Operator-only; not multi-sided |

### 2.2 Potential Differentiators for NeuroVenue OS

- **AI-native scoring** — Not just search, but quantified intelligence.
- **Schema-first API** — Designed for developers to embed, not just end users to browse.
- **Multi-dimensional analysis** — Safety, accessibility, atmosphere, logistics, value (not a single star rating).
- **Real-time pipeline** — Scores update as new data arrives, not quarterly.

---

## 3. Technical Spikes

### 3.1 Scoring Algorithm Design

> **Status:** Not started

**Approaches to evaluate:**
- **Weighted linear model** — Simple, interpretable, easy to tune.
- **Embedding-based similarity** — Use venue embeddings to find "venues like this" patterns.
- **Bayesian rating** — Handle venues with very few reviews more fairly.

**Decision criteria:**
1. Interpretability (can we explain why a score is X?)
2. Data-efficiency (works with sparse data)
3. Update-ability (incremental scoring without full recomputation)

### 3.2 Tech Stack Candidates

> **Status:** Not started (Task NV-007)

| Layer | Option A | Option B | Option C |
|-------|----------|----------|----------|
| Runtime | Node.js 20 | Bun 1.x | Deno 2.x |
| API Framework | Hono | Express 5 | Fastify |
| ORM | Drizzle | Prisma | Kysely |
| Database | PostgreSQL 16 | CockroachDB | — |
| Frontend | Next.js 15 | Astro + React | — |
| Auth | Clerk | Auth.js | Custom JWT |
| Hosting | Vercel | Railway | Fly.io |
| CI/CD | GitHub Actions | — | — |

---

## 4. Data Source Research

### 4.1 Potential External Data Sources

| Source | Data Type | Access Method | Cost |
|--------|-----------|--------------|------|
| Google Places API | Reviews, ratings, location | REST API | Paid (usage-based) |
| Yelp Fusion API | Reviews, ratings, photos | REST API | Free tier available |
| OpenStreetMap | Geospatial, amenity data | Overpass API | Free |
| Social media APIs | Mentions, sentiment | Various | Varies |
| Public safety databases | Incident reports, compliance | Government APIs | Free |

### 4.2 Data Pipeline Architecture (Preliminary)

```
External APIs → Ingestion Workers → Raw Data Store → 
Transform Pipeline → Normalized Signals → Scoring Engine → 
Venue Scores DB → API Layer → Frontend
```

---

## 5. Open Questions

| # | Question | Priority | Status |
|---|----------|----------|--------|
| Q1 | Should scores be real-time or batch-computed? | 🔴 High | Open |
| Q2 | Multi-tenant from day one, or single-tenant MVP? | 🔴 High | Open |
| Q3 | What's the minimum number of signals needed for a reliable score? | 🟡 Medium | Open |
| Q4 | Do we need a map view in the MVP? | 🟡 Medium | Open |
| Q5 | How do we handle venues with no external data? | 🟡 Medium | Open |
| Q6 | Should the API be public from launch or private beta? | 🟢 Low | Open |
| Q7 | Do we need real-time WebSocket updates for the dashboard? | 🟢 Low | Open |

---

> **Next Steps:** Conduct deep research on competitive landscape (NV-006) and finalize tech stack (NV-007). Update this document with findings.
