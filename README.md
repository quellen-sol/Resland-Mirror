# Resland

**AI resume tailoring for software engineers.** You upload a resume. Resland's agents
ask about the work behind each bullet, rewrite the bullets with the details that matter,
and tailor the whole resume to a specific job posting. The result exports as a `.docx`
that keeps your original layout.

It also runs graded system design mock interviews on a whiteboard canvas, and hosts a
free data structures and algorithms study center.

**Live:** [resland.org](https://resland.org)

---

## At a glance

- **Async agent pipeline.** A FastAPI service queues every LLM job on RabbitMQ. A separate
  dispatcher runs the LangGraph agents, so no LLM call ever runs inside an HTTP request.
- **Human-in-the-loop agents that survive restarts.** Agents pause mid-run to ask the user
  questions. Their state is checkpointed to Postgres, so a run can wait days for an answer,
  or come back after a crash or redeploy.
- **Validation in code, not just in the prompt.** Every agent submits its work through a
  typed tool call that code checks before saving. A tailored resume that drops a job,
  moves a bullet to the wrong role, or lists a skill you don't have is sent back to the
  model to fix.
- **Parsing that keeps your formatting.** Custom PDF and DOCX parsers handle two-column
  layouts, sidebars and drawn bullet markers. Fonts, spacing, margins and section order are
  captured from the upload so exports look like your own resume.
- **Usage-based billing that can't double-charge.** Every model response is billed at the
  cost the provider reports. An append-only ledger keyed per conversation turn makes a
  redelivered queue message free. Payments go through Stripe (prepaid balance, webhook
  driven).
- **Tested.** About 1,000 backend tests across four Python packages, plus a fixture corpus of
  hard PDF layouts. CI runs the backend suites against a real Postgres on every pull request.

## Features

| Feature | What happens |
|---|---|
| **Resume import** | Upload a PDF or DOCX. A parser agent turns it into a structured profile: jobs, bullets, skills, education, projects. |
| **Bullet coaching** | Pick a job or a single bullet. The agent asks up to four targeted questions ("About how many orders a day did the checkout service handle?"), then writes three different rewrites per bullet. Apply one, or ask for another round. |
| **Tailoring** | Paste a job posting. The agent works out what the posting values most, asks about the matching work in your history, and rewrites and reorders your resume around it. You review it, ask for revisions, then save, edit and export. |
| **Memory bank** | The facts you give in those interviews are saved, so later coaching and tailoring runs use them instead of asking again. You can review and edit them on the Memory page. |
| **Export** | Rebuilds a `.docx` from your profile, or from a tailored version, using the formatting captured from your original upload. |
| **Tailor with Claude** | A personal MCP server lets Claude Code or Claude Desktop tailor your resume against your Resland account on your own Claude plan, with the same writing rules and memory bank as the site's agent. |
| **Your data** | Download everything Resland stores about you as a zip, or delete your account and its Auth0 login. |
| **System design interviews** | A 45-minute mock interview in four timed phases, with an Excalidraw canvas for your diagram. An interviewer agent runs it, then a separate grader scores you against a six-part rubric and gives a letter grade, a hire signal and written feedback. |
| **DSA study center** | 28 topics, each worked example written in TypeScript, Python, Go, C# and Java. Every example is also a test: all five versions are run and their output is checked. |

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16 (App Router, React 19 server components), TypeScript, Tailwind CSS 4, shadcn/ui, Excalidraw |
| API | Python 3.14, FastAPI, psycopg 3 (async), PyJWT (Auth0 RS256), Stripe |
| Agents | LangGraph, LangChain, OpenRouter (model chosen per job), `langgraph-checkpoint-postgres` |
| Documents | pdfminer.six, python-docx, custom layout analysis and `.docx` renderer |
| Messaging | RabbitMQ 4 via aio-pika (topic exchanges, durable queues, dead-letter queues) |
| Data | PostgreSQL 18, schema defined as a Prisma-Next contract |
| Auth | Auth0 (Next.js session, JWT bearer tokens to the API, device flow for the MCP server) |
| MCP | MCP Python SDK (stdio server for Claude Code and Claude Desktop) |
| Infra | Railway (frontend, API, dispatcher, Postgres, RabbitMQ). AWS S3 via Terraform. Docker. |
| Tooling | uv workspace, pnpm, ruff, pytest, `node --test`, GitHub Actions |

## Architecture

```mermaid
flowchart LR
    user(["Browser"])
    claude(["Claude Code / Desktop"])
    mcp["resland-mcp<br/>(local, stdio)"]

    subgraph web["Next.js frontend"]
        rsc["Server components<br/>and server actions"]
        client["Client components<br/>(forms, polling, Excalidraw)"]
    end

    api["FastAPI<br/>auth, billing, job submission"]
    mq[("RabbitMQ<br/>4 work queues + DLQs")]

    subgraph disp["Dispatcher"]
        consumers["AMQP consumers"] --> runners["Job runners<br/>(worker threads)"] --> agents["LangGraph agents"]
    end

    llm["OpenRouter"]
    pg[("PostgreSQL<br/>app data, agent checkpoints,<br/>token ledger")]
    s3[("S3<br/>uploads, generated .docx")]
    auth0["Auth0"]
    stripe["Stripe"]

    user --> rsc
    user --> client
    rsc -- "Prisma-Next" --> pg
    client -- "Bearer JWT" --> api
    claude --> mcp
    mcp -- "Bearer JWT" --> api
    api -. "JWKS" .-> auth0
    rsc -. "session" .-> auth0
    api --> pg
    api --> s3
    api -- "persistent job message" --> mq
    mq --> consumers
    agents --> llm
    runners --> pg
    runners --> s3
    stripe -- "webhooks" --> api
```

There are three deployable pieces. The API and the dispatcher ship as one Docker image
with two entrypoints (`uv run api` and `uv run dispatcher`).

- **Frontend** ([`frontend/`](frontend/)). Server components read Postgres directly through
  the Prisma-Next ORM, and simple profile edits go through server actions. Anything that
  costs money or starts an agent goes through the API.
- **API** ([`backend/api/`](backend/api/)). Verifies the Auth0 JWT, checks the user's balance,
  writes the job row, and publishes a message. It never waits on a model. It also serves
  the account export and deletion, and the profile, memory and tailored-resume endpoints
  the MCP server uses.
- **Dispatcher** ([`backend/dispatcher/`](backend/dispatcher/)). One consumer per queue. Each
  job runs on a worker thread, writes its progress and results back to the job's row, and
  records what it cost.
- **Shared** ([`backend/shared/`](backend/shared/)). The AMQP client and job message
  dataclasses, the document IR and `.docx` renderer, the writing and memory rules, and the
  system design rubric and diagram analysis. Both services import it, and so does the MCP
  server.

The fourth Python package, [`backend/resland-mcp/`](backend/resland-mcp/), isn't deployed.
It runs on the user's own machine (see [Tailoring with Claude](#tailoring-with-claude-mcp-server)).

### Lifecycle of a job

Every agent feature follows the same pattern. Here is one tailor run:

```mermaid
sequenceDiagram
    actor U as User
    participant FE as Frontend
    participant API as FastAPI
    participant MQ as RabbitMQ
    participant D as Dispatcher
    participant PG as Postgres
    participant LLM as OpenRouter

    U->>FE: Paste a job posting
    FE->>API: POST /tailor
    API->>PG: Check balance, insert run, commit
    API->>MQ: Publish AmqpTailorJob(run_id)
    API-->>FE: run_id
    MQ->>D: Deliver message
    D->>PG: Load run, profile and checkpoint
    loop Until the agent asks a question or submits
        D->>LLM: Model call
        LLM-->>D: Tool calls
    end
    D->>PG: Save checkpoint, question and status, record token usage
    D->>MQ: Ack
    FE->>API: Poll run status every 3s
    API-->>FE: WAITING_FOR_INPUT + question
    U->>FE: Answer
    FE->>API: POST /tailor/{id}/answer
    API->>MQ: Publish AmqpTailorJob(run_id, answer)
    MQ->>D: Deliver, graph resumes from checkpoint
```

A few details make this hold up in production:

- **Commit before publish.** The API commits the job row before it publishes, so the
  dispatcher can never pick up a job whose row isn't visible yet.
- **At-least-once delivery is expected.** Messages are persistent and acked only after
  the job settles. A redelivery of a job that's still running is acked and dropped. Each
  publish carries a fresh `turn_id`, and `token_usage` has a unique key on it, so a
  redelivered turn can't charge twice.
- **Failures leave the run resumable.** If the model provider errors mid-run, the run gets
  a "something went wrong, send any message to continue" prompt instead of failing. The
  next message resumes the graph from its last checkpoint. Hard failures (bad data, missing
  rows) are nacked into a per-queue dead-letter queue.
- **The broker topology is code.** The dispatcher declares the exchanges, queues, bindings
  and dead-letter routing on startup ([`shared/amqp.py`](backend/shared/src/shared/amqp.py)).
  Each consumer gets its own channel on one auto-reconnecting connection.

## Agent flows

All agents live in [`backend/dispatcher/src/dispatcher/agents/`](backend/dispatcher/src/dispatcher/agents/).
The prompts are in the same files as the graphs, so you can read each agent top to bottom.

### Shared design

The multi-turn agents (suggestions, tailor, system design) share one shape:

- A LangGraph `StateGraph` loops between an `llm_call` node and a `tool_node`.
- **Tools are the only way to reach the user.** Plain text from the model is never shown.
  The agent asks with `ask_clarifying_question` and delivers with a `submit_*` tool.
- Asking calls LangGraph's `interrupt()`. The graph stops and the checkpoint is saved to
  Postgres, keyed by the run's id. The user's answer arrives as a new queue message and
  resumes the graph with `Command(resume=answer)`.
- **Submit tools validate before they save.** A submission that fails the check returns the
  problem to the model as the tool result ("Not submitted: ... Fix it and submit again")
  and is never stored.
- Job postings, resumes and candidate notes are wrapped as data in the prompts. Any
  instructions inside them are ignored.
- The resume-writing agents share one set of writing rules
  ([`shared/writing.py`](backend/shared/src/shared/writing.py)): never invent metrics,
  tools or scope, no placeholder numbers, and none of the words that make a resume read as
  machine-written.
- **The interviewing agents remember answers.** Coaching and tailoring read the user's
  memory bank along with the profile, and save the lasting facts from each answer with a
  `remember_facts` tool, so a later run doesn't ask again. The whole bank goes into every
  run's context, so it's capped at 200 facts. A batch with a bad entry is rejected whole,
  so the model can resend it without duplicating the good ones. Limits and prompt rules are
  in [`shared/memory.py`](backend/shared/src/shared/memory.py).

```mermaid
flowchart TD
    start(["Queue message"]) --> llm["llm_call"]
    llm -->|"tool calls"| tools["tool_node"]
    tools -->|"ask_clarifying_question"| ask["⏸ interrupt: question to the user"]
    tools -->|"submit passed validation"| review["⏸ interrupt: result to the user"]
    tools -->|"read / verify / remember tools"| llm
    ask -->|"answer arrives as the next message"| llm
    review -->|"user asks for changes"| llm
    llm -->|"no tool call before submitting<br/>(tailor only)"| nudge["nudge"]
    nudge --> llm
    llm -->|"no tool call after submitting"| done(["Done"])
```

### 1. Resume parser

[`runners/resume.py`](backend/dispatcher/src/dispatcher/runners/resume.py),
[`agents/docx_parser.py`](backend/dispatcher/src/dispatcher/agents/docx_parser.py),
[`doc_parsers/pdf.py`](backend/dispatcher/src/dispatcher/doc_parsers/pdf.py)

```mermaid
flowchart LR
    upload["Upload<br/>.pdf or .docx"] --> s3[("S3")] --> sniff["Detect type<br/>from magic bytes"]
    sniff --> parser["Layout parser<br/>python-docx / pdfminer"]
    parser --> views["Four document views"]
    views --> agent["Parser agent"]
    agent -->|"submit_user_profile"| profile["Structured profile"]
    parser --> capture["Format capture"]
    profile --> capture
    profile --> pg[("Postgres")]
    capture -->|"FormatProfile"| pg
```

Models read layout badly from raw text. Two-column resumes and right-aligned dates come out
in the wrong order. So deterministic code does the layout work first, and the agent gets
four views of the document as tools:

1. **Raw text.**
2. **Block sequence.** Paragraphs or lines in order, with style, font and weight.
3. **Whitespace map.** The gaps above and below each block, which mark section boundaries.
4. **Column counts** per page or section.

For PDFs, the parser normalizes pdfminer's output into its own IR
([`shared/pdfdoc.py`](backend/shared/src/shared/pdfdoc.py)). It then detects text columns
from vertical channels of white space, merges right-floated dates into their row, and tells
drawn bullet dots apart from contact icons by size, shape and position.

The agent copies values verbatim and submits a typed profile once. A second pass then
matches that profile back against the document to capture a `FormatProfile`: fonts and
sizes per role (name, section header, entry title, bullet...), spacing, margins, section
order and titles, and bullet glyph. That profile is what makes exports look like the
user's own resume.

### 2. Bullet coaching (suggestions)

[`agents/suggestions.py`](backend/dispatcher/src/dispatcher/agents/suggestions.py)

| | |
|---|---|
| **Tools** | `get_user_bullet_points`, `ask_clarifying_question`, `remember_facts`, `verify_final_suggestions`, `submit_suggestions` |
| **Flow** | Read the job, its bullets and the memory bank → ask up to 4 specific questions about scale, results, ownership and difficulty that memory doesn't already answer (at most one follow-up round) → save the lasting facts to memory → write three options per bullet, each leading with a different true strength of the work → verify → submit → wait for review |
| **Review** | Applying an option writes it to the profile and ends the session. Any reply ("shorter", "lead with the cost savings") gets a fresh set of three, with the earlier options still in context. |
| **Checks** | Every bullet id belongs to the session, exactly three options per bullet, no blank options, and no duplicates after ignoring case, spacing and a trailing period. |

### 3. Tailoring

[`agents/tailor.py`](backend/dispatcher/src/dispatcher/agents/tailor.py),
[`runners/tailor.py`](backend/dispatcher/src/dispatcher/runners/tailor.py)

| | |
|---|---|
| **Tools** | `get_job_description`, `get_user_profile`, `ask_clarifying_question`, `remember_facts`, `verify_tailored_resume`, `submit_tailored_resume` |
| **Flow** | Read the posting the way its hiring manager would and pick the 4-6 things it values most → map them onto the profile and memory (what already proves a need, bullets that relate but say too little, needs nothing covers) → ask up to 5 questions tied to the posting that memory doesn't already answer → save the lasting facts to memory → rewrite bullets so the matching work comes first, reorder skills, write a summary if asked → verify → submit |
| **Review** | The user can ask for revisions in plain language. The agent revises and resubmits on the same checkpointed thread. Saving copies the result into an editable tailored resume that exports to `.docx`. |
| **Checks** | Every experience in the profile is still present, so the work history shows no gaps. Each experience keeps at least one bullet. Every bullet id stays under the experience it came from. Every skill comes from the user's profile. |

The tailor graph has two extra safeguards because every loop is a billed model call:

- **Nudging stalls.** A reply with no tool call before anything is submitted is a stall,
  not an answer, since the user can't see it. A `nudge` node sends the model back to its
  tools, at most twice in a row. Tool calls whose JSON doesn't parse get an error back as
  their result, so the model can retry.
- **A recursion limit of 40 steps per user action.** LangGraph's default is over 10,000,
  so a model stuck resubmitting a rejected resume would otherwise run thousands of paid
  calls.

### 4. System design interview

[`agents/system_design.py`](backend/dispatcher/src/dispatcher/agents/system_design.py),
[`shared/system_design/`](backend/shared/src/shared/system_design/)

```mermaid
flowchart LR
    subgraph setup["Problem"]
        bank["Problem bank<br/>(16 hand-checked briefs)"]
        writer["Brief writer agent<br/>(problem from a job posting)"]
    end
    setup --> req["Requirements<br/>6 min"] --> est["Estimation<br/>5 min"] --> hld["High-level design<br/>15 min"] --> dd["Deep dive<br/>15 min"] --> grader["Grader agent"] --> report["Report:<br/>grade, hire signal, feedback"]
```

Three separate model roles:

- **Brief writer.** For job-based interviews, it writes a problem from the company's own
  product domain, plus a private brief: clarification answers, expected requirements and
  estimates, a reference design, deep-dive topics and common pitfalls. Bank problems come
  with a hand-checked brief, and their opening message is built from a template, so
  starting one costs nothing.
- **Interviewer.** A checkpointed thread that plays a senior engineer. It answers from the
  brief, reveals scale numbers only when asked, and drives the deep dive one question at a
  time. Its tools are `calculate`, which checks the candidate's arithmetic with an AST-based
  evaluator (no `eval`), and `end_interview`.
- **Grader.** A fresh context, so the interviewer never grades its own conversation, and
  optionally a stronger model. It scores six dimensions from 1 to 5 against the target level
  (mid, senior or staff), citing evidence for each score. The letter grade and hire signal
  are then computed in code from the weighted scores
  ([`rubric.py`](backend/shared/src/shared/system_design/rubric.py)), so they stay
  consistent across models. One dimension far below the bar blocks a hire.

**The interviewer sees the diagram as a graph, not as pixels.**
[`diagram.py`](backend/shared/src/shared/system_design/diagram.py) turns the Excalidraw scene
JSON into components and connections. It uses each arrow's bindings for its endpoints and
infers each component's kind from its label ("Redis" is a cache, "Kafka" a queue). Each turn
sends only what changed since the interviewer last looked: notes are compared by hash and
the diagram as a graph diff. That keeps long interviews from re-sending the whole design
every turn. In the deep dive, simple heuristics about the design are added as hints for the
interviewer to check against the diagram.

## Tailoring with Claude (MCP server)

[`backend/resland-mcp/`](backend/resland-mcp/) is a personal MCP server for Claude Code and
Claude Desktop. Claude does the writing on the user's own Claude plan, so nothing goes
through OpenRouter and nothing is charged to the Resland balance.

- It runs locally over stdio and signs in with Auth0's device flow, so every call reaches
  the API as the user (`GET /profile`, `GET`/`POST /memory`, `/tailored`).
- Its tools read the profile and memory bank, add facts to memory, and save, edit and export
  tailored resumes to the same board the site uses.
- A `get_tailoring_guide` tool and a `tailor` prompt serve the site's own bullet-writing and
  memory rules from `shared`, so Claude follows the same rules as the tailor agent.
- Contract tests drive its tools against the real API routes and a live Postgres, so a
  change to those endpoints can't silently break it.

Setup (an Auth0 Native app, `resland-mcp login`, `claude mcp add`) is in its
[README](backend/resland-mcp/README.md).

## Billing and cost controls

LLM usage is billed against a prepaid balance. More detail in
[`docs/stripe-billing-plan.md`](docs/stripe-billing-plan.md).

- **Metered at real cost.** Each model response's cost, as reported by OpenRouter (net of
  caching discounts), is added up per turn. If a response lacks it, the dispatcher asks
  OpenRouter's generation stats endpoint, then falls back to the model's rate card. Charges
  round up to 1/10,000 of a cent, so small calls are never free.
