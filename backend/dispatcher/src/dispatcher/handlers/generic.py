import asyncio
import json
from dataclasses import dataclass

from aio_pika.abc import AbstractIncomingMessage

from ..runners.generic import JobHandle, JobRunner


class HandlerError(Exception):
    pass


_SETTLE_ATTEMPT_LIMIT = 10


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
        self._settle_attempts: dict[str, int] = {}
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
        # otherwise spam an identical UPDATE each tick. Recorded after the
        # write lands so a DB failure retries next tick.
        if self.last_statuses.get(job_id) != poll_result:
            await asyncio.to_thread(
                self.update_db_status, job_id, poll_result
            )
            self.last_statuses[job_id] = poll_result

        match poll_result:
            case "COMPLETED":
                print(f"Job {job_id} completed")
                await self._settle(job_id, message, accept=True)
            case "FAILED":
                print(f"Job {job_id} failed")
                await self._settle(job_id, message, accept=False)

    async def _settle(
        self, job_id: str, message: AbstractIncomingMessage, *, accept: bool
    ):
        # Settle before untracking: a failed ack/nack leaves the job in
        # running_jobs so the next tick retries.
        try:
            if accept:
                await message.ack()
            else:
                await message.nack(requeue=False)
        except Exception:
            self._settle_attempts[job_id] = self._settle_attempts.get(job_id, 0) + 1
            # A delivery on a dead channel can never settle — the broker
            # already requeued it, so stop retrying after a few ticks.
            if self._settle_attempts[job_id] >= _SETTLE_ATTEMPT_LIMIT:
                print(f"Giving up settling job {job_id}")
                self._drop_job(job_id)
                return
            raise
        self._drop_job(job_id)

    def _drop_job(self, job_id: str):
        self.running_jobs.pop(job_id, None)
        self.last_statuses.pop(job_id, None)
        self._settle_attempts.pop(job_id, None)

    def parse_event(self, message: AbstractIncomingMessage) -> dict:
        if not message.body:
            raise HandlerError("Could not find `body` in `message`")

        return json.loads(message.body)

    async def dispatch_job(self, params: DispatchJobParams):
        if params.job_id in self.running_jobs:
            # Redelivery of an in-flight job — the tracked copy settles it.
            await params.message.ack()
            return
        handle = params.runner.run()
        self.running_jobs[params.job_id] = (handle, params.message)
