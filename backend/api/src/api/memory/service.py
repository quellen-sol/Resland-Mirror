from shared.memory import MAX_MEMORY_FACTS

from ..deps import PgConnection
from ..user_row import share_user_row
from . import db, model

# The only API writer is the personal MCP server, which saves what the user
# told Claude while tailoring — the /memory page labels it "From tailoring".
SOURCE = "TAILOR"


async def list_memory(pg_conn: PgConnection, user_id: str) -> model.MemoryListResponse:
    rows = await db.list_facts(pg_conn, user_id)
    return model.MemoryListResponse(
        facts=[
            model.MemoryFactItem(
                id=fact_id,
                topic=topic,
                content=content,
                source=source,
                updated_at=updated_at.isoformat(),
            )
            for fact_id, topic, content, source, updated_at in rows
        ]
    )


async def remember(
    pg_conn: PgConnection, user_id: str, req: model.RememberRequest
) -> model.RememberResponse:
    """Store facts in the user's bank. Safe to repeat: a fact that's already
    there isn't stored twice, and replaces_id rewrites a fact in place (or
    falls through to an insert when it isn't one of the user's facts)."""
    saved: list[model.MemoryFact] = []
    full = 0
    async with pg_conn.transaction():
        # A clean 404 for a deleted account rather than an FK error mid-batch.
        await share_user_row(pg_conn, user_id)
        count = await db.count_facts(pg_conn, user_id)
        for fact in req.facts:
            row = None
            if fact.replaces_id is not None:
                row = await db.rewrite_fact(
                    pg_conn, user_id, fact.replaces_id, fact.topic, fact.content, SOURCE
                )
            if row is None:
                row = await db.find_fact(pg_conn, user_id, fact.topic, fact.content)
            if row is None:
                if count >= MAX_MEMORY_FACTS:
                    full += 1
                    continue
                row = await db.insert_fact(
                    pg_conn, user_id, fact.topic, fact.content, SOURCE
                )
                count += 1
            saved.append(model.MemoryFact(id=row[0], topic=row[1], content=row[2]))
    return model.RememberResponse(saved=saved, full=full)
