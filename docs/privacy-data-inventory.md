# Personal data inventory

The factual basis for Resland's Privacy Policy and Terms of Service: what
personal data the product collects, where it is stored, who it is sent to, and
how long it is kept. Hand this to whoever drafts the policies (lawyer or
generator), and update it whenever a data flow changes. A policy that
contradicts this file is a policy that says something untrue.

Snapshot of `master` at `a81c42a` plus the deployed image, 2026-10-06. Section
8 lists what has to be decided or fixed before the policies can be published.

## At a glance

- **Operator:** Quellen Ventures LLC (footer, landing-page JSON-LD). There is
  no support or privacy contact email anywhere yet.
- **Collected:** a sign-in identity (Auth0), the uploaded resume and everything
  parsed from it (including name, email, phone, location, links), pasted job
  descriptions, mock-interview work, billing records, and anonymous page views.
- **Sent to third parties:** resume and job content goes to OpenRouter and on
  to the model provider. In production it currently also goes to LangSmith
  (see §2). Payments go through Stripe-hosted Checkout.
- **Not done:** no selling of data, no advertising or third-party analytics
  trackers, no card data on Resland servers, no email marketing (no email
  provider exists).
- **Missing:** account deletion, data export, and any retention limits.

## 1. What we collect

### 1.1 Sign-in identity

| Data | Source | Stored | Code |
|---|---|---|---|
| Auth0 user id (`sub`, e.g. `google-oauth2\|…`) | Auth0 login | `user.auth0_id`; also embedded in S3 keys, AMQP messages, Stripe metadata | `frontend/lib/db.ts`, `backend/api/src/api/auth.py` |
| Name, email, picture, nickname (Auth0 profile claims) | Auth0 login, scopes `openid profile email offline_access` | Only in the encrypted Auth0 session cookie and at Auth0. Not written to our DB. Email is checked for presence; name/email are shown as a dashboard fallback | `frontend/lib/auth0.js`, `frontend/app/(protected)/dashboard/page.tsx` |
| Access/refresh/ID tokens | Auth0 | Encrypted `__session` cookie | `@auth0/nextjs-auth0` defaults |

The `user` row is created with only `auth0_id` on first sign-in.

### 1.2 Resume and profile

| Data | Source | Stored | Kept until |
|---|---|---|---|
| Original resume file (`.docx`/`.pdf`, ≤100 MB) | Upload | S3 `resland-user-resumes/resumes/<auth0_id>/resume_doc.<ext>` | Overwritten by the next upload of the same type. Never deleted. A `.docx` and a `.pdf` can both exist |
| Contact header: full name, email, phone, location, summary | Parsed from the resume, or typed in onboarding / Edit Profile | `user` | Replaced on re-upload or edit |
| Links (LinkedIn, GitHub, website) | Same | `user_social_link` | Same |
| Experience (company, title, dates), bullets, skills, education, projects | Same | `user_base_*` tables | Same. Re-upload rebuilds them |
| Layout profile (fonts, styles, section titles; no contact values) | Parsed from the resume | `user_resume_format` | Replaced on re-upload |
| Generated `.docx` exports | Built from the profile | S3 `…/generated.docx`, `…/tailored/<id>.docx`; served via 5-minute presigned URLs | `generated.docx` is never deleted. Tailored exports are deleted with their tailored resume (best effort) |

The email/name in `user` are the resume-header values, not the Auth0 login
email.

### 1.3 Tailoring and suggestions

| Data | Stored | Notes |
|---|---|---|
| Job description (≤10k chars), company, role | `user_tailor_run`, copied into `user_tailored_resume` and into job-based `user_system_design_session` rows | The copy in a system-design session survives deleting the tailored resume |
| Free-text guidance for bullet suggestions, answers to the agent's questions, revision feedback | Not in app tables. Travels in AMQP messages and is persisted in LangGraph checkpoints (§4) | |
| AI output: tailored resume JSON, suggestion options | `user_tailor_run.result`, `user_tailored_resume.content`, `user_suggestion.result` | Accepting a suggestion overwrites the base bullet |

### 1.4 System-design mock interviews

Requirements and estimates notes, an Excalidraw diagram, the chat transcript
(both sides), and a **graded report with a letter grade and a "hire signal"**
(`user_system_design_session`, `system_design_message`). The grade is an
automated assessment of the user; the Terms should say it is practice feedback,
not a hiring decision. Sessions are kept until the user dismisses them.

