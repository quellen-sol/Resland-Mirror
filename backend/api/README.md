# api

Resland's FastAPI service: Auth0 JWT auth, uploads, job submission over AMQP, tailored
resumes, the memory bank, Stripe billing, admin, and account export and deletion. It never
calls a model itself; the [dispatcher](../dispatcher/) runs the agents.

```bash
uv run api            # http://localhost:3001 (OpenAPI docs at /docs)
uv run pytest --cov
```

The [root README](../../README.md) covers how it fits together, and [`AGENTS.md`](../../AGENTS.md)
covers the local setup and test database.
