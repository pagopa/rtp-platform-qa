import logging
from time import monotonic
from typing import Callable

from fastapi import Request

logger = logging.getLogger("gpd-producer")


async def access_log_middleware(request: Request, call_next: Callable):
    start = monotonic()
    response = await call_next(request)
    elapsed_ms = (monotonic() - start) * 1000
    logger.info(
        "HTTP %s %s -> %s in %.1fms",
        request.method,
        request.url.path,
        getattr(response, "status_code", "-"),
        elapsed_ms,
    )
    return response
