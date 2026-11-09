"""Domain errors, each with a stable code that the inbound adapters turn into a response.

The code is part of the API contract: the frontend translates it into text (ADR 0009),
so the message here is for logs only.
"""

from typing import ClassVar


class DomainError(Exception):
    code: ClassVar[str] = "domain_error"


class InvalidDrawing(DomainError):
    """The drawing breaks a format rule (HTTP 400)."""

    code = "invalid_drawing"


class DrawingTooLarge(DomainError):
    """The drawing has more strokes or points than the limits allow (HTTP 413)."""

    code = "drawing_too_large"


class InvalidPrediction(DomainError):
    """A recognition result breaks a rule; raised for recognizer bugs, never for user input."""

    code = "invalid_prediction"


class InvalidStrokeOrderEvaluation(DomainError):
    """A stroke-order evaluation breaks a rule; raised for evaluator bugs."""

    code = "invalid_stroke_order_evaluation"


class InvalidJobTransition(DomainError):
    """A job was asked to move to a status its current status does not allow."""

    code = "invalid_job_transition"


class QueueFull(DomainError):
    """The job queue is at its limit; the client should retry later (HTTP 503)."""

    code = "queue_full"
