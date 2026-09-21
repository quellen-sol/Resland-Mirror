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
2. `POST /billing/checkout` (`billing/service.py::create_checkout`) looks up or
   creates the Stripe customer (`user.stripe_customer_id`), creates a Checkout
   Session (`mode="payment"`, `client_reference_id=<auth0_id>`,
   `metadata={pack_id, cents}`), inserts a `PENDING` `balance_purchase` row
   keyed by the Stripe session id, and returns the hosted-checkout URL.
3. Stripe calls `POST /stripe/webhook` — unauthenticated, verified by
   `STRIPE_WEBHOOK_SECRET` signature instead (`billing/service.py::handle_webhook`):
   - `checkout.session.completed`: upserts the purchase row (the webhook can
     beat the checkout endpoint's own INSERT), flips `PENDING → COMPLETED`,
     and credits `balance_cents` — all in one transaction. Only a `PENDING`
     row transitions, so a redelivered event can't double-credit.
   - `checkout.session.expired`: marks the row `EXPIRED`.
   - Events without our `client_reference_id`/`cents` metadata are
     acknowledged and ignored.
4. Frontend `/billing` (`frontend/app/(protected)/billing/`) renders packs,
   balance, and purchase history; `components/balance-chip.tsx` links there
   from the nav.

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
   the balance never goes negative.
4. Charge amount: actual OpenRouter cost (`fetch_generation_cost_cents`, with
   one retry per generation) × `COST_MARKUP` (1.25). If any generation lookup
   fails, the whole job falls back to the `model_pricing` rate card —
   partially-resolved jobs never underbill; if the model isn't in the card,
   `FALLBACK_CENTS_*` applies so unpriced models never run free. Amounts are
   `ceil`ed to 1/10,000¢ so sub-cent usage never rounds down to zero.
5. `/admin/*` (`admin/service.py`) exposes read-only per-user
   purchased/used balances, usage by model/kind/day, the recent ledger, and
   revenue; `PUT/DELETE /admin/models/{id}` manages the rate card.

## 2. Safeguards already in place (do not regress)

- Hosted Stripe Checkout — card data never touches Resland.
- Server-side pack catalog; the webhook credits `metadata.cents` we set at
  session creation, never a client-supplied amount.
- Webhook signature verification; both checkout and the webhook 503 when
  Stripe env vars are missing rather than failing open.
- Idempotent top-up: `balance_purchase.id` is the Stripe session id, and only
  the `PENDING → COMPLETED` transition credits.
- Webhook-before-INSERT race handled by the upsert in `handle_webhook`.
- Fractional-cent `Decimal` balance; charges round up, never down to free.
- Model whitelist + admin validation (`openrouter:` prefix, non-negative
  rates, default must be enabled).
- Balance gate at job start; mid-run jobs are never interrupted.

## 3. Known gaps — decisions needed before launch

1. **AMQP redelivery can double-charge.** Messages are `accept`ed only when a
   job completes (`handlers/generic.py`). If the dispatcher crashes mid-job,
   the unacked message is redelivered, the job re-runs, and
   `record_token_usage` writes a **second** ledger row and debit —
   `token_usage` has no uniqueness on `(job_kind, job_id)`.
   *Recommend:* unique constraint on `(job_kind, job_id)` + `ON CONFLICT DO
   NOTHING`, so a re-run's charge is recorded once. Failed-job redelivery goes
   to the DLX, not auto-retry, so this mainly covers crashes/restarts.
2. **No refund/chargeback path.** `charge.refunded` and `charge.dispute.*`
   aren't handled — a refunded purchase keeps its credited balance.
   *Recommend:* subscribe to `charge.refunded`, mark the purchase `REFUNDED`,
   and deduct remaining credit (or document a manual-adjustment runbook).
3. **No cost estimate or spend cap per job.** `require_balance` only checks
   `> 0`; a single job can burn the entire balance (floor at 0 means Resland
   absorbs the overrun). *Decide:* show an estimated cost range before
   starting, and/or cap per-job spend.
4. **`?checkout=success` toast assumes the webhook already landed.** The
   success banner says "balance topped up" and the balance is fetched once on
   mount — the credit may lag a few seconds. *Recommend:* poll `/billing/balance`
   for ~10s after a success redirect.
5. **Stripe customer creation race.** Two concurrent checkouts can create two
   Stripe customers (last write wins; an orphan remains in Stripe). *Recommend:*
   pass an `idempotency_key` to `Customer.create`, or accept as cosmetic.
6. **Pack catalog is hardcoded.** Price changes require a deploy. Fine for
   launch; revisit if pricing iterates often (alternatives: packs in DB, or
   Stripe Prices + lookup keys).
7. **No automated billing tests yet** — backend has no pytest harness, the
   frontend has a single `node --test` file. Section 5 lists the cases to add.
8. **Webhook observability.** Stripe disables endpoints after sustained
   failures. *Recommend:* alert on non-2xx responses at the LB and on
   `Failed to record token usage` in dispatcher logs; run the reconciliation
   queries in §5.4 periodically.
9. **PENDING rows for abandoned checkouts** are only cleared by
   `checkout.session.expired`; if that event isn't subscribed they sit
   `PENDING` forever (harmless to balances, noise in history).

## 4. Setup checklist

### Local (compose)

| Var | Where | Notes |
| --- | --- | --- |
| `STRIPE_SECRET_KEY` | `backend/api/.env` | `sk_test_...` for dev |
| `STRIPE_WEBHOOK_SECRET` | `backend/api/.env` | `whsec_...` printed by `stripe listen` |
| `FRONTEND_BASE_URL` | `backend/api/.env` | success/cancel redirect target |
| `NEXT_PUBLIC_API_BASE_URL` | frontend env | e.g. `http://localhost:3001` |

```bash
stripe login
stripe listen --forward-to localhost:3001/stripe/webhook   # copy whsec_... into .env
docker compose up --build
```

### Production (terraform `api.tf`)

- `stripe_secret_key`, `stripe_webhook_secret` — sensitive TF vars; use
  live-mode `sk_live_...` / endpoint `whsec_...`.
- Register the webhook endpoint in Stripe → Developers → Webhooks:
  `https://<api-host>/stripe/webhook`, events `checkout.session.completed`,
  `checkout.session.expired` (plus `charge.refunded` once handled).
- `FRONTEND_BASE_URL` is `https://resland.org` in terraform — verify.
- `MAINTENANCE_MODE` is currently `"1"` in `api.tf` — confirm that's
  intentional before launch.
- Restricted keys are preferable to secret keys if the API only needs
  Customer + Checkout write.

## 5. Test plan

### 5.1 Automated tests to add

Backend: introduce `pytest` + `pytest-asyncio` in `backend/api` and
`backend/dispatcher`; run against the compose Postgres (or a fixture schema).
Mock Stripe by patching `stripe.Webhook.construct_event` /
`stripe.checkout.Session.create` — never hit real Stripe in CI.

`billing/service.py`:

- checkout: unknown `pack_id` → 400; `STRIPE_SECRET_KEY` unset → 503; happy
  path → URL returned, `PENDING` row keyed by session id; existing
  `stripe_customer_id` reused (no second `Customer.create`); missing user → 404.
- webhook: bad signature → 400 and no credit; `completed` →
  `PENDING → COMPLETED` + `balance_cents += cents`; **same event redelivered →
  no second credit**; `completed` arriving before the checkout INSERT →
  upserted row still ends `COMPLETED` with correct credit; `expired` →
  `EXPIRED`, no credit; event with no metadata → `{ok: true}` no-op.

`balance.py`:

- `require_balance`: 0 or missing user → 402; >0 → returns balance.
- `validate_model_choice`: unknown/disabled → 400; enabled → pass; `None` →
  `None`.

`runners/db_ops.py::record_token_usage`:

- rate-card math when generation lookup fails (incl. partial failure →
  all-or-nothing fallback); actual cost × 1.25 when stats resolve;
  `ceil` to 1/10,000¢; zero tokens → no row, no debit; overrun → balance
  floors at 0, ledger still records full charge.
- **After fixing gap 1:** calling it twice for the same `(job_kind, job_id)`
  writes one row and debits once.

### 5.2 Manual end-to-end (Stripe test mode)

1. `stripe listen` + compose stack up; sign in via Auth0; open `/billing`.
2. Buy **Starter** with `4242 4242 4242 4242` → lands on
   `?checkout=success`; assert balance +$5.00, purchase `COMPLETED`, payment
   visible in Stripe dashboard.
3. `4000 0000 0000 9995` (insufficient funds) → checkout fails, no credit;
   row stays `PENDING` until the `expired` event.
4. Abandon checkout → on `checkout.session.expired` the row goes `EXPIRED`,
   no credit (force with `stripe trigger checkout.session.expired` or wait
   ~24h).
5. `stripe events resend evt_...` on the completed event → **balance must not
   double-credit**.
6. Run a suggestion and a tailor job → balance decreases; `token_usage.amount_cents`
   ≈ OpenRouter cost × 1.25.
7. Drain balance to 0 → next job → 402 → "Top up" toast → `/billing`.
8. Buy two packs back-to-back (double-click Buy) → two sessions, each
   completion credits its own pack — both legitimate purchases.

### 5.3 Failure-injection checks

- Restart the dispatcher mid-job → confirm (after gap 1 fix) no second debit.
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
```

Also reconcile `balance_purchase` `COMPLETED` totals against the Stripe
dashboard (payments minus refunds) each release cycle.

## 6. Pre-launch checklist

- [ ] Gap 1 (double-charge on redelivery) fixed or consciously accepted.
- [ ] Refund runbook written (manual SQL adjustment until `charge.refunded`
      is handled), decision recorded in this doc.
- [ ] Live webhook endpoint registered with exactly the supported events.
- [ ] Live keys set via terraform vars; test keys nowhere near prod env.
- [ ] `MAINTENANCE_MODE` flag reviewed.
- [ ] `TOKEN_PACKS` pricing and `model_pricing` seed data signed off.
- [ ] §5.1 tests merged and green; §5.2 manual run completed in staging.
- [ ] Alerts live for webhook non-2xx and dispatcher charge-recording failures.
