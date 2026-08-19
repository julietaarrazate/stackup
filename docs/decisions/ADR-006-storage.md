# ADR-006: Object Storage (Evidence)

Status: Accepted
Date: 2026-08-19

## Context

Invoices, receipts, contracts, and screenshots (`Evidence`) must not live
on Render's ephemeral filesystem and must not be publicly accessible.

## Decision

Use **Cloudflare R2** (S3-compatible API) as the object store.

- Free tier (verified August 2026): 10 GB storage/month, 1,000,000 Class A
  operations/month (writes: PutObject, multipart, etc.), 10,000,000 Class B
  operations/month (reads), **$0 egress** on all classes.
- Bucket is private; objects are never served with a public URL.
- Upload flow: FastAPI validates MIME type, extension, and size
  server-side (never trusts the client-supplied filename/content-type),
  generates a random `storage_key` (not the user's filename), stores the
  object, and records `Evidence` metadata in Postgres.
- Download flow: FastAPI issues a short-lived **presigned URL** scoped to
  the requesting user's authorized workspace; the browser fetches directly
  from R2 using that URL.
- Max upload size is environment-configurable (`MAX_UPLOAD_SIZE_MB`),
  defaulting to a conservative value for the free tier.

## Consequences

- R2's zero-egress pricing means viewing/downloading evidence never
  incurs bandwidth cost even as usage grows — the free tier's real
  constraint is the 10 GB storage cap, which is generous for
  invoices/receipts (small files) at MVP scale.
- Moving to a paid R2 tier later requires no code change — only quota
  changes on Cloudflare's side.
