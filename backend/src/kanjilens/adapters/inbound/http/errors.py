"""Every error answer carries a stable code, {"error": "<code>"}, for the frontend to translate.

Domain errors map to a status here, and so do request validation errors, which FastAPI would
otherwise answer with 422 and Pydantic details (ADR 0009; CLAUDE.md, "Idioma").
"""

from collections.abc import Mapping, Sequence
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from kanjilens.domain.errors import (
    DomainError,
    DrawingTooLarge,
    InvalidDrawing,
    JobNotFound,
    QueueFull,
)

# Seconds a client waits before resending when the queue is full; about a full queue of 16 jobs
# at the prototype's 0.3 s each (ADR 0019). Revisit with the real inference time.
RETRY_AFTER_SECONDS = 5

INVALID_REQUEST = "invalid_request"
INVALID_STROKE_ORDER_MODE = "invalid_stroke_order_mode"

_DOMAIN_STATUS: dict[type[DomainError], int] = {
    InvalidDrawing: HTTPStatus.BAD_REQUEST,
    DrawingTooLarge: HTTPStatus.CONTENT_TOO_LARGE,
    JobNotFound: HTTPStatus.NOT_FOUND,
    QueueFull: HTTPStatus.SERVICE_UNAVAILABLE,
}


class ApiError(HTTPException):
    """An HTTP error raised outside the domain (e.g. by a middleware), with its stable code."""

    def __init__(self, status_code: int, code: str) -> None:
        super().__init__(status_code=status_code, detail=code)
        self.code = code


def error_response(
    status_code: int, code: str, headers: Mapping[str, str] | None = None
) -> JSONResponse:
    return JSONResponse({"error": code}, status_code=status_code, headers=headers)


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _domain_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(HTTPException, _http_error)


async def _domain_error(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)
    # A domain error with no status here is a bug (e.g. an invalid recognizer result).
    status = _DOMAIN_STATUS.get(type(exc), HTTPStatus.INTERNAL_SERVER_ERROR)
    headers = {"Retry-After": str(RETRY_AFTER_SECONDS)} if isinstance(exc, QueueFull) else None
    return error_response(status, exc.code, headers)


async def _validation_error(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    status, code = _classify(exc.errors())
    return error_response(status, code)


async def _http_error(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, HTTPException)
    code = exc.code if isinstance(exc, ApiError) else _code_from_status(exc.status_code)
    return error_response(exc.status_code, code, exc.headers)


def _classify(errors: Sequence[Any]) -> tuple[int, str]:
    locations = [(error["type"], tuple(error["loc"])) for error in errors]
    # A list over its limit in the schema is the same case as the domain's size limits.
    if any(kind == "too_long" and loc[:2] == ("body", "strokes") for kind, loc in locations):
        return HTTPStatus.CONTENT_TOO_LARGE, DrawingTooLarge.code
    if any(loc[:2] == ("body", "stroke_order_mode") for _, loc in locations):
        return HTTPStatus.BAD_REQUEST, INVALID_STROKE_ORDER_MODE
    if any(loc[:2] in (("body", "strokes"), ("body", "canvas")) for _, loc in locations):
        return HTTPStatus.BAD_REQUEST, InvalidDrawing.code
    return HTTPStatus.BAD_REQUEST, INVALID_REQUEST


def _code_from_status(status_code: int) -> str:
    # "Not Found" -> "not_found": still a code, never free text.
    return HTTPStatus(status_code).phrase.lower().replace(" ", "_").replace("-", "_")
