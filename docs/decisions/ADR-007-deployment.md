# ADR-007: Deployment & Regions

Status: Accepted
Date: 2026-08-19

## Context

The user asked us to verify current Render and Neon region availability and
choose the pairing that minimizes latency between Render (FastAPI) and Neon
(PostgreSQL) specifically — the hot path hit multiple times per request —
rather than optimizing purely for end-user distance.

Verified (August 2026):

- Render regions: Oregon, Ohio, Virginia, Frankfurt, Singapore. No South
  America region exists.
- Neon regions include (AWS-backed): `aws-us-east-1` (N. Virginia),
  `aws-us-east-2` (Ohio), `aws-us-west-2` (Oregon), `aws-eu-central-1`
  (Frankfurt), `aws-eu-west-2` (London), `aws-ap-southeast-1` (Singapore),
  `aws-ap-southeast-2` (Sydney), `aws-sa-east-1` (São Paulo). Neon's Azure
  regions are deprecated and out of scope.

## Decision

- Render web service + worker: region **Virginia**.
- Neon project: region **`aws-us-east-1` (N. Virginia)**.

These are the same metro area, minimizing round-trip time for every
database call FastAPI makes within a request — the dominant latency cost
for this application, since a single dashboard/report request can issue
several sequential queries.

Since Render has no São Paulo region, there is no pairing that also
minimizes latency to end users in Argentina; that tradeoff is accepted for
MVP (see Risks in the architecture overview) and revisited only if/when
Render adds a South American region or the backend moves providers.

Vercel requires no region choice for the frontend — its edge network
serves static/cacheable content close to the user regardless; only the
server-side calls from Next.js to FastAPI benefit from FastAPI↔Neon
proximity, which this decision optimizes.

## Consequences

- Argentina-based end users will see a latency floor of roughly 150-200ms
  to Render/Neon in Virginia, on top of the Vercel edge hop. Acceptable
  for MVP; documented as a known limitation, not silently ignored.
- If Render ever adds a South America region, migrating both Render and
  Neon there is a configuration change (new services + Neon project in
  the new region + data migration), not a rearchitecture.
