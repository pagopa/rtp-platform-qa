from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get('/health')
async def health():
    return {'status': 'healthy', 'service': 'gpd-producer'}


@router.get('/ready')
async def ready(request: Request):
    """Readiness reflects ProducerService availability.

    Returns 200 when the producer is initialized, 503 otherwise.
    """
    producer = getattr(request.app.state, 'producer_service', None)
    if producer is None:
        return JSONResponse({'status': 'not-ready'}, status_code=503)
    return {'status': 'ready'}
