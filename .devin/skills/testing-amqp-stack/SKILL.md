---
name: testing-amqp-stack
description: How to smoke-test the Resland AMQP job pipeline (RabbitMQ + dispatcher + Postgres) locally — service bring-up, env vars, seeding a minimal DB schema, publishing test jobs, and verifying ack/DLQ/reconnect behavior.
---

# Testing the AMQP stack (Resland backend)

## Devin Secrets Needed
None required for the AMQP/DLQ/reconnect paths. Real LLM calls need `OPENROUTER_API_KEY`; real resume parsing needs AWS creds + S3 bucket.

## Bring up services
- `docker compose up -d amqp postgres` from repo root starts RabbitMQ (5672 + mgmt 15672) and Postgres (5432, user/pass/db all `resland`). Images: `rabbitmq:4-management`, `postgres:18`.
- Docker Hub needs allowlisted: `registry-1.docker.io`, `auth.docker.io`, `production.cloudfront.docker.com` (blob CDN — cloudFront, not cloudflare), `docker.io`.
- RabbitMQ mgmt UI: http://localhost:15672 guest/guest (guest is localhost-only; host-side connections work, container-to-container does NOT).
- No `backend/dispatcher/.env` exists in a fresh checkout — export env vars instead. Run dispatcher on the host (not compose) with `localhost` hostnames:
  `cd backend/dispatcher && AMQP_URL=amqp://guest:guest@localhost:5672/ PG_URL=postgres://resland:resland@localhost:5432/resland PYTHONUNBUFFERED=1 uv run dispatcher`
  (PYTHONUNBUFFERED is required or handler/runner print() output never reaches the terminal when piped.)
- Dispatcher now declares all topology itself on startup (exchanges, durable queues, `#` topic bindings, x-dead-letter-exchange args) — no api needed first.
- Verify: `docker exec resland-amqp-1 rabbitmqctl list_queues name messages consumers` / `list_exchanges` / `list_bindings`; or the mgmt UI Queues tab (DLX feature tag) / queue detail page (x-dead-letter-exchange, bindings, consumer count).

## Minimal DB schema for handler tests
No SQL migrations exist in the repo — schema is Prisma-Next contracts (`frontend/prisma/contract.prisma`). For dispatcher smoke tests, create the ~11 tables the runners touch with plain TEXT/INT columns (the dispatcher uses psycopg directly, no enums needed): `user`, `user_upload_job`, `user_base_experience`, `user_base_experience_bullet`, `user_social_link`, `user_base_skill`, `user_base_education`, `user_base_project`, `user_suggestion`, `user_tailor_run`, `model_pricing` (may be empty), `token_usage`.
- Seed a `user_suggestion` row (+ experience + bullet; the fetch uses an INNER join on bullets, so a session with no bullets returns "Session not found").
- With no OPENROUTER_API_KEY / empty model spec, a seeded suggestion or tailor job runs the real runner, the agent call raises, the runner writes `pending_question`/`status='WAITING_FOR_INPUT'` and returns cleanly → job COMPLETED → message **acked**. This is the cheapest way to prove the positive settle path end-to-end.
- Unknown session_id/run_id/user_id → runner raises → FAILED → `nack(requeue=False)` → lands in the matching `*-dlq` via the DLX.
- Malformed JSON / missing id field → handler nacks immediately (no runner started) → DLQ.

## Publishing test jobs
Use the real shared path: `uv run --package shared python your_publish.py` — `AmqpClient("amqp://guest:guest@localhost:5672/")`, `setup(declare_topology=False)`, `get_publisher("<name>-exchange", "#")`, `publish(AmqpSuggestionJob(session_id=...).to_message())`. Job dataclasses: AmqpResumeJob(s3_key, job_id, user_id) → resume-parser-exchange; AmqpSuggestionJob(session_id, answer) → bullet-sugg-exchange; AmqpTailorJob(run_id, answer) → tailor-exchange.

## Reconnect resilience test
`docker restart resland-amqp-1` while the dispatcher runs. Expect `CONNECTION_FORCED ... 'shutdown'` in logs, then "Reconnecting after 5 seconds"; consumers return to 1 per work queue (~5-10s after broker healthy) and a fresh publish is consumed. Exchanges are non-durable auto_delete — robust channels re-declare them on reconnect; durable queues + persistent messages survive.

## Gotchas
- tmux mouse mode is off by default — pane clicks do NOT switch focus; use Ctrl+B + arrow keys. Typed text into the dispatcher pane goes to the running process's stdin (harmless echo).
- `rabbitmqctl` commands print `Timeout: 60.0 seconds ...` noise but still work.
- Non-persistent messages are lost on broker restart even in durable queues — app code publishes via `to_message()` (PERSISTENT), so only hand-crafted raw messages drop.
- `uv run` from repo root doesn't resolve `dispatcher`/`api` scripts — run from the package dir or use `uv run --package <pkg> python ...`.