### 1.5 DSA study center

Topics a signed-in user marks as studied (`user_dsa_progress`). The chosen code
language lives in the browser only (localStorage).

### 1.6 Billing

- Payment happens on **Stripe-hosted Checkout**; card data never reaches
  Resland. Stripe collects the payer's email, card, and whatever billing
  details it requires.
- We create the Stripe customer with **no email or name**, only
  `metadata.auth0_id`, and send `client_reference_id = auth0_id`
  (`backend/api/src/api/billing/service.py`).
- Stored locally: `user.stripe_customer_id`, `user.balance_cents`,
  `balance_purchase` (Checkout session id, amount charged, balance granted,
  currency, status, PaymentIntent id), and `token_usage` (one row per AI job:
  model, tokens, amount charged, provider cost, OpenRouter generation ids).
- Webhooks do not read or store Stripe's `customer_details` (email/name/address).

### 1.7 Site analytics (first-party)

`page_view`, written by `frontend/app/api/metrics/pageview/route.ts`:

- **Stored:** a random per-tab visit id, the path with ids masked
  (`/tailored/[id]`), the previous path, a source category (search, AI, social,
  referral, direct), the referrer **host** or `utm_source`, and `utm_campaign`.
- **Not stored:** IP address, user agent, user id, full referrer URL, query
  strings. The user agent is read only to drop bots. Site admins are excluded.
- **No cookies:** the visit id lives in `sessionStorage` and dies with the tab.
- Kept forever (no purge).

### 1.8 Server logs

CloudWatch `/ecs/api` and `/ecs/dispatcher`, **30-day** retention
(`terraform/modules/ecs`).

- Uvicorn access logs: method, path, status, client address. Behind the load
  balancer the address is most likely the load balancer's, since
  `FORWARDED_ALLOW_IPS` is not set.
- The API prints the caller's Auth0 id on every request while maintenance mode
  is on (`backend/api/src/api/auth.py`).
- The dispatcher prints S3 keys (which contain the Auth0 id) and, when a job
  fails, the **whole job payload**, which can include the user's free-text
  prompt, answer, or chat message (`backend/dispatcher/src/dispatcher/runners/local_threaded.py`).
- Resume text, prompts, and model responses are not printed. Exception messages
  can occasionally carry input values.

## 2. Who receives it (subprocessors)

| Service | Purpose | What it receives |
|---|---|---|
| **Auth0** (Okta) | Sign-in | The account itself: email, name, picture from the social or password login; login sessions |
| **Stripe** | Payments | Everything entered at Checkout (email, card, billing details) plus our `auth0_id` in metadata |
| **OpenRouter** | AI gateway for every model call | **Resume parsing:** the full resume text, including contact details. **Tailoring:** the full profile as JSON, including name, email, phone, location, links, plus the job description and the user's answers. **Suggestions:** the experience entry and bullets, plus the user's guidance and answers (no contact details). **System design:** notes, diagram text, transcript, and for job-based sessions the job description. No user identifier is sent |
| **The model provider OpenRouter routes to** | Running the model | The same content as above. Users pick from an admin-curated list for suggestions, tailoring, and interviews. Resume parsing always uses `RESUME_PARSER_MODEL`, which is `openrouter/auto` (OpenRouter picks the model and provider). No provider privacy routing (`data_collection`, ZDR) is set in code, so the OpenRouter account settings decide whether prompts can reach providers that log or train on them |
| **LangSmith** (LangChain) | Agent tracing | The deployed dispatcher image (pushed to ECR 2026-09-27) contains `backend/dispatcher/.env` with `LANGSMITH_TRACING=true`, and Terraform injects `LANGSMITH_API_KEY`. If that image is what's running, **every prompt, tool output (resume text, contact details, job descriptions), model output, and user answer is sent to the LangSmith project "Resland"** |
| **AWS** (us-east-2) | Hosting | S3 (resume files), RDS Postgres (all app data), Amazon MQ (job messages), ECS Fargate (API and workers), CloudWatch (logs), Route 53, ACM |
| **Frontend host** (Vercel and/or Railway; not in Terraform, needs confirming) | Runs the Next.js server | Every page request, the Auth0 session cookie, and a direct Postgres connection |
| **esm.sh** | Excalidraw fonts on `/system-design/[id]` | The visitor's IP and user agent (browser request). `EXCALIDRAW_ASSET_PATH` is unset, so the package falls back to the CDN |

