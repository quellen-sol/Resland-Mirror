import json
import threading
import time

from rabbitmq_amqp_python_client import AMQPMessagingHandler, Event
from shared.pg import get_pg_client

from .env_vars import PG_URL
from .runners.generic import JobHandle
from .runners.local_threaded import LocalThreadJobRunner


class DispatcherHandler(AMQPMessagingHandler):
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

    def on_amqp_message(self, event: Event):
        print("Got message!")
        try:
            if not event.message.body:
                print("Received message with no body")
                self.delivery_context.discard(event)
                return

            data: dict = json.loads(str(event.message.body, "utf-8"))

            # Try to dispatch job
            job_id = data.get("job_id")
            if not job_id:
                print("Received message with no job_id")
                self.delivery_context.discard(event)
                return

            print(f"Dispatching job {job_id}")
            runner = LocalThreadJobRunner(data)
            handle = runner.run()
            print(f"Job {job_id} started")
            self.running_jobs[job_id] = (handle, event)
        except Exception as e:
            print(f"Error processing message: {e}")
            # TODO: Handle error
