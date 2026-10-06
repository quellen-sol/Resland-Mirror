# AGENTS.md — working in this repo as an agent

Resland is a resume-tailoring product: users upload a resume, the API queues jobs over AMQP,
and LangGraph-based agents in the dispatcher generate tailored documents and suggestions.

This file is the root guide for **automated/agentic contributors**. Package-level pointers:
`frontend/AGENTS.md` (Next.js agent rules — read it before touching the frontend), and the
testing playbooks in `.devin/skills/`.

## Repo map

```
backend/api/          FastAPI app (auth, billing/Stripe, uploads, job submission)   -> pytest
backend/dispatcher/   AMQP consumers + LangGraph agents (tailor, suggestions, parsers) -> pytest
backend/shared/       Shared library: AMQP client, job dataclasses, pdfdoc, db helpers -> pytest
frontend/             Next.js 16 app (UI, Auth0, Prisma-Next contract)              -> node --test
terraform/            Infra definitions
compose.yml           Local stack: api, dispatcher, amqp (rabbitmq:4-management), postgres:18
deploy.sh             Build + push image to ECR, force ECS redeploy (us-east-2), cluster resland-live
Dockerfile            Single image for both api and dispatcher (`uv run api` / `uv run dispatcher`)
docs/                 Design docs (billing plan, UX specs)
.devin/skills/        Rich testing playbooks — read the relevant one before deep testing work
```

### Data + messaging
- **Schema is a Prisma-Next contract**: `frontend/prisma/contract.prisma`. There are **no SQL
  migrations** — apply it with `cd frontend && pnpm prisma db init`. Generated artifacts
  (`contract.json`, `contract.d.ts`) are committed; regenerate rather than hand-edit.
- **RabbitMQ topology is declared by the dispatcher on startup** (exchanges, durable queues,
  `#` topic bindings, DLX args) — no need to start the API first.
- Job dataclasses live in `backend/shared` (`AmqpResumeJob`, `AmqpSuggestionJob`, `AmqpTailorJob`).
- **LangGraph checkpointer tables live in the `langgraph` Postgres schema**, not `public`, created by
  the dispatcher on startup (`dispatcher.pg.do_pg_setup`). `prisma db update` only reads the schemas
  the contract declares and drops tables there that it doesn't model, so keep them out of `public`
  and out of the contract. Raw SQL goes through `shared.checkpoints.CHECKPOINT_TABLES`.
- `token_usage` is an append-only ledger, one row per job (`@@unique([job_kind, job_id])`), recording
  `model` + charged `amount_cents`; billing/admin aggregates read from it.
- **Account deletion** (`DELETE /account`, `backend/api/src/api/account/`) keeps `balance_purchase` and
  `token_usage` rows but re-points them at a PII-free tombstone user (`deleted|<uuid4>`, see
  `shared.accounts`); everything else is deleted. A new table that references `user` (directly or
  through another user-owned table) must be added to `account.db.ERASED_TABLES` (or
  `REPOINTED_TABLES`) and to the data export in `account.model.EXPORT_SECTIONS` — live-schema tests
  in `backend/api/tests/test_account_pg.py` fail until it is.

## Toolchain

| Thing | Version |
|---|---|
| Python | 3.14 (uv workspace, `[tool.uv.workspace] members = ["backend/*"]`) |
| uv | current; each package is its own dist (`uv_build`) |
| Node | 24 |
| pnpm | 10.33.0 (pinned `packageManager`) |
| Postgres | 18 (compose + CI service) |
| RabbitMQ | 4 (`rabbitmq:4-management`, mgmt UI :15672) |
| Lint | ruff (repo-root `.ruff.toml`, `BLE001` ignored) via `./ruff-fix-all.sh` |
| Frontend lint | `pnpm lint` (eslint-config-next); no typecheck script — run `npx tsc --noEmit` |

## Local bring-up

```bash
docker compose up -d amqp postgres                 # infra (host ports 5672/15672/5432)
cd frontend && pnpm install
cd frontend && DATABASE_URL=postgres://resland:resland@localhost:5432/resland pnpm prisma db init
cd frontend && DATABASE_URL=postgres://resland:resland@localhost:5432/resland_test pnpm prisma db init  # test DB
backend/dispatcher: uv run dispatcher   # or: AMQP_URL=amqp://guest:guest@localhost:5672/ PG_URL=... uv run dispatcher
backend/api:        uv run api          # port 3001
frontend:           pnpm dev            # port 3000
```

