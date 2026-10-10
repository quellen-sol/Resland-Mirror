"""Where the dispatcher's LangGraph checkpointer keeps its tables.

They live in their own Postgres schema rather than `public`: Prisma's
`db update` only reads the schemas the contract declares, and drops any table
it finds there that the contract doesn't model. LangGraph owns these
definitions, so they stay out of the contract and out of Prisma's sight.
"""

CHECKPOINT_SCHEMA = "langgraph"

# Every table PostgresSaver.setup() creates, migrations bookkeeping included.
CHECKPOINTER_TABLES = (
    "checkpoint_migrations",
    "checkpoints",
    "checkpoint_blobs",
    "checkpoint_writes",
)

# The tables holding a thread's state, keyed on thread_id — schema-qualified,
# for the raw cleanup deletes outside the checkpointer.
CHECKPOINT_TABLES = tuple(
    f"{CHECKPOINT_SCHEMA}.{t}"
    for t in ("checkpoints", "checkpoint_blobs", "checkpoint_writes")
)

# App tables whose row ids double as LangGraph thread ids: a suggestion
# session, a tailor run, a system design interview. Deleting one of these rows
# should delete its thread too.
THREAD_OWNER_TABLES = (
    "user_suggestion",
    "user_tailor_run",
    "user_system_design_session",
)

# libpq startup options for a checkpointer connection: PostgresSaver uses
# unqualified table names, so search_path is what lands them in the schema.
CHECKPOINT_CONN_OPTIONS = f"-c search_path={CHECKPOINT_SCHEMA}"
