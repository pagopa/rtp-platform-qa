import logging
from typing import Optional

from core.config import settings
from core.utils import sanitize_log_value
from fastapi import APIRouter
from fastapi import File
from fastapi import HTTPException
from fastapi import Query
from fastapi import Request
from fastapi import UploadFile
from models.dto import FileSendResult
from models.dto import SendStatus
from services.ingestion import send_file as ingestion_send_file
from services.ingestion import send_message as ingestion_send_message
from services.producer import ProducerService

router = APIRouter()

logger = logging.getLogger('gpd-producer')
EVENTHUB_TOPIC = settings.eventhub_topic
if not EVENTHUB_TOPIC:
    raise RuntimeError("EVENTHUB_TOPIC is not configured. Please set 'eventhub_topic' in your settings or the EVENTHUB_TOPIC env var.")


def require_producer_service(request: Request, *, missing_status: int = 503) -> ProducerService:
    svc: Optional[ProducerService] = getattr(request.app.state, 'producer_service', None)
    if svc is None:
        raise HTTPException(status_code=missing_status, detail={'status': 'error', 'message': 'Producer service is not available'})
    return svc


@router.post('/send/gpd/message', response_model=SendStatus)
async def send_msg(request: Request, validate: bool = Query(default=True)) -> SendStatus:
    payload = await request.json()
    logger.info(
        'Received message - id: %s, operation: %s, iuv: %s, status: %s',
        sanitize_log_value(payload.get('id')),
        sanitize_log_value(payload.get('operation')),
        sanitize_log_value(payload.get('iuv')),
        sanitize_log_value(payload.get('status')),
    )

    producer_service = require_producer_service(request, missing_status=500)
    return await ingestion_send_message(producer_service, EVENTHUB_TOPIC, payload, validate)


@router.post('/send/gpd/file', response_model=FileSendResult)
async def send_file(
    request: Request,
    file: UploadFile = File(..., description='NDJSON file: one RTPMessage JSON per line'),
    bulk: bool = Query(default=False, description='If true, rate applies but no in-flight cap'),
    rate: int = Query(default=settings.default_rate_limit, ge=1, le=200, description='Messages per second'),
) -> FileSendResult:
    producer_service = require_producer_service(request)
    return await ingestion_send_file(producer_service, EVENTHUB_TOPIC, file, rate, bulk)
