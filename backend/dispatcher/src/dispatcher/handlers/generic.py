import asyncio
import json
from dataclasses import dataclass

from aio_pika.abc import AbstractIncomingMessage

from ..runners.generic import JobHandle, JobRunner


class HandlerError(Exception):
    pass


@dataclass
class DispatchJobParams:
    job_id: str
    runner: JobRunner
    message: AbstractIncomingMessage


class GenericHandlerWithCleanup:
    running_jobs: dict[str, tuple[JobHandle, AbstractIncomingMessage]]
    last_statuses: dict[str, str]

    def __init__(self):
        self.running_jobs = {}
        self.last_statuses = {}
        self._cleanup_task: asyncio.Task | None = None

    def update_db_status(self, job_id: str, status: str):
        pass

    def _ensure_cleanup_task(self):
        # Started lazily from on_message so there is always a running loop —
        # and so instantiating a handler off-loop (tests) stays safe.
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(
                self._cleanup_finished_jobs()
            )

    async def _cleanup_finished_jobs(self):
        while True:
            await asyncio.sleep(1)
            for job_id, (handle, message) in list(self.running_jobs.items()):
                try:
                    await self._reap_job(job_id, handle, message)
                except Exception as e:
                    print(f"Error reaping job {job_id}: {e}")

    async def _reap_job(
        self, job_id: str, handle: JobHandle, message: AbstractIncomingMessage
    ):
        poll_result = handle.poll()
        # Write only on status change — polling every second would
        # otherwise spam an identical UPDATE each tick.
        if self.last_statuses.get(job_id) != poll_result:
            self.last_statuses[job_id] = poll_result
            await asyncio.to_thread(
                self.update_db_status, job_id, poll_result
            )

        match poll_result:
            case "COMPLETED":
                del self.running_jobs[job_id]
                del self.last_statuses[job_id]
                print(f"Job {job_id} completed")
                await message.ack()
            case "FAILED":
                del self.running_jobs[job_id]
                del self.last_statuses[job_id]
                print(f"Job {job_id} failed")
                await message.nack(requeue=False)

    def parse_event(self, message: AbstractIncomingMessage) -> dict:
        if not message.body:
            raise HandlerError("Could not find `body` in `message`")

        return json.loads(message.body)

    def dispatch_job(self, params: DispatchJobParams):
        handle = params.runner.run()
        self.running_jobs[params.job_id] = (handle, params.message)
