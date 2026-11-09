"""Job changes handed to the open SSE streams, in the memory of the API process (ADR 0020).

Each stream subscribes to one job and gets its own small queue, so a notification never waits
for a slow client. Subscribing before reading the job's current state means no change can fall
between the read and the wait. Everything runs on the API's event loop: no locks needed.
"""

import asyncio
from collections.abc import Iterator
from contextlib import contextmanager

from kanjilens.domain.job import RecognitionJob


class JobSubscription:
    def __init__(self, queue: asyncio.Queue[RecognitionJob]) -> None:
        self._queue = queue

    async def next(self) -> RecognitionJob:
        """The job's next state, waiting until it changes."""
        return await self._queue.get()


class InMemoryResultNotifier:
    def __init__(self) -> None:
        self._watchers: dict[str, set[asyncio.Queue[RecognitionJob]]] = {}

    def notify(self, job: RecognitionJob) -> None:
        for queue in self._watchers.get(job.id, ()):
            # Unbounded on purpose: a job changes at most twice after it is queued.
            queue.put_nowait(job)

    @contextmanager
    def subscribe(self, job_id: str) -> Iterator[JobSubscription]:
        """Watch the job until the block ends; leaving it (also by a disconnect) unsubscribes."""
        queue: asyncio.Queue[RecognitionJob] = asyncio.Queue()
        self._watchers.setdefault(job_id, set()).add(queue)
        try:
            yield JobSubscription(queue)
        finally:
            watchers = self._watchers[job_id]
            watchers.discard(queue)
            if not watchers:
                del self._watchers[job_id]

    def watcher_count(self, job_id: str) -> int:
        return len(self._watchers.get(job_id, ()))