`uv run` from the repo root does **not** resolve the `dispatcher`/`api` scripts — run from the
package directory or use `uv run --package <pkg> python ...`.

Set `PYTHONUNBUFFERED=1` when piping dispatcher output, or `print()`/handler logs never appear.

Full-stack UI + Auth0 bypass + moto S3 seeding recipe: `.devin/skills/testing-local-ui-fullstack/SKILL.md`.
Dispatcher/AMQP/DLQ/reconnect smoke test: `.devin/skills/testing-amqp-stack/SKILL.md`.

## Tests

Run per package (they are separate uv packages):

```bash
cd backend/shared     && uv run pytest --cov
cd backend/api        && uv run pytest --cov
cd backend/dispatcher && uv run pytest --cov
cd frontend           && pnpm test          # node --test (explicit file list in package.json)
```

- `asyncio_mode = "auto"` is set in **api only** (`backend/api/pyproject.toml`). Dispatcher/shared
  async tests use `unittest.IsolatedAsyncioTestCase` (no `pytest-asyncio` dependency there).
- Tests default to **fakes**, not live infrastructure. Postgres-dependent tests use `TEST_PG_URL`,
  which **defaults to** `postgres://resland:resland@localhost:5432/resland_test`. They run whenever
  that database is reachable and skip only when it isn't (or when the guard below refuses it).
- ⚠️ **Destructive live-PG fixtures refuse to run** unless the effective database name's last token
  is a scratch marker (`resland_test`, `app-scratch`, `test`…) or `ALLOW_DESTRUCTIVE_TESTS=1` is set
  (see `shared.testing.destructive_db_ok`). When they do run they truncate tables
  (`token_usage`, `model_pricing`, `balance_purchase`, `"user"`, …), so the default is
  `.../resland_test` — never point `TEST_PG_URL` at data you care about.
- `compose.yml` creates `resland_test` via `postgres/init/01-test-db.sql`, but
  `docker-entrypoint-initdb.d` only runs on an **empty data dir** — an existing `db-data` volume
  must be recreated (or the database created by hand) for the test DB to appear.
- `resland_test` starts **empty**: apply the schema to it too (the `resland_test` line in Local
  bring-up) — without it the live-PG fixtures *fail* on missing tables instead of skipping.
- Real LLM calls need `OPENROUTER_API_KEY`; without it agents settle into
  `WAITING_FOR_INPUT`/`pending_question`, which is still a valid end-to-end proof of the pipeline.

## Frontend (Next 16 / React 19)

- **Read `frontend/AGENTS.md` first** — Next 16.3.5 is not the Next in most training data. The
  `<!-- BEGIN:nextjs-agent-rules -->` block there is regenerated by `next dev`; commit it with your
  change rather than deleting it.
- Server components by default; add `"use client"` only where you need state/effects. All API access
  goes through `frontend/lib/api.ts` (typed `ApiError`, `isInsufficientBalance`/`isApiUnreachable`
  helpers) — don't `fetch` the backend ad hoc from components.
- Prisma-Next contract lives in `frontend/prisma/` (`contract.prisma` is the source; `contract.json`
  / `contract.d.ts` are generated and committed). `frontend/prisma-next.md` documents the workflow.
- Tests are plain `node --test` over `frontend/lib/*.test.js` (no Jest/Vitest). Add a file and wire it
  into the `test` script in `frontend/package.json` — the script lists files explicitly, it is not a
  glob.
- Lint with `pnpm lint` (eslint-config-next). There is **no** `typecheck` script — run
  `npx tsc --noEmit` from `frontend/` and report the result in the PR.
- Public pages build their metadata with `pageMetadata()` from `frontend/lib/seo.ts`. Next merges
  metadata shallowly, so a page that sets `openGraph` by hand drops the share image and anything
  that only sets `title` inherits the home page's share tags. New public pages also go in
  `app/sitemap.ts`, and a new dynamic app route with a per-user id (like `/tailored/[id]`) goes in
  `ID_ROUTES` in `frontend/lib/traffic.ts` so the id stays out of the `page_view` log.