- **Gate at the start, never mid-run.** The API refuses to start a job at zero balance
  (HTTP 402). A job already running always finishes, and the balance floors at zero.
- **Models are an allowlist.** Admins enable models and set prices in an admin panel. A
  user-chosen model must match an enabled row, so a free-form model string never reaches
  the model client.
- **Stripe checkout and webhooks.** The client sends only a pack id, and prices live on the
  server. Credits apply only on the `PENDING → COMPLETED` transition, so a redelivered
  webhook can't credit twice. A full refund takes the credit back.

## Repository layout

```
backend/
  api/          FastAPI app: auth, uploads, job submission, tailored resumes, memory,
                billing, admin, account export and deletion
  dispatcher/   AMQP consumers, job runners, LangGraph agents, PDF/DOCX layout parsers
  shared/       AMQP client and job types, .docx renderer, PDF IR, writing and memory
                rules, system design rubric
  resland-mcp/  Personal MCP server for tailoring with Claude Code or Claude Desktop
frontend/
  app/          Next.js routes: dashboard, tailor, tailored, memory, system-design, dsa,
                billing, account, admin
  content/dsa/  Study center topics, with runnable examples in five languages
  prisma/       contract.prisma, the database schema for the whole system
terraform/      The S3 bucket and IAM user for resume files
docs/           Design docs
compose.yml     Local RabbitMQ, Postgres, API and dispatcher
AGENTS.md       Contributor guide: toolchain, conventions, pitfalls
```

