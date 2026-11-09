"""GET /api/recognitions/{id}/events: the job's state changes over SSE (ADR 0020).

One event per state, named after it (event: queued | processing | completed | failed), with
the full state as data, in the GET format; the stream ends at the final state. Each event is
complete, so whoever reconnects gets the current state, with no Last-Event-ID. FastAPI's
EventSourceResponse also sends a keep-alive comment every 15 s.
"""

from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import AbstractContextManager
from typing import Annotated, Protocol

from fastapi import APIRouter, Depends
from fastapi.sse import EventSourceResponse, ServerSentEvent

from kanjilens.adapters.inbound.http.recognition_state import RecognitionStateResponse
from kanjilens.adapters.inbound.http.recognitions import ErrorResponse
from kanjilens.application.use_cases.get_recognition import GetRecognition
from kanjilens.domain.errors import JobNotFound
from kanjilens.domain.job import RecognitionJob


class JobSubscription(Protocol):
    async def next(self) -> RecognitionJob:
        """The job's next state, waiting until it changes."""
        ...


class JobUpdates(Protocol):
    """The stream's side of the ResultNotifier; the use cases only notify."""

    def subscribe(self, job_id: str) -> AbstractContextManager[JobSubscription]:
        """Watch the job until the block ends."""
        ...


async def job_events(
    job_id: str, get_recognition: GetRecognition, updates: JobUpdates
) -> AsyncGenerator[ServerSentEvent]:
    """The current state, then each new one, until the final state.

    Subscribed before the first read, so no change falls between the read and the wait. When
    the client disconnects, the generator is closed and the subscription with it.
    """
    with updates.subscribe(job_id) as subscription:
        try:
            job = get_recognition.execute(job_id)
        except JobNotFound:
            return  # expired between the 404 check and now: nothing left to tell
        yield _event(job)
        while not job.status.is_final:
            previous = job.status
            job = await subscription.next()
            # A change made before the first read is also in the queue: skip the repeat.
            if job.status is not previous:
                yield _event(job)


def recognition_events_router(get_recognition: GetRecognition, updates: JobUpdates) -> APIRouter:
    router = APIRouter()

    def existing_job_id(job_id: str) -> str:
        # Checked before the stream starts, so a missing job is a real 404, not an empty stream.
        get_recognition.execute(job_id)
        return job_id

    @router.get(
        "/api/recognitions/{job_id}/events",
        response_class=EventSourceResponse,
        responses={404: {"model": ErrorResponse, "description": "job_not_found"}},
    )
    async def events(
        job_id: Annotated[str, Depends(existing_job_id)],
    ) -> AsyncIterator[ServerSentEvent]:
        async for event in job_events(job_id, get_recognition, updates):
            yield event

    return router


def _event(job: RecognitionJob) -> ServerSentEvent:
    return ServerSentEvent(
        event=job.status.value, data=RecognitionStateResponse.from_job(job).to_json()
    )
