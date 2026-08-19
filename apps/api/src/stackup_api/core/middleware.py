"""HTTP middleware: assign/propagate a request_id for every request."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import Response

from stackup_api.core.context import set_request_id

REQUEST_ID_HEADER = "X-Request-Id"


async def request_id_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    incoming = request.headers.get(REQUEST_ID_HEADER)
    request_id = incoming or uuid.uuid4().hex
    set_request_id(request_id)
    try:
        response = await call_next(request)
    finally:
        set_request_id(None)
    response.headers[REQUEST_ID_HEADER] = request_id
    return response
