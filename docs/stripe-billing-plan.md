# Stripe billing — integration & testing plan

Plan for taking the prepaid-balance Stripe integration from code-complete to
production. One rule governs everything below: **users are charged exactly for
what they use, credited exactly for what they pay, and never charged or
credited twice for the same event.**

## 1. How billing works today

LLM usage is metered against a prepaid USD balance — `user.balance_cents`, a
`Decimal` holding fractional cents so sub-cent charges still count.

### Purchase flow

1. `GET /billing/packs` returns the server-side `TOKEN_PACKS` catalog
   (`backend/api/src/api/billing/model.py`). The client only sends a `pack_id`,
   so price and grant amounts can never be tampered with. `cents` is balance
   granted, `amount_cents` is the Stripe charge; the difference is the bulk
   bonus.
2. `POST /billing/checkout` (`billing/service.py::create_checkout`) takes a row
   lock on the user (`FOR UPDATE`), creates the Stripe customer on first use
   (`user.stripe_customer_id`), creates a Checkout Session
   (`mode="payment"`, `client_reference_id=<auth0_id>`,
   `metadata={pack_id, cents}`), inserts a `PENDING` `balance_purchase` row
   keyed by the Stripe session id, and returns the hosted-checkout URL.
3. Stripe calls `POST /stripe/webhook` — unauthenticated, verified by
   `STRIPE_WEBHOOK_SECRET` signature instead (`billing/service.py::handle_webhook`):
   - `checkout.session.completed`: upserts the purchase row (the webhook can
     beat the checkout endpoint's own INSERT), records the session's
     `payment_intent` on the row, flips `PENDING → COMPLETED`, and credits
     `balance_cents` — all in one transaction. Only a `PENDING` row
     transitions, so a redelivered event can't double-credit.
   - `checkout.session.expired`: marks the row `EXPIRED`.
   - `charge.refunded`: on a **full** refund (`amount_refunded == amount`),
     flips `COMPLETED → REFUNDED` and claws back the granted cents, floored
     at 0. Partial refunds and already-refunded rows are no-ops.
   - Events without our `client_reference_id`/`cents` metadata are
     acknowledged and ignored.
4. Frontend `/billing` (`frontend/app/(protected)/billing/`) renders packs,
   balance, and purchase history; after `?checkout=success` it polls for ~12s
   so the webhook credit lands without a manual refresh.
   `components/balance-chip.tsx` links there from the nav.

### Usage flow

1. Starting a paid job (`/suggestions`, `/tailor`) goes through
   `balance.py::require_balance` — `402 insufficient_balance` at zero balance.
   The frontend catches 402 and shows a "Top up" toast linking to `/billing`.
2. `validate_model_choice` whitelists a user-picked model against the
   `model_pricing` table; free-form model specs never reach `init_chat_model`.
3. When a dispatcher task finishes (`runners/suggestions.py`,
   `runners/tailor.py`), `record_token_usage` (`runners/db_ops.py`) writes one
   `token_usage` ledger row and debits `balance_cents` in a transaction,
   floored at 0 (`GREATEST(0, ...)`) — an overrunning job still completes and
   the balance never goes negative. The insert is
   `ON CONFLICT (job_kind, job_id) DO NOTHING`, so a job re-run after AMQP
   redelivery charges once, never twice.
4. Charge amount: actual OpenRouter cost (`fetch_generation_cost_cents`, with
   one retry per generation) × `COST_MARKUP` (1.25). If any generation lookup
   fails, the whole job falls back to the `model_pricing` rate card —
   partially-resolved jobs never underbill; if the model isn't in the card,
   `FALLBACK_CENTS_*` applies so unpriced models never run free. Amounts are
   `ceil`ed to 1/10,000¢ so sub-cent usage never rounds down to zero.
5. `/admin/*` (`admin/service.py`) exposes read-only per-user
   purchased/used balances, usage by model/kind/day, the recent ledger, and
   revenue; `PUT/DELETE /admin/models/{id}` manages the rate card.

## 2. Money-safety invariants (do not regress)

- Hosted Stripe Checkout — card data never touches Resland.
- Server-side pack catalog; the webhook credits `metadata.cents` we set at
  session creation, never a client-supplied amount.
- Webhook signature verification; both checkout and the webhook 503 when
  Stripe env vars are missing rather than failing open.
- Idempotent top-up: `balance_purchase.id` is the Stripe session id, and only
  the `PENDING → COMPLETED` transition credits.
- Idempotent charge-back: only `COMPLETED → REFUNDED` claws back, and only on
  a full refund.
- Idempotent usage debit: `token_usage` is unique on `(job_kind, job_id)`;
  AMQP `accept`s a message only when the job completes, so a crash mid-job
  redelivers it — the second run sees the existing ledger row and skips the
  debit.
- Webhook-before-INSERT race handled by the upsert in `handle_webhook`.
- Stripe customer creation is serialized per user (`FOR UPDATE`) — concurrent
  checkouts can't create duplicate customers.
- Fractional-cent `Decimal` balance; charges round up, never down to free.
- Model whitelist + admin validation (`openrouter:` prefix, non-negative
  rates, default must be enabled).
- Balance gate at job start; mid-run jobs are never interrupted.

## 3. Open questions — decide before launch

1. **Per-job spend cap / estimate.** `require_balance` only checks `> 0`; a
   single job can burn the entire balance (floor at 0 means Resland absorbs
   the overrun). *Decide:* show an estimated cost range before starting,
   and/or cap per-job spend.
2. **Partial refunds** are ignored — a partial refund leaves the purchase
   `COMPLETED`. *Decide:* is that right, or should partial refunds claw back
   proportionally? Also whether `charge.dispute.*` should freeze balances.
3. **Pack catalog is hardcoded.** Price changes require a deploy. Fine for
   launch; revisit if pricing iterates often (alternatives: packs in DB, or
   Stripe Prices + lookup keys).
4. **Webhook observability.** Stripe disables endpoints after sustained
   failures. *Recommend:* alert on non-2xx responses at the LB and on
   `Failed to record token usage` in dispatcher logs; run the reconciliation
   queries in §5.4 periodically.
5. **PENDING rows for abandoned checkouts** rely on
   `checkout.session.expired` to clear; if that event isn't subscribed they
   sit `PENDING` forever (harmless to balances, noise in history).

## 4. Environment setup

| Var | Where | Notes |
| --- | --- | --- |
| `STRIPE_SECRET_KEY` | `backend/api/.env` | `sk_test_...` for dev, `sk_live_...` in prod (terraform var) |
| `STRIPE_WEBHOOK_SECRET` | `backend/api/.env` | `whsec_...` from `stripe listen` (dev) or the dashboard endpoint (prod) |
| `FRONTEND_BASE_URL` | `backend/api/.env` | checkout success/cancel redirect target |
| `NEXT_PUBLIC_API_BASE_URL` | frontend env | e.g. `http://localhost:3001` |

Production (`terraform/api.tf`): `stripe_secret_key` and
`stripe_webhook_secret` are sensitive TF vars. Register the webhook endpoint
in Stripe → Developers → Webhooks: `https://<api-host>/stripe/webhook`,
events `checkout.session.completed`, `checkout.session.expired`,
`charge.refunded`. `FRONTEND_BASE_URL` is `https://resland.org` in terraform —
verify. `MAINTENANCE_MODE` is currently `"1"` in `api.tf` — confirm that's
intentional before launch. Restricted keys are preferable to secret keys if
the API only needs Customer + Checkout write.

## 5. Testing

### 5.1 Local sandbox walkthrough (Stripe test mode)

Stripe "test mode" is the sandbox — `sk_test_`/`whsec_` keys, fake card
numbers, no real money. Full local loop:

```bash
# 1. Stripe CLI: forward webhook events to the local API.
stripe login --api-key sk_test_...          # or interactive login
stripe listen --forward-to localhost:3001/stripe/webhook
#    -> prints "Ready! Your webhook signing secret is whsec_..."
#    -> put it in backend/api/.env as STRIPE_WEBHOOK_SECRET

# 2. backend/api/.env needs at minimum:
#      STRIPE_SECRET_KEY=sk_test_...
#      STRIPE_WEBHOOK_SECRET=whsec_...   (from step 1)
#      PG_URL=postgres://resland:resland@localhost:5432/resland
#      FRONTEND_BASE_URL=http://localhost:3000
#    plus the Auth0/S3/AMQP vars the rest of the API already needs.

# 3. Stack
docker compose up --build                   # api :3001, dispatcher, amqp, postgres
cd frontend && pnpm dev                     # frontend :3000
```

Then drive it like a user:

1. Sign in via Auth0, open `http://localhost:3000/billing` — balance shows $0.
2. Buy **Starter** with test card `4242 4242 4242 4242`, any future expiry,
   any CVC/ZIP → lands on `?checkout=success`. Within ~2s the balance shows
   $5.00 and the purchase row reads `COMPLETED`. `stripe listen` logs the
   `checkout.session.completed` delivery and the API's 200.
3. Declined card `4000 0000 0000 9995` → Stripe shows the failure, no credit;
   the row stays `PENDING` until the session expires.
4. Abandon a checkout → on `checkout.session.expired` the row goes `EXPIRED`
   (checkout sessions live ~24h; force with the dashboard's "Expire session"
   or send a crafted event).
5. **Idempotency**: `stripe events resend evt_...` (or the dashboard's
   "Resend") on the completed event → balance must not double-credit.
6. `stripe trigger checkout.session.completed` sends a synthetic event with
   no Resland metadata — the API should 200-ack and change nothing.
7. **Refund**: `stripe refunds create --charge ch_...` (or dashboard →
   payment → Refund) → `charge.refunded` arrives → row goes `REFUNDED`,
   credit clawed back. A partial refund leaves it `COMPLETED`.
8. Run a suggestion/tailor job → dispatcher logs `Charged X¢ for <job>`;
   `token_usage` gains a row; balance drops. Drain to $0 → the next job gets
   402 → the "Top up" toast appears.
9. Kill and restart the dispatcher mid-job → the message is redelivered, the
   job re-runs, but `record_token_usage` inserts once — no second debit
   (`SELECT * FROM token_usage WHERE job_id = ...` shows one row).

### 5.2 Automated tests

`pytest` suites live in `backend/api/tests/` (webhook/checkout/balance-gate —
Stripe mocked) and `backend/dispatcher/tests/` (`record_token_usage`). They
need a real Postgres — compose's works — and skip when none is reachable:

```bash
docker compose up -d postgres
cd backend/api        && uv run --group dev pytest   # TEST_PG_URL to override
cd ../dispatcher      && uv run --group dev pytest
```

`uv run --group dev` installs pytest via the dev dependency-group; run
`uv lock` once (networked) to refresh `uv.lock`.

Backend coverage now: webhook credit idempotency + redelivery, the
webhook-before-INSERT race, expiry, bad-signature rejection, metadata-less
events, full/partial/refunded-twice refund handling, refund floor at 0,
`require_balance` 402s, `validate_model_choice` whitelist, checkout happy
path + customer reuse + unknown-pack/missing-user/unconfigured-Stripe errors;
rate-card math, actual-cost markup, fallback rate, overrun floor, zero-token
no-op, and the redelivery no-double-charge guard.

Still to add when the harness proves out: concurrency tests (parallel
checkout for one user; parallel `record_token_usage` for one job) — the
unique constraint and row lock make them deterministic to assert.

### 5.3 Failure-injection checks

- Restart the dispatcher mid-job → no second debit (unique `(job_kind, job_id)`).
- Kill the API between `Session.create` and the PENDING insert → the webhook
  upsert still credits correctly.
- Wrong `STRIPE_WEBHOOK_SECRET` → webhook 400s; Stripe retries; no credit.
- `stripe listen` stopped → events queue; on restart, redelivery credits once.

### 5.4 Reconciliation queries (staging/prod, run periodically)

```sql
-- Per-user drift: balance should be >= purchased - used (floor at 0).
-- A negative diff means an overcharge or a missing COMPLETED credit.
SELECT u.auth0_id, u.balance_cents,
       COALESCE(p.purchased, 0) AS purchased, COALESCE(t.used, 0) AS used,
       COALESCE(p.purchased, 0) - COALESCE(t.used, 0) AS expected_min
FROM "user" u
LEFT JOIN (SELECT user_id, SUM(cents) AS purchased FROM balance_purchase
           WHERE status = 'COMPLETED' GROUP BY user_id) p
  ON p.user_id = u.auth0_id
LEFT JOIN (SELECT user_id, SUM(amount_cents) AS used FROM token_usage
           GROUP BY user_id) t
  ON t.user_id = u.auth0_id
ORDER BY (u.balance_cents - (COALESCE(p.purchased,0) - COALESCE(t.used,0))) ASC;

-- Purchases stuck PENDING > 24h (webhook not received / session abandoned).
SELECT * FROM balance_purchase
WHERE status = 'PENDING' AND created_at < now() - interval '24 hours';

-- REFUNDED purchases whose balance couldn't be fully clawed back.
SELECT bp.id, bp.user_id, bp.cents
FROM balance_purchase bp JOIN "user" u ON u.auth0_id = bp.user_id
WHERE bp.status = 'REFUNDED' AND u.balance_cents > 0
  -- recompute check: purchased-active should leave enough to have clawed back
  AND u.balance_cents > (
    SELECT COALESCE(SUM(t.amount_cents),0) FROM token_usage t
    WHERE t.user_id = u.auth0_id
  ) - bp.cents;
```

Also reconcile `balance_purchase` `COMPLETED` totals against the Stripe
dashboard (payments minus refunds) each release cycle.

## 6. Pre-launch checklist

- [ ] Open questions in §3 answered (spend cap, partial-refund policy,
      dispute policy).
- [ ] Live webhook endpoint registered with `checkout.session.completed`,
      `checkout.session.expired`, `charge.refunded`.
- [ ] Live keys set via terraform vars; test keys nowhere near prod env.
- [ ] `MAINTENANCE_MODE` flag reviewed.
- [ ] `TOKEN_PACKS` pricing and `model_pricing` seed data signed off.
- [ ] §5.1 sandbox walkthrough completed end-to-end; §5.2 tests green.
- [ ] Alerts live for webhook non-2xx and dispatcher charge-recording failures.
