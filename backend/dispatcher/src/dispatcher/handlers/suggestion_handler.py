from aio_pika.abc import AbstractIncomingMessage

from ..runners.suggestions import SuggestionsRunner
from .generic import DispatchJobParams, GenericHandlerWithCleanup, HandlerError


class SuggestionHandler(GenericHandlerWithCleanup):
    def __init__(self):
        super().__init__()

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
