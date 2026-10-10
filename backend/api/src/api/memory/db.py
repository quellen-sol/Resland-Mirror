"""Memory-bank SQL, mirroring the dispatcher's db_ops.save_memory_facts so a
fact saved over the API behaves like one an agent saved."""

from ..deps import PgConnection


async def list_facts(pg_conn: PgConnection, user_id: str):
    """(id, topic, content, source, updated_at) rows, grouped by topic and
    oldest first within one."""
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(
            """
            SELECT id, topic, content, source, updated_at FROM user_memory_fact
            WHERE user_id = %s ORDER BY topic, id
            """,
            [user_id],
        )
        return await res.fetchall()


async def count_facts(pg_conn: PgConnection, user_id: str) -> int:
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(
            "SELECT count(*) FROM user_memory_fact WHERE user_id = %s", [user_id]
        )
        return (await res.fetchone())[0]


async def rewrite_fact(
    pg_conn: PgConnection,
    user_id: str,
    fact_id: int,
    topic: str,
    content: str,
    source: str,
):
    """(id, topic, content) of the rewritten fact, or None when the id isn't
    one of the user's facts."""
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(
            """
            UPDATE user_memory_fact
            SET topic = %s, content = %s, source = %s, updated_at = now()
            WHERE id = %s AND user_id = %s
            RETURNING id, topic, content
            """,
            (topic, content, source, fact_id, user_id),
        )
        return await res.fetchone()


async def find_fact(pg_conn: PgConnection, user_id: str, topic: str, content: str):
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(
            """
            SELECT id, topic, content FROM user_memory_fact
            WHERE user_id = %s AND topic = %s AND content = %s
            ORDER BY id LIMIT 1
            """,
            (user_id, topic, content),
        )
        return await res.fetchone()


async def insert_fact(
    pg_conn: PgConnection, user_id: str, topic: str, content: str, source: str
):
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(
            """
            INSERT INTO user_memory_fact (user_id, topic, content, source)
            VALUES (%s, %s, %s, %s)
            RETURNING id, topic, content
            """,
            (user_id, topic, content, source),
        )
        return await res.fetchone()