## Data model

The schema is one [Prisma-Next contract](frontend/prisma/contract.prisma) shared by both
languages: the frontend uses the generated ORM, and the Python services write plain SQL
with psycopg. The main groups of tables:

- **Profile.** `user`, experiences, bullets, skills, education, projects, social links, and
  the memory bank (`user_memory_fact`).
- **Agent sessions.** `user_suggestion`, `user_tailor_run`, `user_system_design_session`
  and its messages. Each row holds the status, the pending question and the result the UI
  polls for.
- **Documents.** `user_resume_format` (the captured `FormatProfile`), tailored and generated
  resumes.
- **Money.** `token_usage` (append-only, one row per job turn), `model_pricing`,
  `balance_purchase`.

LangGraph's checkpoint tables live in their own `langgraph` schema. The dispatcher creates
them on startup, so they stay outside the contract and Prisma's schema sync never touches
them.

**Deleting an account** ([`backend/api/src/api/account/`](backend/api/src/api/account/))
erases every row and S3 file the user owns, but keeps `balance_purchase` and `token_usage`,
re-pointed at a placeholder user with no personal data, so revenue and usage totals still
add up. It locks the user row and refuses while a job is still running. An
`account_deletion` row that holds only the Auth0 id lets a background sweeper retry deleting
the Auth0 login, and makes the API and the frontend refuse sessions issued before the
deletion. Live-schema tests fail if a new table that references a user isn't added to the
erase and export lists, so nothing new can be left behind.

