"""POST /api/recognitions receives a drawing and queues its job (ADRs 0016 and 0019);
GET /api/recognitions/{id} answers the job's current state, the polling fallback (ADR 0020)."""

from typing import Annotated

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt

from kanjilens.adapters.inbound.http.recognition_state import RecognitionStateResponse
from kanjilens.application.use_cases.get_recognition import GetRecognition
from kanjilens.application.use_cases.submit_recognition import SubmitRecognition
from kanjilens.domain.drawing import DRAWING_LIMITS, CanvasSize, Drawing, Point, Stroke
from kanjilens.domain.job import JobStatus
from kanjilens.domain.stroke_order import StrokeOrderMode

# [x, y, t]: CSS pixels from the canvas top-left corner, and ms since the first point.
# Strict numbers: "10" or true is not a coordinate, and t is a whole number. FastAPI validates
# the parsed JSON in Python mode, so the model itself stays lax (lists for tuples, text for enums).
type PointRequest = tuple[StrictFloat, StrictFloat, StrictInt]
type StrokeRequest = Annotated[
    list[PointRequest], Field(max_length=DRAWING_LIMITS.max_points_per_stroke)
]


class CanvasRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    width: StrictFloat
    height: StrictFloat


class RecognitionRequest(BaseModel):
    """The drawing as the canvas sends it. The schema caps the list sizes; the domain checks
    the rest (total points, canvas size, coordinates, time) when the Drawing is built."""

    model_config = ConfigDict(extra="forbid")

    stroke_order_mode: StrokeOrderMode
    canvas: CanvasRequest
    strokes: Annotated[list[StrokeRequest], Field(max_length=DRAWING_LIMITS.max_strokes)]

    def to_drawing(self) -> Drawing:
        return Drawing(
            CanvasSize(self.canvas.width, self.canvas.height),
            tuple(Stroke(tuple(Point(x, y, t) for x, y, t in stroke)) for stroke in self.strokes),
        )


class SubmitRecognitionResponse(BaseModel):
    job_id: str
    status: JobStatus


class ErrorResponse(BaseModel):
    error: str


def recognitions_router(
    submit_recognition: SubmitRecognition, get_recognition: GetRecognition
) -> APIRouter:
    router = APIRouter()

    @router.post(
        "/api/recognitions",
        status_code=status.HTTP_202_ACCEPTED,
        responses={
            400: {
                "model": ErrorResponse,
                "description": "invalid_drawing, invalid_stroke_order_mode",
            },
            413: {"model": ErrorResponse, "description": "drawing_too_large"},
            503: {"model": ErrorResponse, "description": "queue_full, with Retry-After"},
        },
    )
    async def submit(request: RecognitionRequest) -> SubmitRecognitionResponse:
        job = submit_recognition.execute(request.stroke_order_mode, request.to_drawing())
        return SubmitRecognitionResponse(job_id=job.id, status=job.status)

    @router.get(
        "/api/recognitions/{job_id}",
        response_model_exclude_none=True,
        responses={404: {"model": ErrorResponse, "description": "job_not_found"}},
    )
    async def get(job_id: str) -> RecognitionStateResponse:
        return RecognitionStateResponse.from_job(get_recognition.execute(job_id))

    return router
