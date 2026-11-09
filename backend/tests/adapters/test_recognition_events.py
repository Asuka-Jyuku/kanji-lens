"""The SSE event sequence of a job, driven by hand (no HTTP, no inference process)."""

import asyncio
from datetime import timedelta

import pytest
from fastapi.sse import ServerSentEvent

from fakes import DRAWING, RESULT, T0, FakeJobRepository
from kanjilens.adapters.inbound.http.recognition_events import job_events
from kanjilens.adapters.outbound.notifier.in_memory_result_notifier import InMemoryResultNotifier
from kanjilens.application.use_cases.get_recognition import GetRecognition
from kanjilens.domain.job import RecognitionJob
from kanjilens.domain.stroke_order import StrokeOrderMode

pytestmark = pytest.mark.anyio

T1 = T0 + timedelta(seconds=1)


class Setup:
    def __init__(self) -> None:
        self.repository = FakeJobRepository()
        self.notifier = InMemoryResultNotifier()
        self.job = RecognitionJob.submit(mode=StrokeOrderMode.UNORDERED, drawing=DRAWING, now=T0)
        self.repository.save(self.job)

    def change(self, job: RecognitionJob) -> None:
        # What ProcessRecognition does: store, then notify.
        self.repository.save(job)
        self.notifier.notify(job)

    def events(self) -> asyncio.Task[list[ServerSentEvent]]:
        async def collect() -> list[ServerSentEvent]:
            stream = job_events(self.job.id, GetRecognition(self.repository), self.notifier)
            return [event async for event in stream]

        return asyncio.ensure_future(collect())


async def settle() -> None:
    for _ in range(5):
        await asyncio.sleep(0)


async def test_one_event_per_state_until_the_final_one() -> None:
    setup = Setup()
    events = setup.events()
    await settle()

    started = setup.job.start(T0)
    setup.change(started)
    await settle()
    setup.change(started.complete(RESULT, T1))

    received = await asyncio.wait_for(events, 5)
    assert [e.event for e in received] == ["queued", "processing", "completed"]
    assert received[-1].data["predictions"][0]["kanji"] == "日"
    assert setup.notifier.watcher_count(setup.job.id) == 0


async def test_a_finished_job_sends_its_final_state_and_ends() -> None:
    setup = Setup()
    setup.change(setup.job.start(T0).complete(RESULT, T1))

    received = await asyncio.wait_for(setup.events(), 5)

    assert [e.event for e in received] == ["completed"]


async def test_a_change_already_read_is_not_sent_twice() -> None:
    # The change lands between subscribing and the first read: it is read, and also queued.
    setup = Setup()
    started = setup.job.start(T0)
    stream = job_events(setup.job.id, GetRecognition(setup.repository), setup.notifier)
    setup.repository.on_get = lambda _job_id: setup.change(started)

    first = await anext(stream)
    setup.change(started.complete(RESULT, T1))
    rest = [event async for event in stream]

    assert [e.event for e in [first, *rest]] == ["processing", "completed"]


async def test_a_client_that_leaves_unsubscribes() -> None:
    setup = Setup()
    stream = job_events(setup.job.id, GetRecognition(setup.repository), setup.notifier)
    await anext(stream)
    assert setup.notifier.watcher_count(setup.job.id) == 1

    await stream.aclose()  # what Starlette does when the client disconnects

    assert setup.notifier.watcher_count(setup.job.id) == 0
