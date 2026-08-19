# ADR-004: Multi-tenancy & Authorization

Status: Accepted
Date: 2026-08-19

## Context

STACKUP must be multi-tenant from day one, even with a single real user
today. The domain must never be modeled as `User → Costs` directly; every
cost-bearing entity must hang off a `Workspace`. Authorization must never
trust a `workspace_id` sent by the client.

## Decision

- Every tenant-scoped table carries `workspace_id` (directly or
  transitively via a FK chain: `Application → Environment`,
  `Application/Environment → CostItem`, etc.).
- On every authenticated request, FastAPI resolves the caller's
  `WorkspaceMember` rows from the session (never from a request body or
  query param) and builds the set of workspace IDs the caller may act on.
- A single **policy/authorization module** (`core/policy.py`) centralizes
  role→permission checks. Route handlers call `require(user, workspace,
  action)`; no ad-hoc `if role == "admin"` checks scattered across
  controllers.
- Roles (fixed set for MVP): `owner`, `admin`, `member`, `viewer`.
  - `owner`: full control, including ownership transfer and workspace
    deletion.
  - `admin`: manage applications/costs/vendors/services/members, cannot
    change ownership or delete the workspace.
  - `member`: create/update operational data (applications, environments,
    costs, expenses, evidence) they have access to.
  - `viewer`: read-only.
- Every query resolving a single resource by ID additionally filters by
  the caller's authorized workspace set at the database layer (not just
  checked in application code after fetching) — an ID for another
  workspace returns 404, not 403, to avoid leaking existence.
- `AuditEvent` records actor, workspace, entity, action, before/after, and
  request_id for privileged mutations (member role changes, deletions,
  ownership transfer).

## Consequences

- Every new endpoint must go through the policy module — enforced via code
  review and an integration test suite that asserts cross-workspace access
  is denied for every resource type (see Phase 9 security tests).
- Slightly more query complexity (always joining/filtering on
  workspace_id) in exchange for authorization that cannot be bypassed by a
  crafted request body.
