# Free Tier Audit

Verified against provider documentation and pricing pages, August 2026.
Re-verify before final production deployment — free tiers change.

| Service | Purpose | Free tier | Relevant limits | Expiration? | Persistence? | At limit | Upgrade path | Migration required? |
|---|---|---|---|---|---|---|---|---|
| **Vercel** (Hobby) | Frontend hosting (apps/web) | Free, **non-commercial only** | 100GB fast data transfer/mo, 1M edge requests/mo, 6,000 build-exec minutes/mo, 1M function invocations/mo, 4 CPU-hrs function compute/mo, 360 GB-hrs function memory/mo, 200 projects, 100 deploys/day | No time-based expiration | N/A (compute, not data) | Project pauses; no silent overage billing | Vercel Pro, $20/seat/mo | No — same deploy target, just plan upgrade |
| **Render** (web service) | FastAPI API host | Free (shared 750 instance-hrs/mo across free services in the workspace) | Spins down after 15 min idle → cold start on next request | No | N/A (compute) | Requests queue behind a cold start; no hard cutoff observed at MVP scale | Paid instance type (always-on) | No — same service, resize instance type |
| **Render** (background worker) | arq worker | Same free instance-hour pool as above | Same idle/cold-start behavior — acceptable since jobs are async, not user-facing | No | N/A | Same | Paid instance type | No |
| **Render PostgreSQL** | **NOT USED** — explicitly prohibited | Free tier expires 30 days after creation + 14-day grace, then Render **deletes the database and all data** | — | **Yes, 30 days** | **No — data loss on expiry** | Database becomes inaccessible, then deleted | N/A — we do not use this | N/A |
| **Neon** | Primary PostgreSQL (all persistent app data) | Free | 100 CU-hours/mo compute, 0.5GB storage/project, up to 10 branches/project, up to 100 projects, scale-to-zero | Free-plan projects may be reclaimed after an extended period of inactivity (Neon's stated policy references ~90 days) | Yes, durable, until reclaimed for inactivity | Compute throttles/pauses at CU exhaustion; storage cap blocks new writes | Neon paid plan (Launch tier and above) | No — same connection string shape, same schema |
| **Upstash Redis** | Job queue broker, cache, rate limiting | Free | 256MB data, 500,000 commands/mo, 10GB bandwidth/mo | No | Yes, durable (not in-memory-only like Render KV) | Requests over quota are rejected/billed depending on plan settings | Upstash Pay-as-you-go / fixed plans | No — same Redis URL |
| **Cloudflare R2** | Evidence file storage | Free | 10GB storage/mo, 1M Class A ops/mo (writes), 10M Class B ops/mo (reads), $0 egress always | No | Yes, durable | New writes fail past storage cap; can still read | R2 paid usage (still $0 egress) | No — same bucket/API |
| **Sentry** (Developer) | Error tracking + basic perf monitoring, web + api | Free forever | 5,000 errors/mo, 10,000 performance units/mo, 30-day retention, **1 user seat** | No | 30-day retention only | New events dropped once monthly cap hit; no charge | Sentry Team plan | No — same DSN |
| **GitHub Actions** | CI (lint/typecheck/test/build/e2e) | Free (private repo) | 2,000 Linux minutes/mo, 500MB artifact storage; public repos are unmetered | No | N/A | Runs blocked/billed past quota | GitHub Team ($4/user/mo → 3,000 min) or per-minute overage | No |

## Explicit risks called out

1. **Vercel Hobby is contractually non-commercial.** STACKUP as a real
   product (even used personally to track Oído/Cuadra costs) is arguably
   fine on Hobby while it's a personal tool, but the moment it's offered
   commercially it must move to Pro. Flag this before any commercial
   launch — do not treat this as a technical migration only.
2. **Never use Render's free PostgreSQL**, per explicit product
   requirement — enforced architecturally (Neon is the only Postgres
   target in every environment, including local dev via a Neon branch).
3. **Neon free-tier inactivity reclamation**: mitigated by real usage;
   if the project is expected to sit idle for a long stretch, upgrade
   first rather than risk reclamation.
4. **Sentry's 1-seat limit** means a second developer needs their own
   Sentry account or the org needs to upgrade — plan for this before
   inviting a collaborator.
5. No component here is assumed to remain free forever; every row above
   has a documented, code-unchanged upgrade path.
