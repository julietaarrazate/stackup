# ADR-003: Authentication

Status: Accepted
Date: 2026-08-19

## Context

Requirements: production-grade auth (registration, login, logout, email
verification, password reset/change, session revocation, rate limiting,
secure HttpOnly/Secure/SameSite cookies, no sensitive tokens in
localStorage, CSRF protection where relevant), no homemade auth, and a
single chosen solution documented here. The user specifically asked to
evaluate **Better Auth** and **Auth.js/NextAuth**.

Research findings (August 2026):

- **Better Auth** is a TypeScript-only, framework-agnostic auth library. It
  expects to own the database/session logic from a JS/TS runtime. Our
  backend of record is FastAPI (Python) holding the domain model
  (Workspace, WorkspaceMember, etc.) — bolting Better Auth on would mean
  either running a second Node auth service as the source of truth (extra
  moving part, extra infra, session state split across two databases) or
  not using it for what it's designed for. Poor fit.
- **Auth.js/NextAuth** is designed to be the source of truth *inside*
  Next.js itself (its own session/JWT, its own adapter to a database).
  Using it with a separate FastAPI backend requires either duplicating
  session validation (a FastAPI dependency that decrypts Auth.js JWTs) or
  keeping two overlapping notions of "who is logged in." It's built for
  Next.js-owns-auth architectures, which is not ours (FastAPI owns the
  domain and must independently authorize every request, including from
  future non-Next.js clients like background jobs or a future public API).
- **fastapi-users**: a mature, actively maintained library built
  specifically for FastAPI + SQLAlchemy. Provides registration, login,
  logout, email verification, password reset, cookie transport, hashing
  (argon2/bcrypt via passlib), and pluggable user models — i.e. everything
  the requirements ask for, without writing auth primitives by hand.

## Decision

Use **fastapi-users** as the single authentication solution, with FastAPI
as the sole source of truth for sessions, and Next.js acting as a
BFF that forwards the session cookie:

1. Next.js Route Handlers proxy `/auth/*` and API calls to FastAPI
   server-side.
2. FastAPI sets the session cookie (`HttpOnly`, `Secure` in production,
   `SameSite=Lax`, scoped to the parent domain `stackup.ar` so it is valid
   for both `app.stackup.ar` and `api.stackup.ar`).
3. The browser only ever sees an opaque HttpOnly cookie — never a token it
   can read or that ends up in localStorage.
4. CSRF: since the API only accepts the session cookie together with a
   custom header set by same-origin fetches from the Next.js BFF (and
   enforces `SameSite=Lax` + strict CORS to the single first-party
   origin), classic form-based CSRF against FastAPI is not exploitable;
   state-changing endpoints additionally require the custom header as a
   defense-in-depth double-submit check.
5. Rate limiting on `/auth/login`, `/auth/register`, `/auth/forgot-password`
   via the Redis-backed limiter (ADR-005's Upstash Redis instance).

## Consequences

- Auth logic lives entirely in `apps/api`, reusable if a future client
  (mobile app, CLI, public API) needs to authenticate without going
  through Next.js.
- Next.js never needs its own user/session table — one source of truth,
  simpler to audit and to reason about workspace authorization (ADR-004).
- We take on a Python dependency (`fastapi-users`) instead of an
  ecosystem-standard JS one; acceptable since the domain and authorization
  boundary already live in Python.

## Implementation notes (as built in Phase 2)

- Version pinned: `fastapi-users[sqlalchemy]` 15.x.
- Transport: `CookieTransport` (HttpOnly; Secure in every non-local
  environment; SameSite=Lax; cookie name `stackup_session`; parent-domain
  scoped via `COOKIE_DOMAIN` so it is valid across app/api subdomains).
- Strategy: `DatabaseStrategy` over an `access_token` table — sessions are
  server-side and **revocable**: logout deletes the row and the session is
  invalid immediately (satisfies the session-revocation requirement; a
  self-contained JWT could not do this).
- Rate limiting on `login`/`register`/`forgot-password` via an in-memory
  fixed-window limiter today; a Redis (Upstash) backend replaces the store
  in Phase 5+ without touching call sites (ADR-005).
- `AUTH_SECRET` signs reset/verification tokens and is rejected at startup
  if left at the dev default in staging/production.

## Risk: fastapi-users is in maintenance mode (recorded 2026-08)

As of the 15.x line, fastapi-users is in **maintenance mode** — security
and dependency updates continue, but no new features, and the maintainers
have signalled a successor Python auth toolkit is being worked on.

- **Why we still chose it:** it is mature, security-maintained, and
  purpose-built for exactly FastAPI + SQLAlchemy; the requirements forbid
  homemade auth; and the two named alternatives are worse fits (Better Auth
  is TypeScript-only; NextAuth/Auth.js expects to own auth inside Next.js).
  For an MVP that needs register/login/logout/reset/verify/revocable
  sessions today, it is the lowest-risk option that satisfies the brief.
- **Mitigation / migration path:** our design already isolates the blast
  radius. Sessions are plain rows in `access_token`; users are plain rows
  in `user`; the cookie is a standard HttpOnly session cookie; and every
  authorization decision lives in our own `core/policy.py` and
  `get_workspace_context`, not in the auth library. Replacing fastapi-users
  later (with its successor or another library) means swapping the
  register/login/session plumbing behind the same cookie contract, with the
  domain, policy, and BFF untouched. Revisit when the successor reaches a
  stable release.
