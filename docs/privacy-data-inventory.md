# Personal data inventory

The factual basis for Resland's Privacy Policy and Terms of Service: what
personal data the product collects, where it is stored, who it is sent to, and
how long it is kept. Hand this to whoever drafts the policies (lawyer or
generator), and update it whenever a data flow changes. A policy that
contradicts this file is a policy that says something untrue.

Snapshot of `master` at `a81c42a` plus the owner's answers about production
hosting and policy decisions, 2026-10-06. Section 8 lists what is still open.

## At a glance

- **Operator:** Quellen Ventures LLC, a Colorado LLC.
  - Contact: `marquelle.nesbitt@gmail.com`.
  - Mailing address (registered agent): United States Corporation Agents, Inc.,
    8400 E Crescent Pkwy, Suite 600, Greenwood Village, CO 80111, US.
- **Hosting:**
  - Railway, region US West: the API, dispatcher, frontend, Postgres and
    RabbitMQ.
  - AWS S3, `us-east-2`: resume files.
  - Vercel is not used.
  - The AWS ECS/RDS/Amazon MQ stack in `terraform/` has been torn down
    (see §5).
- **Collected:**
  - a sign-in identity (Auth0)
  - the uploaded resume and everything parsed from it, including name, email,
    phone, location and links
  - pasted job descriptions
  - mock-interview work
  - billing records
  - anonymous page views
- **Sent to third parties:**
  - Resume and job content goes to OpenRouter, with zero data retention
    enforced, and on to OpenAI or Anthropic models.
  - Agent traces go to LangSmith.
  - Payments go through Stripe-hosted Checkout.
- **Not done:**
  - no selling of data
  - no advertising or third-party analytics trackers
  - no card data on Resland servers
  - no email marketing (no email provider exists)
- **Decided:**
  - Users must be 18+.
  - The policies cover GDPR/UK GDPR.
  - Balance never expires, and refunds are discretionary.
  - On account deletion, the balance is forfeited, and billing records are
    kept de-identified.
- **In progress:** self-serve account deletion and data export
  (`feat/account-deletion-export`). Until that merges, there is no deletion,
  no export, and no retention limit.

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

