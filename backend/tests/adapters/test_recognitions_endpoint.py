from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from kanjilens.adapters.inbound.http.body_limit import MAX_BODY_BYTES
from kanjilens.adapters.inbound.http.errors import RETRY_AFTER_SECONDS
from kanjilens.bootstrap.app import create_app

URL = "/api/recognitions"


def body(**changes: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "stroke_order_mode": "unordered",
        "canvas": {"width": 320, "height": 320},
        "strokes": [
            [[41.0, 30.5, 0], [41.2, 88.0, 140]],
            [[44.1, 31.0, 410], [118.3, 29.4, 590], [117.9, 92.2, 780]],
        ],
    }
    payload.update(changes)
    return payload


def strokes(count: int, points: int) -> list[list[list[float]]]:
    return [[[10.0, 10.0, i * points + j] for j in range(points)] for i in range(count)]


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as test_client:
        yield test_client


def test_a_valid_drawing_is_accepted_and_queued(client: TestClient) -> None:
    response = client.post(URL, json=body(stroke_order_mode="ordered"))

    assert response.status_code == 202
    assert response.json()["status"] == "queued"
    assert len(response.json()["job_id"]) == 32


def test_each_submission_gets_its_own_job(client: TestClient) -> None:
    first = client.post(URL, json=body()).json()["job_id"]
    second = client.post(URL, json=body()).json()["job_id"]

    assert first != second


# --- 400 ---------------------------------------------------------------------------------


@pytest.mark.parametrize("mode", ["sometimes", "", None, 1])
def test_an_unknown_mode_is_400(client: TestClient, mode: object) -> None:
    response = client.post(URL, json=body(stroke_order_mode=mode))

    assert response.status_code == 400
    assert response.json() == {"error": "invalid_stroke_order_mode"}


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"strokes": []}, id="no strokes (domain)"),
        pytest.param({"strokes": [[[400.0, 10.0, 0]]]}, id="outside the canvas (domain)"),
        pytest.param({"strokes": [[[10.0, 10.0, 5], [10.0, 10.0, 1]]]}, id="time back (domain)"),
        pytest.param({"canvas": {"width": 10, "height": 320}}, id="tiny canvas (domain)"),
        pytest.param({"strokes": [[[10.0, 10.0]]]}, id="point without t (schema)"),
        pytest.param({"strokes": [[[10.0, 10.0, 1.5]]]}, id="fractional t (schema)"),
        pytest.param({"strokes": [[["10", 10.0, 0]]]}, id="coordinate as text (schema)"),
        pytest.param({"canvas": {"width": 320}}, id="canvas without height (schema)"),
    ],
)
def test_an_invalid_drawing_is_400(client: TestClient, changes: dict[str, Any]) -> None:
    response = client.post(URL, json=body(**changes))

    assert response.status_code == 400
    assert response.json() == {"error": "invalid_drawing"}


def test_unknown_fields_are_refused(client: TestClient) -> None:
    response = client.post(URL, json=body(colour="red"))

    assert response.status_code == 400
    assert response.json() == {"error": "invalid_request"}


def test_a_body_that_is_not_json_is_400(client: TestClient) -> None:
    response = client.post(URL, content=b"{not json", headers={"content-type": "application/json"})

    assert response.status_code == 400
    assert "error" in response.json()


# --- 413 ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("count", "points"),
    [
        pytest.param(41, 1, id="41 strokes (schema)"),
        pytest.param(1, 1_001, id="1001 points in a stroke (schema)"),
        pytest.param(11, 1_000, id="11000 points in total (domain)"),
    ],
)
def test_a_drawing_over_the_limits_is_413(client: TestClient, count: int, points: int) -> None:
    response = client.post(URL, json=body(strokes=strokes(count, points)))

    assert response.status_code == 413
    assert response.json() == {"error": "drawing_too_large"}


def test_a_body_over_1_mib_is_413_before_parsing(client: TestClient) -> None:
    response = client.post(
        URL, content=b" " * (MAX_BODY_BYTES + 1), headers={"content-type": "application/json"}
    )

    assert response.status_code == 413
    assert response.json() == {"error": "drawing_too_large"}


def test_a_chunked_body_over_1_mib_is_413_too(client: TestClient) -> None:
    def chunks() -> Iterator[bytes]:
        for _ in range(MAX_BODY_BYTES // 65_536 + 2):
            yield b" " * 65_536

    response = client.post(URL, content=chunks(), headers={"content-type": "application/json"})

    assert response.status_code == 413
    assert response.json() == {"error": "drawing_too_large"}


# --- 503 ---------------------------------------------------------------------------------


def test_the_17th_job_waiting_is_refused_with_retry_after(client: TestClient) -> None:
    # No consumer yet (#46), so nothing leaves the queue.
    for _ in range(16):
        assert client.post(URL, json=body()).status_code == 202

    response = client.post(URL, json=body())

    assert response.status_code == 503
    assert response.json() == {"error": "queue_full"}
    assert response.headers["retry-after"] == str(RETRY_AFTER_SECONDS)


# --- other errors keep the same shape ----------------------------------------------------


def test_an_unknown_route_answers_with_a_code(client: TestClient) -> None:
    response = client.get("/api/nothing-here")

    assert response.status_code == 404
    assert response.json() == {"error": "not_found"}
