import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("gpd-producer")


def unhandled_exception_handler(request: Request, exc: Exception):
    """Global fallback error handler used by FastAPI."""
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal Server Error",
            "requestId": request.scope.get("request_id"),
        },
    )


def add_exception_handlers(app: FastAPI) -> None:
    """Register the global exception handler explicitly.

    Defining the handler at module level and registering it with
    app.add_exception_handler avoids IDE/linters flagging it as unused.
    """
    app.add_exception_handler(Exception, unhandled_exception_handler)
