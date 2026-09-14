from abc import ABC, abstractmethod
from typing import Any


class RunnerError(Exception):
    pass


class JobHandle(ABC):
    job_data: Any

    @abstractmethod
    def __init__(self, job_data: Any):
        self.job_data = job_data

    @abstractmethod
    def poll(self) -> str:
        return "PENDING"


class JobRunner(ABC):
    job_data: Any

    @abstractmethod
    def __init__(self, job_data):
        self.job_data = job_data

    @abstractmethod
    def run(self) -> JobHandle:
        return JobHandle(self.job_data)
