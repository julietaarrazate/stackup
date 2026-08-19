# ADR-009: Money and Currency Modeling

Status: Accepted
Date: 2026-08-19

## Context

Cost data is the core value of the product; correctness of money handling
is not negotiable. Float arithmetic is explicitly forbidden by the product
requirements, and original currency must never be destroyed by conversion.

## Decision

- All monetary columns are PostgreSQL `NUMERIC(14, 2)` (via SQLAlchemy's
  `Numeric` mapped to Python `Decimal` — never `float` anywhere in the
  domain, API schemas, or Cost Engine).
- Every monetary value is stored as an `(amount, currency)` pair; currency
  is an ISO 4217 3-letter code. Initial supported set: USD, ARS, EUR, BRL,
  MXN, stored as data (a `Currency` reference, not a hardcoded enum) so the
  set can grow without a migration touching business logic.
- `Workspace.base_currency` is used only for **reporting aggregation**
  (e.g. "total monthly cost" across items in different currencies). The
  underlying `CostItem`/`CostHistory`/`Expense` rows always retain their
  original `(amount, currency)` — conversion happens at query/report time,
  never by overwriting stored data.
- `ExchangeRate` (base_currency, quote_currency, rate, source,
  effective_at) is modeled in the domain from Phase 4 but its automated
  population (external FX API) is out of scope for the MVP; until then,
  reports that mix currencies either group by currency or use a
  manually-entered rate — never a silent 1:1 assumption.
- The Cost Engine (ADR referenced in architecture overview) is the single
  place that computes `monthly_equivalent`, `annualized_cost`, and
  currency-aware aggregates — never duplicated in frontend code.

## Consequences

- Every API schema (Pydantic) for a monetary field uses `Decimal` with
  explicit quantization rules (2 decimal places), and JSON serialization
  emits it as a string to avoid float round-tripping in JS.
- Frontend formatting (locale, symbol) is purely presentational; it never
  re-derives amounts, only formats numbers already computed by the backend.
