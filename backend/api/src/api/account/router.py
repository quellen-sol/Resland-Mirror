from collections.abc import Iterator
from typing import IO

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..auth import Auth0UserId
from ..deps import PgConnection
from . import model, service

router = APIRouter(prefix="/account")

_STREAM_CHUNK = 64 * 1024


def _stream(archive: IO[bytes]) -> Iterator[bytes]:
    try:
        while chunk := archive.read(_STREAM_CHUNK):
            yield chunk
    finally:
        archive.close()


@router.get(
    "/export",
    response_class=StreamingResponse,
    responses={200: {"content": {service.EXPORT_CONTENT_TYPE: {}}}},
)
async def export_account(user_id: Auth0UserId, pg_conn: PgConnection):
    archive = await service.export_account(pg_conn=pg_conn, user_id=user_id)
    return StreamingResponse(
        _stream(archive),
        media_type=service.EXPORT_CONTENT_TYPE,
        headers={
            "Content-Disposition": (
                f'attachment; filename="{service.export_filename()}"'
            ),
            # Personal data — never let a shared cache keep a copy.
            "Cache-Control": "no-store",
        },
    )


# DELETE on the resource, not POST /account/delete: the operation is
# idempotent by design — a retry after a partial failure finishes the job,
# and repeating a finished deletion is a no-op success.
@router.delete("", response_model=model.DeleteAccountResponse)
async def delete_account(user_id: Auth0UserId, pg_conn: PgConnection):
    return await service.delete_account(pg_conn=pg_conn, user_id=user_id)
