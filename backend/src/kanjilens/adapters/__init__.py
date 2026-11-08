"""Framework code.

Inbound adapters (HTTP, SSE, queue consumer) call the use cases; outbound adapters
(recognizer, stroke-order checker, queue, job store, notifier) implement the ports.
"""
