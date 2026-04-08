# Longevity OS — Design Spec
**Date:** 2026-04-07  
**Status:** Approved

---

## Overview

A personal longevity system running on a Raspberry Pi 5, accessible via browser over Tailscale. Three parallel tracks:

- **Track A (primary):** Biological longevity — biomarker tracking, tiered intervention protocols, research synthesis
- **Track B:** Digital continuity — knowledge/memory preservation, foundation for future AI persona
- **Track C:** Systemic OS — the application itself, orchestrating all data, protocols, and knowledge

The system starts with what the user has now (Garmin Fenix 7X Sapphire Solar, Garmin Index, BP monitor, basic supplements) and is designed to grow as interventions escalate and new data sources are added. An existing health tracking app (`health-at-home`) will be integrated or replaced in a later phase.

---

## User Profile

- **Age:** 31
- **Devices:** Garmin Fenix 7X Sapphire Solar, Garmin Index smart scale, manual BP monitor
- **Current protocols:** Multivitamin, cod liver oil (daily). Right arm physio ongoing — upper body exercise limited.
- **Intervention philosophy:** Evidence-based first, tiered by cost and evidence grade. Willing to escalate to cutting-edge/experimental over time.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Raspberry Pi 5                      │
│                                                     │
│  ┌─────────────┐    ┌──────────────────────────┐   │
│  │   FastAPI   │◄───│   Background Workers      │   │
│  │  (port 8000)│    │  - Garmin sync (hourly)   │   │
│  └──────┬──────┘    │  - Research digest (daily)│   │
│         │           └──────────────────────────┘   │
│  ┌──────▼──────┐    ┌──────────────────────────┐   │
│  │   SQLite    │    │   Claude API              │   │
│  │  (primary)  │    │  (research synthesis)     │   │
│  └─────────────┘    └──────────────────────────┘   │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │         React Frontend (port 3000)           │   │
│  │    served locally, accessed via browser      │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
         ▲                        ▲
    Garmin Connect API       Manual inputs
    (Fenix 7X, Index)        (BP, supplements,
                              journal entries)
```

**Key decisions:**
- FastAPI for backend — Python ecosystem is ideal for future biostatistics/ML
- SQLite to start — no ops overhead, easily migrated to Postgres later
- React + Vite frontend — rich interactive dashboard, accessible from any device via Tailscale
- Claude API for research synthesis — evidence grading and protocol recommendations
- No cloud dependency for personal data — everything stays on the Pi

---

## Modules

### Module 1 — Data Ingestion
Pulls from all sources into a unified timeline.

- **health-at-home bridge (primary):** Calls `http://100.70.55.16:49999/api/health?days=N` — the existing Apple Health dashboard already running on the local network. Provides: steps, active energy, resting HR, heart rate (min/avg/max), sleep stages (Deep/REM/Core/Awake), weight, BMI, body fat, distance, dietary macros, walking metrics. 90 days of historical data available.
- **Garmin Connect API (fallback):** Used only for metrics not in Apple Health — primarily HRV and VO2 max. Requires `garminconnect` Python library + credentials.
- **Manual entry:** BP readings, supplement doses taken, symptoms, energy/mood (1–10)
- **CSV import:** Blood panels (Medichecks, Thriva, or similar)
- Runs hourly via APScheduler; full historical backfill on first run

### Module 2 — Biomarker Dashboard
Time-series visualisation of all tracked metrics.

- Charts: HRV, sleep quality, VO2 max, weight, body fat %, BP, resting HR
- Correlation overlay: intervention events plotted against biomarker trends
- Baseline report auto-generated after 30 days of data
- Built with Recharts

### Module 3 — Protocol Engine (Track A core)
The tiered intervention system.

- **Protocol library** with fields: name, evidence grade (A/B/C), cost tier (£/££/£££), mechanism, references
- **Tier 1 (now — low cost, strong evidence):**
  - Sleep: 7–9 hrs, consistent timing, dark/cool room, no screens -1hr
  - Exercise: Zone 2 cardio (150+ min/week), strength training 2x/week (modified for arm physio), VO2 max intervals monthly
  - Diet: Mediterranean-adjacent, time-restricted eating consideration, protein 1.6g/kg
  - Supplements review: multivitamin assessed, cod liver oil (Omega-3/Vit D confirmed), add magnesium glycinate, creatine
