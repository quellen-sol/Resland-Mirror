from aio_pika.abc import AbstractIncomingMessage
from shared.pg import get_pg_client

from ..env_vars import PG_URL
from ..runners.db_ops import set_suggestion_failed
from ..runners.suggestions import SuggestionsRunner
from .generic import DispatchJobParams, GenericHandlerWithCleanup, HandlerError


class SuggestionHandler(GenericHandlerWithCleanup):
    def __init__(self):
        super().__init__()

    def update_db_status(self, job_id: str, status: str):
        # The runner writes WAITING_FOR_INPUT/COMPLETED itself; only hard
        # failures need the session row updated here.
        if status == "FAILED":
            with get_pg_client(PG_URL) as conn:
                set_suggestion_failed(conn, job_id)

    async def on_message(self, message: AbstractIncomingMessage):
        self._ensure_cleanup_task()
        try:
            data = self.parse_event(message)

            session_id = data.get("session_id")
            if not session_id:
                raise HandlerError("Could not find `session_id` in message")

            runner = SuggestionsRunner(data)
            await self.dispatch_job(
                DispatchJobParams(
                    job_id=session_id, runner=runner, message=message
                )
            )
        except Exception as e:
            print(f"Error processing message: {e}")
            await message.nack(requeue=False)
