from aio_pika.abc import AbstractIncomingMessage
from shared.pg import get_pg_client

from ..env_vars import PG_URL
from ..runners.db_ops import set_tailor_failed
from ..runners.tailor import TailorRunner
from .generic import DispatchJobParams, GenericHandlerWithCleanup, HandlerError


class TailorHandler(GenericHandlerWithCleanup):
    def __init__(self):
        super().__init__()

    async def on_message(self, message: AbstractIncomingMessage):
        self._ensure_cleanup_task()
        try:
            data = self.parse_event(message)

            run_id = data.get("run_id")
            if not run_id:
                raise HandlerError("Could not find `run_id` in message")

            runner = TailorRunner(data)
            self.dispatch_job(
                DispatchJobParams(job_id=run_id, runner=runner, message=message)
            )
        except Exception as e:
            print(f"Error processing message: {e}")
            await message.nack(requeue=False)

    def update_db_status(self, job_id: str, status: str):
        # The runner writes WAITING_FOR_INPUT/COMPLETED itself; only hard
        # failures need the run row updated here.
        if status == "FAILED":
            with get_pg_client(PG_URL) as conn:
                set_tailor_failed(conn, job_id)