- The public DSA study center (`/dsa`) is content in `frontend/content/dsa` — read its README
  before adding or editing a topic. Each example is a runnable program in five languages;
  `pnpm test:dsa-examples` runs them all (needs `node`, `python3`, `go`, `dotnet` 10 and `java`
  on PATH, and skips a missing toolchain) and `pnpm test:dsa-links` checks the LeetCode links.
  Neither is part of `pnpm test`, so run them when you touch `content/dsa`.

## CI (`pull_request` → master)

`.github/workflows/pr-ci.yml` runs a single `backend-tests` job:
Postgres 18 service → `pnpm install --frozen-lockfile` (frontend install exists **only** to provide
the Prisma CLI) → `pnpm prisma db init` → `uv lock` → `uv run --frozen pytest --cov` for
**shared, api, dispatcher** in that order.

Notes for agents:
- CI runs `uv lock` before testing because dev-group additions have landed without a re-locked
  `uv.lock` while PyPI was unreachable. If you add dependencies, run `uv lock` and commit the result.
- CI does **not** currently run frontend tests, eslint, or `tsc`. Run them locally and say so in the PR.
- `uvx ruff` may be unreachable in sandboxed environments; if so, verify style by other means and
  state the limitation in the PR instead of silently skipping.

## Preferred development process

For any non-trivial change, work in this order — it keeps the contract explicit and the tests honest:

1. **Determine the schema for this change** — decide the data shape first (the Prisma-Next contract,
   API request/response models, AMQP message dataclasses) and agree the interface before writing
   behaviour.
2. **Dummy logic/functions** — stub the signatures with the real types and return shapes.
3. **Tests** — write the tests against those stubs first. They should fail for the right reason, not
   because the module doesn't import.
4. **Fully implemented logic** — fill the stubs in until the tests pass.
5. **Then test everything** — all three backend suites (`shared`, `api`, `dispatcher`) plus frontend
   lint/`tsc`, and the full-stack flows where they apply.

Steps 1-3 are cheap and catch design mistakes while they're still free; a PR that jumped straight to
step 4 gets sent back.

## Conventions

- **Never commit to `master` directly.** Branch, push, open a PR; the human owner merges.
- **Always open a PR for your changes** — don't wait to be asked. Once a change is done and tested,
  branch, commit, push, and open a PR against `master`, then report the link. Uncommitted edits
  or local-only commits aren't finished work.
- Branch naming: `fix/<issue>-slug`, `feat/<issue>-slug`, `docs/<issue>-slug`, or the Devin agent
  convention `devin/<epoch>-slug`. Keep one issue per branch.
- Commit messages: imperative subject, body explains *why*. Reference the issue (`Refs #63`).
- Keep diffs tight: no drive-by reformatting or dependency bumps unrelated to the change.
- Python: ruff config is authoritative (`BLE001` — blind `except Exception` — is intentionally
  allowed; don't "fix" it). Prefer typed dataclasses in `shared` over ad-hoc dicts across the wire.
- Frontend: **read `frontend/AGENTS.md` and `frontend/node_modules/next/dist/docs/` first** — Next 16
  differs from most training data. Server components by default; keep API access in `lib/api.ts`.
- Secrets: never commit `.env`/`.env.local` or credentials. AWS/OpenRouter/Stripe/Auth0 values are
  injected at runtime (ECS task definitions / local env files, both untracked).
- Deploys: `./deploy.sh` is owner-run; agents build and test locally only unless explicitly asked.

## Reviewing

- Reviewers commandeer PRs, they don't rewrite them: leave review comments with `file:line` and a
  concrete suggestion, or push a follow-up commit on the author's branch after saying so in the PR.
- Bot collaborators post their summaries in `#bot-lab` and cross-review each other's PRs.

## Known pitfalls

- Live-PG test fixtures truncate tables and **refuse to run** unless the target DB is a scratch/test
  database (or `ALLOW_DESTRUCTIVE_TESTS=1`); see Tests above.
- `frontend/AGENTS.md` contains a `next dev`-managed block — it is regenerated on every dev run;
  don't delete it from diffs, commit it with your change.
- RabbitMQ `guest` is localhost-only: host-side connections work, container-to-container does not.
- A `user_suggestion` row needs at least one bullet — the fetch INNER-joins bullets and otherwise
  reports "Session not found".
- Non-persistent AMQP messages are lost on broker restart even in durable queues; always publish
  via the shared `to_message()` path (PERSISTENT).