Not used: analytics or ad trackers, error monitoring, email providers, a CDN.
Google Fonts are self-hosted by `next/font`, so browsers never contact Google.

## 3. Cookies and browser storage

| Name | Type | Set by | Purpose | Lifetime |
|---|---|---|---|---|
| `__session` (+ `__session__N` chunks) | Cookie, httpOnly, SameSite=Lax | Auth0 SDK | Encrypted login session | Rolling: 1 day idle, 3 days max |
| `__txn_<state>` | Cookie, httpOnly | Auth0 SDK | Login in progress | 1 hour |
| `resland.visit`, `resland.visit.path` | sessionStorage | Page-view tracker | Group a visit's page views | Until the tab closes |
| `resland.dsa.language` | localStorage | DSA study center | Remember code language | Until cleared |
| `mermaid-to-excalidraw`, `publish-library-data` | localStorage | Excalidraw | Only if those dialogs are opened | Until cleared |

Auth0's hosted login page and Stripe Checkout set their own cookies on their own
domains. There is no cookie banner, consent manager, or Global Privacy Control
handling. Everything above is either needed for sign-in or anonymous
first-party analytics. Whether that needs a consent prompt for EU/UK visitors is
a question for the lawyer.

## 4. Retention and deletion today

| Data | Kept for | User can delete? |
|---|---|---|
| Original resume in S3 | Until overwritten by a new upload | No |
| Profile (`user`, `user_base_*`, links, format) | Until re-upload or edit | Edit only |
| `generated.docx` | Until regenerated | No |
| Tailored resumes | Until deleted | Yes (S3 file deleted best effort) |
| Tailor runs | Until dismissed; completed runs are cleared when a new run starts | Yes |
| Suggestions | Until accepted or dismissed; re-upload deletes them | Yes |
| System-design sessions and transcripts | Until dismissed | Yes |
| LangGraph checkpoints (`langgraph` schema): full conversations, including the tailor profile with contact details, and the user's answers | Deleted with their run/session. **Orphaned forever** when a re-upload deletes suggestion rows, and for any abandoned session. No TTL, no application-level encryption | Indirectly |
| AMQP dead-letter queues: failed job messages, which can contain user free text | **Forever.** No TTL and nothing consumes them | No |
| `token_usage`, `balance_purchase` | Forever (accounting) | No |
| `page_view` | Forever | n/a (anonymous) |
| CloudWatch logs | 30 days | No |
| RDS automated backups | 3 days | No |
| Auth0 account | Until deleted in Auth0 | No |
| Stripe customer and payments | Indefinitely, per Stripe's own obligations | No |
| LangSmith traces | Per the LangSmith plan's retention | No |

There is **no account deletion, no data export, and no "delete my resume"**.
The schema declares no `onDelete` cascades, so an account-deletion path has to
delete dependent rows in order, then the S3 prefix `resumes/<auth0_id>/`, the
LangGraph threads, the Auth0 user, and the Stripe customer (or keep billing
records with a stated reason).

## 5. Security: what the policy can and can't claim

**Accurate today**
- HTTPS everywhere: the API load balancer redirects HTTP to HTTPS (ACM cert).
- Card details never touch Resland (Stripe-hosted Checkout).
- Every content query is scoped to the signed-in user. Admins see users' email,
  name, balance, and usage through `/admin`, but not resume content, job
  descriptions, or transcripts (though they have direct database access).

**Not accurate today; don't claim it until fixed**
- **Database encryption at rest:** `storage_encrypted` is unset on the RDS
  instance (`terraform/rds.tf`), so it is off. RDS can't encrypt an existing
  instance in place: snapshot, copy the snapshot with encryption, restore.
- **Network isolation:** RDS is `publicly_accessible` with `0.0.0.0/0` on 5432
  (password auth only), probably because the frontend host connects to
  Postgres directly. The Amazon MQ broker is also `publicly_accessible`.
- **S3 hardening:** the bucket declares no encryption, public-access block,
  versioning, or lifecycle rules (`terraform/durable/s3.tf`). AWS defaults
  (SSE-S3; public access blocked on buckets created after April 2023) probably
  apply, but the repo doesn't enforce them.
