# stackup-web

Next.js (App Router, TypeScript strict) frontend for STACKUP, deployed on
Vercel. Acts as a BFF in front of FastAPI (see
`../../docs/decisions/ADR-001-architecture.md`): server components and route
handlers call the backend server-side and forward the session cookie; the
browser never talks to FastAPI directly.

## Local development

```bash
cd apps/web
pnpm install
cp ../../.env.example .env.local   # set API_BASE_URL to the FastAPI URL
pnpm dev
```

## Quality checks (what CI runs)

```bash
pnpm lint
pnpm typecheck
pnpm build
```

## Layout

```
app/          App Router routes, layout, global styles (design tokens)
app/api/      Route Handlers = the BFF proxy to FastAPI
components/    UI components (own STACKUP visual identity)
lib/          server-only API client
```

TypeScript is pinned to 5.9 (not the newly-released 7.0) for ecosystem/ESLint
compatibility with Next 16; revisit once the lint toolchain fully supports 7.
