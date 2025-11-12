import uuid
from typing import Callable

from fastapi import Request

REQUEST_ID_HEADER = 'x-request-id'


async def request_id_middleware(request: Request, call_next: Callable):
    """Attach a request id to each request/response for correlation."""
    req_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
    request.scope['request_id'] = req_id
    response = await call_next(request)
    response.headers[REQUEST_ID_HEADER] = req_id
    return response