## Infrastructure

Everything runs in one [Railway](https://railway.com) project: the frontend
(resland.org), the API (api.resland.org), the dispatcher, Postgres and RabbitMQ. Railway
builds each service from `master` when a push touches its files. The API and the
dispatcher build the same [`Dockerfile`](Dockerfile) and differ only in their start
command. Postgres and RabbitMQ are reachable only over Railway's private network.

Uploaded resumes and generated documents live in S3. The bucket and the IAM user the
services sign in with are defined in [`terraform/durable/`](terraform/durable/).

## Running locally

Prerequisites: Docker, Python 3.14 with [uv](https://docs.astral.sh/uv/), Node 24 with
pnpm 10.

```bash
# Infrastructure: RabbitMQ (management UI on :15672) and Postgres
docker compose up -d amqp postgres

# Database schema
(cd frontend && pnpm install &&
  DATABASE_URL=postgres://resland:resland@localhost:5432/resland pnpm prisma db init)

# Copy each .env.example to .env (or .env.local) and fill in Auth0, AWS and OpenRouter values
#   backend/api/.env.example  backend/dispatcher/.env.example  frontend/.env.example

# Run each in its own terminal
cd backend/dispatcher && uv run dispatcher   # declares the RabbitMQ topology on startup
cd backend/api && uv run api                 # http://localhost:3001 (OpenAPI docs at /docs)
cd frontend && pnpm dev                      # http://localhost:3000
```

Without an `OPENROUTER_API_KEY`, agent jobs still go through the whole pipeline and stop at
`WAITING_FOR_INPUT`. [`AGENTS.md`](AGENTS.md) covers the full setup, the test database and
known pitfalls.

## Tests

```bash
cd backend/shared     && uv run pytest --cov
cd backend/api        && uv run pytest --cov
cd backend/dispatcher && uv run pytest --cov
cd backend/resland-mcp && uv run pytest --cov
cd frontend           && pnpm test && pnpm lint && npx tsc --noEmit
```

- Tests run against fakes by default. Tests that need Postgres run against a scratch
  `resland_test` database, and a guard refuses to truncate any database that isn't marked
  as scratch.
- Agent tests drive the real LangGraph graphs with scripted model responses. They cover the
  interrupt and resume paths, the validators, stalls, crash recovery and billing.
- The PDF parser is tested against a generated corpus of hard layouts (sidebars, two
  columns, icon grids, entries split across pages, CJK names, scanned pages with no text)
  plus real-world resume layouts (a Canva export and a Google Docs export) whose text was
  rewritten as a fictional persona. Separate fidelity tests check that DOCX and PDF
  formatting survive a round trip through the renderer.
- CI ([`.github/workflows/pr-ci.yml`](.github/workflows/pr-ci.yml)) applies the schema to
  Postgres 18 and runs all four backend suites on every pull request.
