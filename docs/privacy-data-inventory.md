# Personal data inventory

The factual basis for Resland's Privacy Policy and Terms of Service: what
personal data the product collects, where it is stored, who it is sent to, and
how long it is kept. Hand this to whoever drafts the policies (lawyer or
generator), and update it whenever a data flow changes. A policy that
contradicts this file is a policy that says something untrue.

Snapshot of `master` at `20a502d` (account deletion and export, the memory
bank, and resland-mcp merged), 2026-10-10, plus the owner's answers about
production hosting and policy decisions from 2026-10-06. Section 8 lists what
is still open.

## At a glance

- **Operator:** Quellen Ventures LLC, a Colorado LLC.
  - Contact: `marquelle.nesbitt@gmail.com`.
  - Mailing address (registered agent): United States Corporation Agents, Inc.,
    8400 E Crescent Pkwy, Suite 600, Greenwood Village, CO 80111, US.
- **Hosting:**
  - Railway, region US West: the API, dispatcher, frontend, Postgres and
    RabbitMQ.
  - AWS S3, `us-east-2`: resume files.
  - Vercel doesn't serve production, but its GitHub app is still connected
    and builds previews of `frontend/` for PRs (§2).
  - The AWS ECS/RDS/Amazon MQ stack in `terraform/` has been torn down
    (see §5).
- **Collected:**
  - a sign-in identity (Auth0)
  - the uploaded resume and everything parsed from it, including name, email,
    phone, location and links
  - pasted job descriptions
  - memory facts: details about the user's work, saved from their interview
    answers
  - mock-interview work
  - billing records
  - anonymous page views
