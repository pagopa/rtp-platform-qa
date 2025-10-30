from fastapi import APIRouter

router = APIRouter()


@router.get('/health')
async def health():
    return {'status': 'healthy', 'service': 'gpd-producer'}


@router.get('/ready')
async def ready():
    return {'status': 'ready'}
