---
name: testing-local-ui-fullstack
description: How to run the full Resland stack locally for UI/browser testing — Next dev + FastAPI with Auth0 bypassed via a minted __session cookie and a localhost JWKS server, real Postgres schema via prisma db init, moto as S3, and seeding a complete onboarded user. Complements testing-amqp-stack (which covers dispatcher-only smoke tests without the frontend or auth).
---

# Full-stack UI testing for Resland (frontend + API + auth + S3)

## Devin Secrets Needed
None for a fully local run. `OPENROUTER_API_KEY` is only needed if a real LLM agent run must complete; without it tailor/suggestion runs land in `WAITING_FOR_INPUT` with a "Something went wrong — send any message" pending question, which itself is a valid pipeline proof.

## Stack bring-up (all host-side, localhost ports)
- Infra: `docker compose up -d amqp postgres` (see testing-amqp-stack skill). Docker Hub needs allowlisting (registry-1.docker.io, auth.docker.io, production.cloudfront.docker.com).
- Real schema (preferred over the amqp skill's hand-built minimal tables when the API/frontend are in scope): `cd frontend && DATABASE_URL=postgres://resland:resland@localhost:5432/resland pnpm prisma db init` — applies all `migrations/app/*` including new feature tables.
- `frontend/.env.local` (untracked, create it): `DATABASE_URL`, `NEXT_PUBLIC_API_BASE_URL=http://localhost:3001`, `APP_BASE_URL=http://localhost:3000`, `AUTH0_DOMAIN=<any well-formed domain, e.g. devin-test.us.auth0.com>` (`.local` TLDs are rejected by the Auth0 SDK domain validation), `AUTH0_CLIENT_ID/SECRET=<anything>`, `AUTH0_AUDIENCE=<aud>`, `AUTH0_SECRET=<64+ chars>` — you need to KNOW the secret to mint the cookie.
- Frontend: `cd frontend && pnpm dev` (port 3000). Google Fonts fetch may fail sandboxed — next/font warns and falls back, non-fatal.

## Auth0 bypass (the hard part — works end to end)
The frontend uses Auth0 v4 `__session` JWE cookie (alg=dir, enc=A256GCM, CEK = `hkdf(sha256, AUTH0_SECRET, "", "JWE CEK", 32)`); the API independently verifies RS256 JWTs via PyJWKClient at `https://{AUTH0_DOMAIN}/.well-known/jwks.json`.
1. Stand up a local JWKS issuer: generate an RSA key, sign a token (`iss=https://<host>:<port>/`, `aud=<AUTH0_AUDIENCE>`, `sub=auth0|<tester id>`, exp +24h), serve `jwks.json` over HTTPS. Python 3.14 requires the CA cert to have `basicConstraints=critical,CA:TRUE` AND `keyUsage=critical,keyCertSign,cRLSign` (a bare CA:TRUE self-signed cert is rejected). Run the API with `SSL_CERT_FILE=<ca.pem>` so urllib trusts it, and `AUTH0_DOMAIN=<host>:<port>` (the API accepts a port; the frontend SDK does not need to reach it).
2. Mint the browser cookie in pure node:crypto: encrypt `{"user":{"sub","email","name","sid"},"tokenSet":{"accessToken":"<the RS256 JWT>","expiresAt","scope"},"internal":{"sid","createdAt"}}` as a compact JWE with dir/A256GCM and the derived CEK. `getAccessToken` returns the embedded token without a network call when it is unexpired and there is no refreshToken — so the JWT inside the cookie must match the key your JWKS server currently serves (regenerate cookie + token together).
3. Inject the cookie: `document.cookie` does NOT work on non-HTML documents and the cookie is HttpOnly-ish in behavior — the reliable trick is that cookies are host-scoped (port-independent): run a 5-line HTTP server on `localhost:9999` that responds `Set-Cookie: __session=<jwe>; Path=/; SameSite=Lax` + `Location: http://localhost:3000/dashboard`, then navigate the browser to it once. Every subsequent request to :3000 carries the session.
4. Verify with curl: `curl -b "__session=<jwe>" localhost:3000/dashboard` renders (200), and `curl -H "Authorization: Bearer <jwt>" localhost:3001/tailored` returns 200 — proves both halves before touching the browser.

## S3 stand-in for export paths
- `uvx --from 'moto[server]' moto_server -p 5000` + `AWS_ENDPOINT_URL=http://localhost:5000 S3_RESUME_BUCKET=resumes-test AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_REGION=us-east-1` on the API. boto3 honors AWS_ENDPOINT_URL; create the bucket once (`aws --endpoint-url http://localhost:5000 s3 mb s3://resumes-test`). Export POSTs then really upload a docx and return a presigned localhost URL the browser downloads — verify content by unzipping `word/document.xml` and grepping for markers.

## Seeding a usable user
- The API reads the `user` table by `auth0_id` (= token `sub`). Seed `auth0_id='auth0|devin-tester'`, `balance_cents>0` (POST /tailor returns 402 at zero), `has_onboarded=true`, `full_name`, plus base experiences + bullets, categorized `user_base_skill` rows, education, project, social link — everything the resume/document pipeline joins.
- To exercise "completed run" UI without a live agent: submit a real run via the UI (proves publish→dispatcher→status writeback), then `UPDATE user_tailor_run SET status='COMPLETED', result='<TailorRunResult JSON>'` — resubmitting the form returns the same active run (IN PROCESSING/WAITING_FOR_INPUT/COMPLETED are all "active") and renders the result panel.

## Gotchas
- `start_tailor` reuses an existing active run for the user — a leftover test row makes a new POST return the old run instead of publishing a job.
- Next.js client Router Cache + server re-writing the session cookie can serve stale accessTokens after you re-mint: prefer full document reloads, and if API calls 401 in the browser while curl works, re-set the cookie via the redirect server.
- The dispatcher only needs `AMQP_URL` + `PG_URL`; the API needs those plus `AUTH0_DOMAIN`, `AUTH0_AUDIENCE`, `SSL_CERT_FILE`, and the AWS/S3 vars.
