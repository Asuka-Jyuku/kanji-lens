import pytest

from fakes import DRAWING, T0
from kanjilens.adapters.outbound.notifier.in_memory_result_notifier import InMemoryResultNotifier
from kanjilens.domain.job import RecognitionJob
from kanjilens.domain.stroke_order import StrokeOrderMode

pytestmark = pytest.mark.anyio

JOB = RecognitionJob.submit(mode=StrokeOrderMode.UNORDERED, drawing=DRAWING, now=T0)
STARTED = JOB.start(T0)


async def test_every_subscriber_gets_each_change_in_order() -> None:
    notifier = InMemoryResultNotifier()

    with notifier.subscribe(JOB.id) as first, notifier.subscribe(JOB.id) as second:
        notifier.notify(STARTED)

        assert await first.next() == STARTED
        assert await second.next() == STARTED


async def test_a_change_with_nobody_watching_is_dropped() -> None:
    notifier = InMemoryResultNotifier()

    notifier.notify(STARTED)

    assert notifier.watcher_count(JOB.id) == 0


async def test_only_the_watched_job_reaches_the_subscriber() -> None:
    notifier = InMemoryResultNotifier()
    other = RecognitionJob.submit(mode=StrokeOrderMode.UNORDERED, drawing=DRAWING, now=T0)

    with notifier.subscribe(JOB.id) as subscription:
        notifier.notify(other.start(T0))
        notifier.notify(STARTED)

        assert await subscription.next() == STARTED


async def test_leaving_the_block_unsubscribes_even_on_error() -> None:
    notifier = InMemoryResultNotifier()

    with notifier.subscribe(JOB.id):
        assert notifier.watcher_count(JOB.id) == 1
    with pytest.raises(RuntimeError), notifier.subscribe(JOB.id):
        raise RuntimeError("client went away")

    assert notifier.watcher_count(JOB.id) == 0
