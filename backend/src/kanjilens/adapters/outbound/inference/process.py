"""The inference process (ADRs 0011 and 0019): one spawned worker, apart from the event loop.

The worker runs the initializer once (from #48 on, it loads the model and the KanjiVG
references) and then one call at a time. Calls cross by pickle: the function must be importable
by name (module level) and its arguments and result plain data (wire.py).
"""

import asyncio
import logging
import multiprocessing
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool

_log = logging.getLogger(__name__)


class InferenceProcess:
    def __init__(self, initializer: Callable[[], None] | None = None) -> None:
        self._initializer = initializer
        self._pool: ProcessPoolExecutor | None = None

    async def start(self) -> None:
        """Start the worker and run the initializer now, not on the first job.

        Raises BrokenProcessPool when the initializer fails, so the app does not start.
        """
        self._pool = self._new_pool()
        try:
            await self.run(_ready)
        except BaseException:
            self.stop()  # the replacement pool that run() created would be left behind
            raise

    async def run[*Ts, R](self, function: Callable[[*Ts], R], *args: *Ts) -> R:
        """Run function(*args) in the worker. When the worker dies, raises BrokenProcessPool
        and starts a new one (which runs the initializer again) for the next call."""
        if self._pool is None:
            raise RuntimeError("the inference process has not started")
        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(self._pool, function, *args)
        except BrokenProcessPool:
            _log.error("the inference process died; starting a new one")
            broken, self._pool = self._pool, self._new_pool()
            broken.shutdown(wait=False, cancel_futures=True)
            raise

    def stop(self) -> None:
        """Stop the worker without waiting for the call in progress: its job is lost, like
        every in-memory job when the API stops (ADR 0019)."""
        if self._pool is not None:
            self._pool.terminate_workers()
            self._pool = None

    def _new_pool(self) -> ProcessPoolExecutor:
        # spawn on every platform: the Windows default, so Linux (forkserver by default since
        # Python 3.14) behaves like the school notebook.
        return ProcessPoolExecutor(
            max_workers=1,
            mp_context=multiprocessing.get_context("spawn"),
            initializer=self._initializer,
        )


def _ready() -> None:
    """Runs in the worker: returning proves it started and the initializer worked."""