- **Tier 2 (when Tier 1 is stable — moderate cost):**
  - Regular blood biomarker panels (Medichecks Advanced Well Man or similar, 2x/year)
  - NMN or NR (500mg/day — NAD+ precursor, reasonable human data)
  - CGM trial (2-week Libre sensor to understand glucose response)
  - Consider adding: Vitamin D (if deficient on panel), Omega-3 at therapeutic dose
- **Tier 3 (experimental — to review when science matures):**
  - Low-dose rapamycin (mTOR inhibitor — most compelling longevity drug in animal models, early human data)
  - Senolytics (dasatinib + quercetin — clears senescent cells, limited human data)
  - Peptides (BPC-157, TB-500 — repair/recovery, mostly anecdotal)
  - Plasma-inspired interventions, partial reprogramming (watch space — 5–10 year horizon)
- **Daily checklist:** supplement compliance, sleep target met, exercise completed
- **Compliance tracking** feeds into biomarker correlation

### Module 4 — Research Synthesis Engine
Keeps protocols current without requiring constant manual research.

- Weekly digest: Claude API synthesises new PubMed papers + curated sources
- Curated sources: Examine.com, Hallmarks of Aging literature, Bryan Johnson protocols, Peter Attia/Andrew Huberman synthesis, Longevity Subreddit signal
- Per-intervention summaries with evidence grade and last-updated date
- Flags new research relevant to active protocols

### Module 5 — Knowledge Preservation (Track B foundation)
Building the structured dataset that captures who the user is over time.

- **Daily journal** with structured prompts: decisions made, beliefs updated, what mattered, energy/mood rating
- **Belief snapshots:** versioned, timestamped statements of values, opinions, and worldview
- **Memory index:** searchable log of significant experiences, relationships, and perspectives
- **Export:** full data as structured JSON — raw material for a future AI persona or digital twin
- Privacy: all data local, never sent to external services (except Claude API for synthesis, which gets no personal journal data)

### Module 6 — Digital Continuity (Track B advanced — Phase 4)
The "failing that" failsafe.

- Conversation interface seeded with Module 5 data
- Periodic fine-tuning or rich-prompt construction from accumulated knowledge base
- Not built in Phase 1–3; Module 5 collects the training data in the meantime
- Goal: a model that can represent the user's knowledge, values, and perspective with fidelity

---

## Data Model

```
BiomarkerReading
  id, source (garmin|manual|import), metric, value, unit, recorded_at

ProtocolEntry
  id, protocol_id, date, complied (bool), notes

Intervention
  id, name, tier (1|2|3), evidence_grade (A|B|C), cost_tier (1|2|3),
  mechanism, references[], started_at, ended_at

JournalEntry
  id, date, body (text), tags[], belief_snapshot (JSON), mood (1-10), energy (1-10)

ResearchDigest
  id, generated_at, source, summary, interventions_mentioned[], raw_response
```

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Backend | FastAPI + Python 3.12 | Async, lightweight, excellent data science ecosystem |
| Task queue | APScheduler | Simple cron-style jobs, no Redis needed |
| Database | SQLite + SQLAlchemy | Zero ops, sufficient for personal use, easy to migrate |
| Frontend | React + Vite + shadcn/ui | Fast builds, excellent component library |
| Charts | Recharts | Composable, React-native |
| AI | Anthropic SDK (Claude Sonnet) | Research synthesis + future digital twin |
| Garmin | `garminconnect` Python library | Well-maintained unofficial API |

---

## Build Phases

| Phase | Scope | Goal |
|---|---|---|
| 1 | Garmin ingestion + biomarker dashboard + protocol checklist | Usable system in days |
| 2 | Research synthesis + correlation analysis + blood panel CSV import | Intelligence layer |
| 3 | Knowledge preservation (journal + belief snapshots + export) | Track B foundation |
| 4 | Digital continuity module + health-at-home integration | Long-term continuity |

---

## Out of Scope (for now)

- Mobile app (browser via Tailscale is sufficient)
- Multi-user support
- Cloud hosting (Pi-local only)
- Automated supplement ordering
- Direct BP monitor API (manual entry for now)
- health-at-home integration (Phase 4)
