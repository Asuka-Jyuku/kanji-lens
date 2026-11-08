"""The bounded in-memory queue of the API process (ADR 0019)."""

import asyncio

from kanjilens.domain.errors import QueueFull

# Initial value from ADR 0019, to revisit with the real inference time.
QUEUE_SIZE = 16


class AsyncioJobQueue:
    def __init__(self, maxsize: int = QUEUE_SIZE) -> None:
        self._queue: asyncio.Queue[str] = asyncio.Queue(maxsize=maxsize)

    def enqueue(self, job_id: str) -> None:
        try:
            self._queue.put_nowait(job_id)
        except asyncio.QueueFull:
            raise QueueFull(f"the queue holds {self._queue.maxsize} jobs") from None

    def __len__(self) -> int:
        return self._queue.qsize()
