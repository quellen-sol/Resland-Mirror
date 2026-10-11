# Resland frontend

The Next.js 16 app (App Router, React 19) for Resland. The [root README](../README.md)
covers the architecture, and [`AGENTS.md`](AGENTS.md) is worth reading before changing
anything here: Next 16 differs from most Next.js docs and examples.

```bash
pnpm install
cp .env.example .env.local   # Auth0, database and API values
pnpm dev                     # http://localhost:3000, expects the API on :3001
pnpm test                    # node --test over the files listed in package.json
pnpm lint
npx tsc --noEmit
```

- The database schema is the Prisma-Next contract in [`prisma/contract.prisma`](prisma/contract.prisma).
  [`prisma-next.md`](prisma-next.md) covers the workflow.
- All calls to the backend API go through [`lib/api.ts`](lib/api.ts).
- The DSA study center's content is in [`content/dsa`](content/dsa/README.md).
