"""Structured JSON logging via structlog.

Every log line carries the current request_id (when inside a request) so a
single request can be traced across API and worker logs and correlated with
Sentry events (ADR-008).
"""

from __future__ import annotations

import logging

import structlog
from structlog.typing import EventDict, WrappedLogger

from stackup_api.core.context import get_request_id


def _add_request_id(
    _logger: WrappedLogger, _method: str, event_dict: EventDict
) -> EventDict:
    request_id = get_request_id()
    if request_id is not None:
        event_dict["request_id"] = request_id
    return event_dict


def configure_logging(*, debug: bool) -> None:
    logging.basicConfig(
        format="%(message)s",
        level=logging.DEBUG if debug else logging.INFO,
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _add_request_id,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if debug else logging.INFO
        ),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)  # type: ignore[no-any-return]