- **Sent to third parties:**
  - Resume, memory and job content goes to OpenRouter, with zero data
    retention enforced, and on to OpenAI or Anthropic models.
  - Agent traces go to LangSmith.
  - Payments go through Stripe-hosted Checkout.
  - A user who connects resland-mcp to their own Claude app sends their
    profile and memory to Anthropic under their own Claude account (§1.9).
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
- **Self-serve deletion and export:** merged (#81) as the Account & Data page
  (`/account`). In production it also needs the S3 `ListBucket` grant, which
  isn't applied yet, and the Auth0 Management API credentials (§8).

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
| Free-text guidance for bullet suggestions, answers to the agent's questions, revision feedback | The raw text isn't in app tables. It travels in AMQP messages and is persisted in LangGraph checkpoints (§4) | The facts the agent takes from it go to the memory bank (next row) |
| Memory bank: up to 200 facts, each a topic (a job, a project, "Preferences" or "General") and up to 500 characters of text | `user_memory_fact`, with the source `TAILOR`, `SUGGESTION` or `USER` | The tailor and suggestion agents choose what to save from the user's answers and feedback, without asking about each fact. Users can also type facts in. Facts survive a resume re-upload. The whole bank goes into every tailor and suggestion run. Users view, edit and delete facts on `/memory` |
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

### 1.9 resland-mcp (Claude Code / Claude Desktop)

`backend/resland-mcp` is an MCP server a user runs on their own machine inside
their own Claude app. Claude does the tailoring on the user's Claude plan, and
the server reads and saves through the API as that user:

- **Sign-in:** Auth0's device flow, through its own Native application in the
  Resland tenant. The refresh token is saved on the user's machine
  (`~/.config/resland-mcp/credentials.json`, mode 0600).
- **Reads:** `GET /profile` (the whole base profile, including name, email,
  phone, location and links), `GET /memory`, and the tailored-resume board.
- **Writes:** memory facts (`POST /memory`) and tailored resumes
  (`POST`/`PATCH /tailored`). Exports are saved to `~/Downloads/resland`.
- **Where the data goes:** to Anthropic, under the user's own Claude account
  and terms. Nothing goes through OpenRouter, and nothing is charged to the
  balance.

It's installed from the repo today. If it's offered to users, the policy needs
to say that connecting a third-party AI client sends their data to that
client's provider, under the user's own agreement with them.

## 2. Who receives it (subprocessors)

| Service | Purpose | What it receives |
|---|---|---|
| **Railway** (US West) | Hosts the API, dispatcher, frontend, Postgres, and RabbitMQ | All app data at rest. Every page request and API call. The Auth0 session cookie passes through the frontend |
| **AWS S3** (`us-east-2`) | File storage | Original resumes and generated `.docx` files |
| **Auth0** (Okta) | Sign-in | The account itself: email, name, picture from the social or password login; login sessions. The API calls the Auth0 Management API to delete the login on account deletion and to read the login profile into the data export |
| **Stripe** | Payments | Everything entered at Checkout (email, card, billing details) plus our `auth0_id` in metadata. Account deletion expires open Checkout sessions and deletes the Stripe customer |
| **OpenRouter** | AI gateway for every model call | **Resume parsing:** the full resume text, including contact details. **Tailoring:** the full profile as JSON, including name, email, phone, location, links, plus the job description, the user's answers, and the whole memory bank. **Suggestions:** the experience entry and bullets, plus the user's guidance and answers and the whole memory bank (no contact details). **System design:** notes, diagram text, transcript, and for job-based sessions the job description. No user identifier is sent. **Zero data retention is enforced on all providers in the account settings** (owner, 2026-10-06) |
| **OpenAI, Anthropic** (via OpenRouter) | Running the models | The same content as above. The `/admin` model list offers OpenAI GPT and Anthropic Claude models. Resume parsing uses `RESUME_PARSER_MODEL`. If that is still `openrouter:openrouter/auto`, OpenRouter can pick another vendor's zero-retention endpoint. Pin it to an OpenAI or Claude model so the policy's list is complete |
| **LangSmith** (LangChain) | Agent tracing | When `LANGSMITH_TRACING=true` is set on the dispatcher, every prompt, tool output (resume text, contact details, job descriptions), model output, and user answer goes to the LangSmith project. Listed as a subprocessor by decision; set the project's trace retention to the shortest tier |
| **esm.sh** | Excalidraw fonts on `/system-design/[id]` | The visitor's IP and user agent (browser request). `EXCALIDRAW_ASSET_PATH` is unset, so the package falls back to the CDN |
| **Vercel** | None in production. Its GitHub app is still connected and builds previews of `frontend/` for PRs (seen on #79) | Whatever the preview environment is configured with. The repo doesn't show whether previews get production Auth0, database or API credentials. If they do, anyone signing in on a preview sends their session and data through Vercel. Disconnect it, or check the preview environment (§8) |

Not a subprocessor: Anthropic receiving data through resland-mcp (§1.9). The
user sends it from their own Claude app, under their own agreement with
Anthropic.

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
| Original resume in S3 | Until overwritten by a new upload | With the account |
| Profile (`user`, `user_base_*`, links, format) | Until re-upload or edit | Edit, or with the account |
| `generated.docx` | Until regenerated | With the account |
| Tailored resumes | Until deleted | Yes (S3 file deleted best effort) |
| Tailor runs | Until dismissed; completed runs are cleared when a new run starts | Yes |
| Suggestions | Until accepted or dismissed; re-upload deletes them | Yes |
| Memory facts | Until deleted. Kept across resume re-uploads | Yes, on `/memory` |
| System-design sessions and transcripts | Until dismissed | Yes |
| LangGraph checkpoints (`langgraph` schema): full conversations, including the tailor profile with contact details, and the user's answers | Deleted with their run or session, including when a re-upload deletes suggestion rows. **Kept forever** for a session that's abandoned rather than finished or dismissed. No TTL, no application-level encryption | Indirectly, and all of them with the account |
| AMQP dead-letter queues: failed job messages, which can contain user free text | **Forever.** No TTL and nothing consumes them | No. Account deletion can't reach them |
| `token_usage`, `balance_purchase` | Forever (accounting). On account deletion they stay, re-pointed to a tombstone user (`deleted\|<uuid4>`) that holds no personal data | No |
| `account_deletion`: a deleted login's Auth0 id | Until 3 days after Auth0 confirms the login is deleted (the longest session lifetime). Until then the API and frontend refuse that login's leftover sessions and tokens | n/a |
| `page_view` | Forever | n/a (anonymous) |
| Railway logs | 7 days (Hobby) / 30 days (Pro) | No |
| Postgres backups | **None today.** Planned: weekly, kept one month | No |
| Auth0 account | Until the account is deleted. If Auth0 fails, an API sweeper retries every 10 minutes until it confirms | With the account |
| Stripe customer | Until the account is deleted | With the account |
| Stripe payment records | Indefinitely, per Stripe's own obligations | No |
| LangSmith traces | Per the project's trace retention setting | No |

**Account deletion** (`DELETE /account`, `backend/api/src/api/account/`) is
refused while a job is running. Otherwise it:

- expires open Stripe Checkout sessions,
- deletes the S3 prefix `resumes/<auth0_id>/`,
- deletes the Stripe customer,
- deletes every user-owned DB row (`account.db.ERASED_TABLES`) and the
  LangGraph threads of their runs and sessions, and re-points the billing rows
  to a tombstone,
- deletes the Auth0 login.

Deletion can't reach dead-letter messages, platform logs, backups, LangSmith
traces, or Stripe's payment records. The policy should say those age out on
their own schedules, or stay under Stripe's obligations.

**Data export** (`GET /account/export`) is a .zip with `data.json`, the user's
S3 files, and a README. `data.json` holds the profile, memory, suggestions,
tailor runs, tailored resumes, mock interviews, DSA progress, purchases and
charges, and the Auth0 login profile. It leaves out:

- the LangGraph checkpoints, which hold the raw answers and guidance,
- internal fields: storage paths, provider costs, request ids, admin flags,
  and the interviewer's hidden notes,
- card details and logs.

The README in the archive says what's left out.

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
  - The whole memory bank goes into every tailor and suggestion run.
  - LangSmith receives traces.
- "A .zip with everything Resland stores about you" (Download Your Data,
  `frontend/app/(protected)/account/account-client.tsx`; Help says much the
  same).
  **Broader than the export:** it leaves out the LangGraph checkpoints, which
  hold the user's raw answers and guidance, plus internal fields and logs
  (§4). The README inside the archive says so, but the card doesn't.
- "Permanently deletes your profile, memory, uploaded and generated resumes,
  tailored resumes, suggestions, mock interviews and study progress, and
  removes your sign-in. Records of your purchases and charges are kept for our
  accounting, no longer linked to you." (Delete Your Account, account page;
  Help says much the same.) Accurate for what Resland holds. The policy still
  has to say that dead-letter messages, logs, backups and LangSmith traces age
  out on their own schedules (§4).
- "Unused balance isn't refunded when you delete your account" (account page,
  Help) and "As long as you keep your account, your balance never expires"
  (Help). Matches the decided terms (§7).
- "Fix anything that's wrong or out of date, and delete anything you don't
  want used." (`/memory`) Accurate: a deleted fact isn't used again. Copies in
  open sessions' checkpoints and in LangSmith traces stay until those go.
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
  - Tailoring through resland-mcp is free: it runs on the user's own Claude
    plan, and nothing is charged to the balance.
  - The balance never goes negative, and new jobs are refused at zero.
- **Balance and refunds (decided):**
  - The balance never expires.
  - Purchases aren't refundable except at the operator's discretion or where
    the law requires.
  - Any remaining balance is forfeited on account deletion. The Account &
    Data page shows the balance and warns about this before the user
    confirms.
  - A full Stripe refund removes the granted balance (floored at zero). A
    partial refund leaves the balance untouched, which is fine for
    discretionary refunds.
  - EU/UK consumers have a 14-day right to withdraw from digital services. It
    lapses only if they expressly ask for the service to start right away and
    acknowledge losing the right, which can be done in the checkout consent
    text. That's a lawyer question.
- **AI output:** generated resumes and suggestions can be wrong or embellished,
  and the user is responsible for what they send to employers. Interview grades
  are automated practice feedback, not hiring decisions. The memory bank is
  written by the AI from the user's answers, so its facts can be wrong too; the
  user can edit or delete them.
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
- Self-serve account deletion and data export merged (#81).
- A resume re-upload no longer orphans the checkpoints of the suggestions it
  deletes.

**Still to do**
1. Make account deletion and export work in production. Apply the S3
   `ListBucket` grant in `terraform/durable` (`iam.tf` marks it as not
   applied; without it, both fail with a 502 at the S3 listing step). Give the
   Railway API service the Auth0 Management API app's credentials (see #81).
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
6. Retention: add a TTL to the dead-letter queues, a `page_view` retention
   window, and a cleanup for the checkpoints of abandoned sessions.
7. Self-host the Excalidraw fonts (`EXCALIDRAW_ASSET_PATH`), or list esm.sh.
8. Update the Help page's privacy answer (§6).
9. Publish `/privacy`, `/terms`, and a refund policy. Add them to the footer
   `LEGAL_LINKS` and `app/sitemap.ts`, and set Checkout's
   `consent_collection.terms_of_service = "required"`.
10. Disconnect the Vercel GitHub app, or check that its preview deployments
    don't get production credentials (§2).
11. Decide whether resland-mcp is offered to users. If it is, cover
    connecting third-party AI clients in the policy (§1.9).
12. Narrow the export card's "everything Resland stores about you", or name
    what's left out (§6).
