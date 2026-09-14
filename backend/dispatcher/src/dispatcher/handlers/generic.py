import json
import threading
import time
from dataclasses import dataclass

from rabbitmq_amqp_python_client import AMQPMessagingHandler, Event
from shared.pg import get_pg_client

from ..env_vars import PG_URL
from ..runners.generic import JobHandle, JobRunner


class HandlerError(Exception):
    pass


@dataclass
class DispatchJobParams:
    job_id: str
    runner: JobRunner
    event: Event


class GenericHandlerWithCleanup(AMQPMessagingHandler):
    running_jobs: dict[str, tuple[JobHandle, Event]]
    cleanup_thread: threading.Thread

    def __init__(self):
        super().__init__()
        self.running_jobs = {}
        self.pg_client = get_pg_client(PG_URL)
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_finished_jobs, daemon=True
        )
        self.cleanup_thread.start()

    def _cleanup_finished_jobs(self):
        while True:
            time.sleep(1)
            # print(f"Cleaning up up to {len(self.running_jobs)} jobs")
            for job_id, (handle, event) in list(self.running_jobs.items()):
                poll_result = handle.poll()
                # Update job in db
                print(f"Updating job {job_id} with status {poll_result}")
                self.pg_client.execute(
                    "UPDATE user_upload_job SET status = %s WHERE id = %s",
                    (poll_result, job_id),
                )

                match poll_result:
                    case "COMPLETED":
                        del self.running_jobs[job_id]
                        print(f"Job {job_id} completed")
                        self.delivery_context.accept(event)
                    case "FAILED":
                        del self.running_jobs[job_id]
                        print(f"Job {job_id} failed")
                        self.delivery_context.discard(event)

    def parse_event(self, event: Event) -> dict:
        if not event.message:
            raise HandlerError("Could not find `message` in Event")

        if not event.message.body:
            raise HandlerError("Could not find `body` in `message`")

        return json.loads(str(event.message.body, "utf-8"))

    def dispatch_job(self, params: DispatchJobParams):
        handle = params.runner.run()
        self.running_jobs[params.job_id] = (handle, params.event)