- **Secrets:** they are plaintext env vars in the ECS task definitions and
  Terraform state. `.dockerignore` excludes only the root `.env`, so
  `backend/dispatcher/.env` (API keys included) is baked into the image pushed
  to ECR.

## 6. What the site already promises

These must stay true, or the policy and the copy must change together:

- "Checkout runs through Stripe, so Resland never sees your card details."
  (`frontend/app/help/page.tsx`) Accurate.
- "Your profile is private to your account. When you run a suggestion or tailor
  a resume, the text involved is sent to the AI model you picked so it can do
  the work." (`frontend/app/help/page.tsx`) **Incomplete:**
  - Resume parsing sends the whole resume to a model the user doesn't pick.
  - Mock interviews send content too.
  - LangSmith receives everything while tracing is on.
- Charges are "the AI provider's cost for that work, plus a service fee"
  (billing page, Help). The fee is a 1.25× markup (`COST_MARKUP`); the UI never
  shows the number.
- "One-time payments through Stripe. Nothing renews." (landing page) Accurate.

## 7. Facts the Terms of Service need

- **Contracting party:** Quellen Ventures LLC. The state of formation (for
  governing law) is not in the repo.
- **Accounts:** Auth0 sign-up. No age gate and no Terms acceptance step at
  sign-up or checkout.
- **Billing:** a prepaid USD balance bought in one-time Stripe Checkout packs.

  | Pack | Pay | Balance added |
  |---|---|---|
  | Starter | $5 | $5.00 |
  | Standard | $10 | $11.00 |
  | Pro | $20 | $25.00 |

  - Each AI job (suggestion, tailoring, interview turn) is charged at the
    provider's cost × 1.25. If the cost lookup fails, the admin rate card is
    used instead.
  - Resume parsing is free.
  - The balance never goes negative, and new jobs are refused at zero.
  - The balance has no expiry logic.
- **Refunds:** a full Stripe refund removes the granted balance (floored at
  zero). A partial refund leaves the balance untouched; that behaviour is an
  open decision in `docs/stripe-billing-plan.md`. There is no written refund
  policy yet, and Stripe expects one on the site.
- **AI output:** generated resumes and suggestions can be wrong or embellished,
  and the user is responsible for what they send to employers. Interview grades
  are automated practice feedback, not hiring decisions.
- **User content:** Resland needs a license to store and process uploads and to
  send them to the processors in §2. Who owns the output also needs stating.
- **Operator controls:** a site-wide maintenance mode and a payments pause
  (`site_settings`).

## 8. Before publishing

**Decide**
1. Will you serve EU/UK users? That adds GDPR lawful-basis, transfer, and
   rights language, and may affect §3.
2. Minimum age: 13, 16, or 18.
3. Unused balance: does it expire, and is it refundable, including on account
   closure? Some US states regulate expiring prepaid value.
4. How partial refunds should behave.
5. Which frontend host is live: Vercel, Railway, or both.
6. A contact address for privacy and support requests.

**Fix in code/infra, or disclose as-is**
1. **LangSmith:** either turn tracing off in production, or list LangSmith as a
   subprocessor and set a short trace retention. To turn it off, first move
   `RESUME_PARSER_MODEL` (and the other `*_MODEL` vars) into Terraform, then
   stop shipping `backend/**/.env` in the image. Today resume parsing depends on
   that baked-in file.
2. **OpenRouter:** turn on the account setting that excludes providers that
   train on or retain prompts, or send `provider.data_collection: "deny"` / ZDR
   per request. Consider pinning the parser model instead of `openrouter/auto`
   so the policy can name providers.
3. **Account deletion and data export** (§4), plus a "delete my resume" option.
4. **Retention:** purge orphaned checkpoints, add a TTL to the dead-letter
   queues, add a `page_view` retention window, and add S3 lifecycle rules if
   wanted.
5. **Database:** encrypt RDS at rest, and restrict RDS and MQ network access.
6. Self-host the Excalidraw fonts (`EXCALIDRAW_ASSET_PATH`), or list esm.sh.
7. Update the Help page's privacy answer (§6).
8. Publish `/privacy`, `/terms`, and a refund policy. Add them to the footer
   `LEGAL_LINKS` and `app/sitemap.ts`, and set Checkout's
   `consent_collection.terms_of_service = "required"`.
