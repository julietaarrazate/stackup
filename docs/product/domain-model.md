# STACKUP — Domain Model

All monetary fields are `NUMERIC(14,2)` + `currency CHAR(3)` (see ADR-009).
No entity below is ever deleted physically once it has associated history;
soft-close via `status`/`end_date` instead (see individual notes).

## User

Managed by `fastapi-users`. `id, email, hashed_password, is_active,
is_verified, created_at, updated_at`.

## Workspace

`id, name, slug (unique), base_currency, timezone, created_at, updated_at`

## WorkspaceMember

`id, workspace_id, user_id, role (owner|admin|member|viewer), created_at,
updated_at`. Unique on `(workspace_id, user_id)`.

## Application

`id, workspace_id, name, slug, description, status (active|archived),
production_url, repository_url, logo, created_at, updated_at`. Unique on
`(workspace_id, slug)`.

## Environment

`id, application_id, name, type (development|staging|production|other),
url, created_at, updated_at`.

## Vendor

`id, name, slug (unique), website, logo, category, created_at, updated_at`.
Not hardcoded in the UI — seeded as data, extensible by any workspace
member with permission (e.g. Vercel, Neon, Render, Cloudinary, Sentry,
GitHub, Resend, Cloudflare).

## Service

`id, vendor_id, name, slug, category, website, created_at, updated_at`.
A Vendor has many Services (e.g. Vercel → Hobby/Pro/Enterprise).

## CostItem

The core entity.

```
id, workspace_id, application_id, environment_id (nullable),
service_id, name, description, category,
billing_type (fixed|usage|one_time),
amount NUMERIC(14,2), currency CHAR(3),
frequency (weekly|monthly|quarterly|yearly|custom),
status (active|paused|ended),
certainty (confirmed|estimated|projected),
start_date, end_date (nullable), notes,
created_at, updated_at
```

Invariants (property-tested, see roadmap Phase 9):
- `monthly_equivalent` and `annualized_cost` are pure functions of
  `(amount, frequency)` — e.g. yearly amount / 12 = monthly equivalent;
  monthly amount × 12 = annualized.
- `environment_id`, when present, must belong to `application_id`.
- `application_id` must belong to `workspace_id`.
- Ending a CostItem never deletes it or its `CostHistory`/`Expense` rows.

## CostHistory

`id, cost_item_id, amount, currency, effective_from, effective_to
(nullable), reason, created_at`. Append-only ledger of price changes for a
CostItem (e.g. Vercel Pro USD 20 → USD 25).

## Expense

Separates *what something costs* (CostItem) from *what was actually paid*
(Expense).

`id, workspace_id, cost_item_id, amount, currency, paid_at, status,
invoice_number (nullable), evidence_id (nullable), created_at, updated_at`.

## Evidence

`id, workspace_id, type (invoice|receipt|contract|screenshot|other),
filename, storage_key, mime_type, size, created_at`. `storage_key` points
to a private Cloudflare R2 object; `filename` is user-facing metadata only
and is never trusted as a filesystem path or content-type source (see
ADR-006).

## AuditEvent

`id, actor_user_id, workspace_id, entity, entity_id, action, before
(jsonb), after (jsonb), created_at, request_id, metadata (jsonb)`. Written
for privileged mutations: member role changes, ownership transfer,
deletions/archival, workspace settings changes. No secrets or full
Evidence file contents are ever stored here.

## Future entities (domain reserved, not built in MVP)

- `ExchangeRate` (base_currency, quote_currency, rate, source,
  effective_at) — see ADR-009.
- `BackgroundJob` (id, type, status, idempotency_key, attempt_count,
  last_error, payload, created_at, updated_at) — see ADR-005; built in
  Phase 7 but the table is designed alongside CostItem so nothing about
  jobs forces a schema rewrite later.
- Repository/integration entities for GitHub analysis (Phase 8): a
  `Detection` concept (application, source=github, detected service,
  confidence, confirmed_at) that a user must explicitly confirm before it
  becomes a real `CostItem` — detections are never auto-promoted to costs.
