from aio_pika.abc import AbstractIncomingMessage
from shared.pg import get_pg_client

from ..env_vars import PG_URL
from ..runners.db_ops import set_system_design_failed
from ..runners.system_design import SystemDesignRunner
from .generic import DispatchJobParams, GenericHandlerWithCleanup, HandlerError


class SystemDesignHandler(GenericHandlerWithCleanup):
    def __init__(self):
        super().__init__()

    async def on_message(self, message: AbstractIncomingMessage):
        self._ensure_cleanup_task()
        try:
            data = self.parse_event(message)

            session_id = data.get("session_id")
            if not session_id:
                raise HandlerError("Could not find `session_id` in message")

            runner = SystemDesignRunner(data)
            await self.dispatch_job(
                DispatchJobParams(job_id=session_id, runner=runner, message=message)
            )
        except Exception as e:
            print(f"Error processing message: {e}")
            await message.nack(requeue=False)

    def update_db_status(self, job_id: str, status: str):
        # The runner writes turn results itself; only hard failures need the
        # session row updated here.
        if status == "FAILED":
            with get_pg_client(PG_URL) as conn:
                set_system_design_failed(conn, job_id)
