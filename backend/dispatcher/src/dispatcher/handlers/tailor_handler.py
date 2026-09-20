from rabbitmq_amqp_python_client import Event

from ..runners.db_ops import set_tailor_failed
from ..runners.tailor import TailorRunner
from .generic import DispatchJobParams, GenericHandlerWithCleanup, HandlerError


class TailorHandler(GenericHandlerWithCleanup):
    def __init__(self):
        super().__init__()

    def on_amqp_message(self, event: Event):
        try:
            data = self.parse_event(event)

            run_id = data.get("run_id")
            if not run_id:
                raise HandlerError("Could not find `run_id` in message")

            runner = TailorRunner(data)
            self.dispatch_job(
                DispatchJobParams(job_id=run_id, runner=runner, event=event)
            )
        except Exception as e:
            print(f"Error processing message: {e}")
            self.delivery_context.discard(event)

    def update_db_status(self, job_id: str, status: str):
        # The runner writes WAITING_FOR_INPUT/COMPLETED itself; only hard
        # failures need the run row updated here.
        if status == "FAILED":
            set_tailor_failed(self.pg_client, job_id)
