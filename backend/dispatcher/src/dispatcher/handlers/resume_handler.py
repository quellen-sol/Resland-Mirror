from rabbitmq_amqp_python_client import Event

from ..runners.resume_runner import ResumeRunner
from .generic import DispatchJobParams, GenericHandlerWithCleanup, HandlerError


class ResumeHandler(GenericHandlerWithCleanup):
    def __init__(self):
        super().__init__()

    def on_amqp_message(self, event: Event):
        try:
            data = self.parse_event(event)

            job_id = data.get("job_id")
            if not job_id:
                raise HandlerError("Could not find `job_id` in message")

            runner = ResumeRunner(data)
            self.dispatch_job(
                DispatchJobParams(job_id=job_id, runner=runner, event=event)
            )
        except Exception as e:
            print(f"Error processing message: {e}")
            self.delivery_context.discard(event)
