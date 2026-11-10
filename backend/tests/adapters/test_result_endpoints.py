"""GET /api/recognitions/{id} and its SSE stream, end to end: the app runs its lifespan, so the
inference process (with placeholder or test functions) really processes the jobs."""

import json
import threading
import time
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

import worker_functions
from kanjilens.adapters.outbound.recognizer import placeholder as placeholder_recognizer
from kanjilens.adapters.outbound.stroke_order import placeholder as placeholder_evaluator
from kanjilens.bootstrap.app import InferenceFunctions, create_app

TIMEOUT_SECONDS = 10
PLACEHOLDER = InferenceFunctions(
    recognize=placeholder_recognizer.recognize, evaluate=placeholder_evaluator.evaluate
)
SLOW = InferenceFunctions(
    recognize=worker_functions.recognize_slowly, evaluate=placeholder_evaluator.evaluate
)
CRASHING = InferenceFunctions(
    recognize=worker_functions.recognize_or_crash, evaluate=placeholder_evaluator.evaluate
)

type Event = tuple[str, dict[str, Any]]


def drawing(mode: str = "unordered", strokes: int = 2) -> dict[str, Any]:
    return {
        "stroke_order_mode": mode,
        "canvas": {"width": 320, "height": 320},
        "strokes": [[[40.0, 10.0 * i, 2 * i], [90.0, 10.0 * i, 2 * i + 1]] for i in range(strokes)],
    }


def submit(client: TestClient, body: dict[str, Any]) -> str:
    response = client.post("/api/recognitions", json=body)
    assert response.status_code == 202
    job_id: str = response.json()["job_id"]
    return job_id


def wait_for(
    client: TestClient, job_id: str, done: Callable[[dict[str, Any]], bool]
) -> dict[str, Any]:
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        state: dict[str, Any] = client.get(f"/api/recognitions/{job_id}").json()
        if done(state):
            return state
        time.sleep(0.02)
    raise AssertionError(f"job {job_id} did not get there in {TIMEOUT_SECONDS} s")


def final(state: dict[str, Any]) -> bool:
    return state["status"] in ("completed", "failed")


def read_events(client: TestClient, job_id: str) -> list[Event]:
    """The events until the server ends the stream. Read in a thread with a deadline, so a
    stream that never ends fails the test instead of hanging the run (and the CI)."""
    events: list[Event] = []
    errors: list[BaseException] = []

    def read() -> None:
        try:
            name = ""
            with client.stream("GET", f"/api/recognitions/{job_id}/events") as response:
                assert response.status_code == 200
                assert response.headers["content-type"].startswith("text/event-stream")
                for line in response.iter_lines():
                    if line.startswith("event:"):
                        name = line.removeprefix("event:").strip()
                    elif line.startswith("data:"):
                        events.append((name, json.loads(line.removeprefix("data:"))))
        except BaseException as error:
            errors.append(error)

    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    reader.join(TIMEOUT_SECONDS)
    assert not reader.is_alive(), f"the stream did not end; events so far: {events}"
    if errors:
        raise errors[0]
    return events


@pytest.fixture
def app_with(request: pytest.FixtureRequest) -> Iterator[TestClient]:
    with TestClient(create_app(request.param)) as client:
        yield client


# --- GET, one test per status -----------------------------------------------------------


def test_get_a_queued_job() -> None:
    client = TestClient(create_app())  # no lifespan: nothing takes the job from the queue
    job_id = submit(client, drawing())

    response = client.get(f"/api/recognitions/{job_id}")

    assert response.status_code == 200
    assert response.json() == {
        "job_id": job_id,
        "status": "queued",
        "stroke_order_mode": "unordered",
    }


@pytest.mark.parametrize("app_with", [SLOW], indirect=True)
def test_get_a_processing_job(app_with: TestClient) -> None:
    job_id = submit(app_with, drawing())

    state = wait_for(app_with, job_id, lambda s: s["status"] != "queued")

    assert state == {"job_id": job_id, "status": "processing", "stroke_order_mode": "unordered"}


@pytest.mark.parametrize("app_with", [PLACEHOLDER], indirect=True)
def test_get_a_completed_unordered_job(app_with: TestClient) -> None:
    job_id = submit(app_with, drawing("unordered"))

    state = wait_for(app_with, job_id, final)

    assert state == {
        "job_id": job_id,
        "status": "completed",
        "stroke_order_mode": "unordered",
        "predictions": [
            {"kanji": "日", "confidence": 0.6},
            {"kanji": "目", "confidence": 0.25},
            {"kanji": "白", "confidence": 0.1},
        ],
    }


