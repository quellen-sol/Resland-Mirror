"""Row lock that keeps new work from racing an account deletion.

Account deletion holds FOR UPDATE on the user's row while it checks for
in-flight jobs and erases everything. Inserting into a user-owned table
already conflicts with that (the foreign-key check takes FOR KEY SHARE on the
row), but some writes don't touch the foreign key: flipping a waiting session
back to PROCESSING, or writing a generated file to S3. Those call
share_user_row() first, in the same transaction as the write, so either the
deletion sees their work (and refuses with 409) or they see the account is
gone (and stop with 404) — never half of each.
"""

from fastapi import HTTPException

from .deps import PgConnection


async def share_user_row(conn: PgConnection, user_id: str) -> None:
    """FOR KEY SHARE on the user's row until the current transaction ends.

    Blocks while a deletion holds the row; raises 404 when the account no
    longer exists. Call it inside `conn.transaction()` — on an autocommit
    connection outside one, the lock is released as soon as it's taken."""
    raise NotImplementedError
