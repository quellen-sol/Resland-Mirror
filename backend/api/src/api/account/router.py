from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..auth import Auth0UserId
from ..deps import PgConnection
from . import model, service

router = APIRouter(prefix="/account")


@router.get(
    "/export",
    response_class=StreamingResponse,
    responses={200: {"content": {service.EXPORT_CONTENT_TYPE: {}}}},
)
async def export_account(user_id: Auth0UserId, pg_conn: PgConnection):
    raise NotImplementedError


# DELETE on the resource, not POST /account/delete: the operation is
# idempotent by design — a retry after a partial failure finishes the job,
# and repeating a finished deletion is a no-op success.
@router.delete("", response_model=model.DeleteAccountResponse)
async def delete_account(user_id: Auth0UserId, pg_conn: PgConnection):
    return await service.delete_account(pg_conn=pg_conn, user_id=user_id)