@pytest.mark.parametrize("app_with", [PLACEHOLDER], indirect=True)
def test_get_a_completed_ordered_job(app_with: TestClient) -> None:
    job_id = submit(app_with, drawing("ordered", strokes=2))

    state = wait_for(app_with, job_id, final)

    assert state["status"] == "completed"
    assert [p["stroke_order"] for p in state["predictions"]] == [
        {
            "status": "evaluated",
            "correct": True,
            "expected_strokes": 2,
            "drawn_strokes": 2,
            "issues": [],
        }
    ] * 3


@pytest.mark.parametrize("app_with", [CRASHING], indirect=True)
def test_get_a_failed_job(app_with: TestClient) -> None:
    job_id = submit(app_with, drawing(strokes=worker_functions.CRASH_STROKES))

    state = wait_for(app_with, job_id, final)

    assert state == {
        "job_id": job_id,
        "status": "failed",
        "stroke_order_mode": "unordered",
        "failure": "inference_failed",
    }


@pytest.mark.parametrize("app_with", [CRASHING], indirect=True)
def test_a_crash_fails_its_job_and_the_next_job_still_completes(app_with: TestClient) -> None:
    crashed = submit(app_with, drawing(strokes=worker_functions.CRASH_STROKES))
    after = submit(app_with, drawing(strokes=1))

    assert wait_for(app_with, crashed, final)["failure"] == "inference_failed"
    assert wait_for(app_with, after, final)["status"] == "completed"


@pytest.mark.parametrize("app_with", [SLOW], indirect=True)
def test_jobs_run_one_at_a_time(app_with: TestClient) -> None:
    # One inference at a time (ADR 0011): while the first job runs, the second one waits.
    first = submit(app_with, drawing())
    second = submit(app_with, drawing("ordered"))

    wait_for(app_with, first, lambda s: s["status"] == "processing")
    assert app_with.get(f"/api/recognitions/{second}").json()["status"] == "queued"

    wait_for(app_with, second, lambda s: s["status"] != "queued")
    assert app_with.get(f"/api/recognitions/{first}").json()["status"] == "completed"
    assert wait_for(app_with, second, final)["status"] == "completed"


@pytest.mark.parametrize("path", ["/api/recognitions/{}", "/api/recognitions/{}/events"])
def test_an_unknown_or_expired_job_is_404_on_both(path: str) -> None:
    response = TestClient(create_app()).get(path.format("0" * 32))

    assert response.status_code == 404
    assert response.json() == {"error": "job_not_found"}


# --- SSE ------------------------------------------------------------------------------------


@pytest.mark.parametrize("app_with", [SLOW], indirect=True)
def test_the_stream_sends_queued_processing_completed_and_ends(app_with: TestClient) -> None:
    # A first slow job holds the worker, so the second one is surely still queued.
    first = submit(app_with, drawing())
    wait_for(app_with, first, lambda s: s["status"] == "processing")
    second = submit(app_with, drawing("ordered"))

    events = read_events(app_with, second)

    assert [name for name, _ in events] == ["queued", "processing", "completed"]
    assert [data["status"] for _, data in events] == ["queued", "processing", "completed"]
    assert events[-1][1] == app_with.get(f"/api/recognitions/{second}").json()


@pytest.mark.parametrize("app_with", [PLACEHOLDER], indirect=True)
def test_a_stream_opened_after_the_end_sends_the_final_state_and_ends(
    app_with: TestClient,
) -> None:
    job_id = submit(app_with, drawing())
    finished = wait_for(app_with, job_id, final)

    events = read_events(app_with, job_id)

    assert events == [("completed", finished)]


@pytest.mark.parametrize("app_with", [CRASHING], indirect=True)
def test_a_failed_job_ends_the_stream_with_its_failure(app_with: TestClient) -> None:
    job_id = submit(app_with, drawing(strokes=worker_functions.CRASH_STROKES))
    wait_for(app_with, job_id, final)

    events = read_events(app_with, job_id)

    assert [(name, data.get("failure")) for name, data in events] == [
        ("failed", "inference_failed")
    ]
