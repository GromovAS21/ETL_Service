from abc import ABC, abstractmethod
from datetime import datetime


class State(ABC):
    @abstractmethod
    async def get_state(self, job_name: str) -> datetime | None: ...

    @abstractmethod
    async def set_state(self, job_name: str, last_run: datetime) -> None: ...
