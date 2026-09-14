import queue
import threading
from abc import abstractmethod
from typing import Any

from .generic import JobHandle, JobRunner


class LocalThreadedJobHandle(JobHandle):
    thread: threading.Thread
    queue: queue.Queue

    def __init__(self, job_data: Any, thread: threading.Thread, queue: queue.Queue):
        super().__init__(job_data)
        self.thread = thread
        self.queue = queue

    def poll(self) -> str:
        # See if exception was thrown, return FAILED
        try:
            _, e = self.queue.get_nowait()
            print(f"Exception was thrown from job with data {self.job_data}: {e}")
        except queue.Empty:
            pass
        else:
            return "FAILED"

        if self.thread.is_alive():
            return "PROCESSING"
        else:
            return "COMPLETED"


class LocalThreadJobRunner(JobRunner):
    def __init__(self, job_data: Any):
        super().__init__(job_data)

    def run(self) -> JobHandle:
        q = queue.Queue()
        t = threading.Thread(target=self.task, args=(q,))
        t.start()
        return LocalThreadedJobHandle(self.job_data, t, q)

    @abstractmethod
    def task(self, queue: queue.Queue):
        pass
