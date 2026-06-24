from __future__ import annotations

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)


class TraceMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        trace_id = request.headers.get("X-Trace-ID", f"trace-{int(time.time() * 1000)}")
        start = time.time()

        request.state.trace_id = trace_id

        response = await call_next(request)

        duration_ms = (time.time() - start) * 1000
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Duration-Ms"] = f"{duration_ms:.2f}"

        logger.info(
            f"[{trace_id}] {request.method} {request.url.path} "
            f"-> {response.status_code} ({duration_ms:.1f}ms)"
        )

        return response
