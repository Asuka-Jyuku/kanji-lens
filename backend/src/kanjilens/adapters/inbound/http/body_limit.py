"""Cap the request body before anything parses it (CLAUDE.md, "Segurança").

The schema and the domain cap strokes and points, but only after the JSON is parsed; this caps
the bytes, so an oversized body never reaches memory. Pure ASGI, so it also counts a chunked
body, which has no Content-Length.
"""

from http import HTTPStatus

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from kanjilens.adapters.inbound.http.errors import ApiError, error_response
from kanjilens.domain.errors import DrawingTooLarge

# 10,000 points (ADR 0016) at up to ~60 bytes each as JSON, with room to spare.
MAX_BODY_BYTES = 1024 * 1024


class BodySizeLimitMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int = MAX_BODY_BYTES) -> None:
        self._app = app
        self._max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        if self._declared_length(scope) > self._max_bytes:
            response = error_response(HTTPStatus.CONTENT_TOO_LARGE, DrawingTooLarge.code)
            await response(scope, receive, send)
            return

        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self._max_bytes:
                    # Raised while FastAPI reads the body, so it turns into this error answer.
                    raise ApiError(HTTPStatus.CONTENT_TOO_LARGE, DrawingTooLarge.code)
            return message

        await self._app(scope, limited_receive, send)

    @staticmethod
    def _declared_length(scope: Scope) -> int:
        for name, value in scope["headers"]:
            if name == b"content-length":
                try:
                    return int(value)
                except ValueError:
                    return 0
        return 0
