from rabbitmq_amqp_python_client import Event

from ..runners.suggestions import SuggestionsRunner
from .generic import DispatchJobParams, GenericHandlerWithCleanup, HandlerError


class SuggestionHandler(GenericHandlerWithCleanup):
    def __init__(self):
        super().__init__()

    def on_amqp_message(self, event: Event):
        try:
            data = self.parse_event(event)

            session_id = data.get("session_id")
            if not session_id:
                raise HandlerError("Could not find `session_id` in message")

            runner = SuggestionsRunner(data)
            self.dispatch_job(
                DispatchJobParams(job_id=session_id, runner=runner, event=event)
            )
        except Exception as e:
            print(f"Error processing message: {e}")
            self.delivery_context.discard(event)