Railway keeps application and HTTP logs for **7 days on Hobby, 30 on Pro**.
The window isn't configurable within a plan, and Railway doesn't delete logs
on request
([Railway logging docs](https://docs.railway.com/reference/logging)). Write
the policy as "up to 30 days" and assume logs may contain IP addresses.

- Uvicorn access logs: method, path, status, client address.
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
| **Railway** (US West) | Hosts the API, dispatcher, frontend, Postgres, and RabbitMQ | All app data at rest. Every page request and API call. The Auth0 session cookie passes through the frontend |
| **AWS S3** (`us-east-2`) | File storage | Original resumes and generated `.docx` files |
| **Auth0** (Okta) | Sign-in | The account itself: email, name, picture from the social or password login; login sessions |
| **Stripe** | Payments | Everything entered at Checkout (email, card, billing details) plus our `auth0_id` in metadata |
| **OpenRouter** | AI gateway for every model call | **Resume parsing:** the full resume text, including contact details. **Tailoring:** the full profile as JSON, including name, email, phone, location, links, plus the job description and the user's answers. **Suggestions:** the experience entry and bullets, plus the user's guidance and answers (no contact details). **System design:** notes, diagram text, transcript, and for job-based sessions the job description. No user identifier is sent. **Zero data retention is enforced on all providers in the account settings** (owner, 2026-10-06) |
| **OpenAI, Anthropic** (via OpenRouter) | Running the models | The same content as above. The `/admin` model list offers OpenAI GPT and Anthropic Claude models. Resume parsing uses `RESUME_PARSER_MODEL`. If that is still `openrouter:openrouter/auto`, OpenRouter can pick another vendor's zero-retention endpoint. Pin it to an OpenAI or Claude model so the policy's list is complete |
| **LangSmith** (LangChain) | Agent tracing | When `LANGSMITH_TRACING=true` is set on the dispatcher, every prompt, tool output (resume text, contact details, job descriptions), model output, and user answer goes to the LangSmith project. Listed as a subprocessor by decision; set the project's trace retention to the shortest tier |
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

## 4. Retention and deletion

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
| `token_usage`, `balance_purchase` | Forever (accounting). Decided: on account deletion they stay, repointed to an anonymous placeholder user | No |
| `page_view` | Forever | n/a (anonymous) |
| Railway logs | 7 days (Hobby) / 30 days (Pro) | No |
| Postgres backups | **None today.** Planned: weekly, kept one month | No |
| Auth0 account | Until deleted in Auth0 | No |
| Stripe customer and payments | Indefinitely, per Stripe's own obligations | No |
| LangSmith traces | Per the project's trace retention setting | No |

`feat/account-deletion-export` adds a self-serve export, and a deletion that
covers:

- every DB row (billing de-identified),
- the S3 prefix `resumes/<auth0_id>/`,
- the LangGraph threads,
- the Stripe customer,
- the Auth0 user.

It also fixes the re-upload checkpoint orphaning. Deletion can't reach
dead-letter messages, platform logs, backups, or LangSmith traces. The policy
should say those age out on their own schedules.

## 5. Security: what the policy can claim

**Accurate**
- HTTPS for all traffic to the site and API.
- **Encryption at rest:** Railway encrypts all volumes and backups with
  AES-256. The S3 bucket has default SSE-S3 (AES-256) encryption (verified
  2026-10-06).
- **S3 access:** all four public-access-block settings are on, and there is no
  bucket policy (verified 2026-10-06). Versioning is off, so deleted files
  don't linger as old versions.
- **Network isolation:** Postgres and RabbitMQ are reachable only over
  Railway's private network, which runs over encrypted WireGuard tunnels.
- Railway holds SOC 2 Type II and offers a GDPR Article 28 DPA
  ([Railway Station](https://station.railway.com/questions/data-protection-questions-encryption-a-e5128546)).
- Card details never touch Resland (Stripe-hosted Checkout).
- Every content query is scoped to the signed-in user. Admins see users' email,
  name, balance, and usage through `/admin`, but not resume content, job
  descriptions, or transcripts (though the owner has direct database access).

**Caveats**
- The AWS stack in `terraform/` (ECS, RDS, Amazon MQ, a load balancer, the
  `api` ECR repository) **no longer exists**. Checked in `us-east-2` on
  2026-10-06: no RDS instances or snapshots, no MQ brokers, no `resland-live`
  ECS cluster, no load balancers, no ECR repository. Only the S3 bucket is
  live. `terraform/` (apart from `durable/`), `deploy.sh`, and the deploy notes
  in `AGENTS.md` are stale.
- The S3 settings above come from AWS defaults, not from Terraform, so
  nothing in the repo stops them from changing.
- `.dockerignore` excludes only the root `.env`, so a local `docker build`
  bakes `backend/dispatcher/.env` (API keys included) into the image. Railway
  builds from git, where `.env` is ignored, so production isn't affected.

## 6. What the site already promises

These must stay true, or the policy and the copy must change together:

- "Checkout runs through Stripe, so Resland never sees your card details."
  (`frontend/app/help/page.tsx`) Accurate.
- "Your profile is private to your account. When you run a suggestion or tailor
  a resume, the text involved is sent to the AI model you picked so it can do
  the work." (`frontend/app/help/page.tsx`) **Incomplete:**
  - Resume parsing sends the whole resume to a model the user doesn't pick.
  - Mock interviews send content too.
  - LangSmith receives traces.
- Charges are "the AI provider's cost for that work, plus a service fee"
  (billing page, Help). The fee is a 1.25× markup (`COST_MARKUP`); the UI never
  shows the number.
- "One-time payments through Stripe. Nothing renews." (landing page) Accurate.

## 7. Facts the Terms of Service need

- **Contracting party:** Quellen Ventures LLC, a Colorado LLC. Governing law
  is Colorado.
- **Accounts:** Auth0 sign-up. **Users must be 18 or older.** There is no age
  gate and no Terms acceptance step at sign-up or checkout yet.
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
- **Balance and refunds (decided):**
  - The balance never expires.
  - Purchases aren't refundable except at the operator's discretion or where
    the law requires.
  - Any remaining balance is forfeited on account deletion; the deletion
    screen warns about this.
  - A full Stripe refund removes the granted balance (floored at zero). A
    partial refund leaves the balance untouched, which is fine for
    discretionary refunds.
  - EU/UK consumers have a 14-day right to withdraw from digital services. It
    lapses only if they expressly ask for the service to start right away and
    acknowledge losing the right, which can be done in the checkout consent
    text. That's a lawyer question.
- **AI output:** generated resumes and suggestions can be wrong or embellished,
  and the user is responsible for what they send to employers. Interview grades
  are automated practice feedback, not hiring decisions.
- **User content:** Resland needs a license to store and process uploads and to
  send them to the processors in §2. Who owns the output also needs stating.
- **Operator controls:** a site-wide maintenance mode and a payments pause
  (`site_settings`).

## 8. Before publishing

**Done or decided**
- Zero data retention enabled for all OpenRouter providers.
- LangSmith will be listed.
- Postgres and RabbitMQ are private on Railway.
- Users must be 18+.
- GDPR is in scope.
- Balance never expires and refunds are discretionary.
- Billing records are kept de-identified on deletion.
- Contact email, mailing address, and governing law are set.

**Still to do**
1. Merge account deletion and data export (`feat/account-deletion-export`).
   It needs an Auth0 Management API app; see that PR.
2. Pin `RESUME_PARSER_MODEL`, plus the `SUGGESTIONS_MODEL` and `TAILOR_MODEL`
   fallbacks, to OpenAI or Claude models in Railway, so `openrouter/auto` can't
   route outside the vendors the policy names.
3. Set LangSmith trace retention to the shortest tier, and turn on the planned
   weekly Postgres backups.
4. Sign Railway's DPA. Confirm the DPAs for Stripe, Auth0, OpenRouter,
   LangSmith, and AWS; most are incorporated into their terms automatically.
5. Remove the stale AWS deploy path: `terraform/` outside `durable/`,
   `deploy.sh`, and the ECS/ECR notes in `AGENTS.md`. The resources
   themselves are already gone.
6. Retention: add a TTL to the dead-letter queues and a `page_view` retention
   window.
7. Self-host the Excalidraw fonts (`EXCALIDRAW_ASSET_PATH`), or list esm.sh.
8. Update the Help page's privacy answer (§6).
9. Publish `/privacy`, `/terms`, and a refund policy. Add them to the footer
   `LEGAL_LINKS` and `app/sitemap.ts`, and set Checkout's
   `consent_collection.terms_of_service = "required"`.
