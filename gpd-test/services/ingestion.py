from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from core.rate_limit import TokenBucketLimiter
from core.utils import iter_file_lines
from fastapi import HTTPException
from fastapi import UploadFile
from models.dto import FileError
from models.dto import FileSendResult
from models.dto import RTPMessage
from models.dto import SendStatus
from services.producer import ProducerService

logger = logging.getLogger('gpd-producer')


async def send_message(
    producer_service: ProducerService,
    topic: str,
    payload: dict[str, Any],
    validate: bool,
) -> SendStatus:
    if validate:
        try:
            _ = RTPMessage(**payload)
        except Exception as e:
            logger.warning('Validation failed: %s', e)
            raise HTTPException(status_code=422, detail={'status': 'error', 'message': f"Payload validation failed: {e}"})

    try:
        await producer_service.send_json(topic, payload)
        return SendStatus(status='success')
    except Exception as e:
        logger.exception('Error sending message: %s', e)
        raise HTTPException(status_code=500, detail={'status': 'error', 'message': str(e)})


async def send_file(
    producer_service: ProducerService,
    topic: str,
    file: UploadFile,
    rate: int,
    bulk: bool,
) -> FileSendResult:
    async def process_line(line_no: int, text: str):
        nonlocal sent, failed
        stripped = text.strip()
        if not stripped or stripped.startswith('#'):
            return
        try:
            payload: dict[str, Any] = json.loads(stripped)
            _ = RTPMessage(**payload)  # validation
        except Exception as e:
            failed += 1
            err = FileError(type=type(e).__name__, message=str(e))
            errors_map[err.type] = err
            return
        try:
            await limiter.acquire()
            if bulk:
                await producer_service.send_json(topic, payload)
            else:
                assert sem is not None
                async with sem:
                    await producer_service.send_json(topic, payload)
            sent += 1
        except Exception as e:
            failed += 1
            err = FileError(type=type(e).__name__, message=str(e))
            errors_map[err.type] = err
            logger.debug('Failed to send line %s due to %s', line_no, err.type)

    sent: int = 0
    failed: int = 0
    errors_map: dict[str, FileError] = {}

    sem = None if bulk else asyncio.Semaphore(rate)
    limiter = TokenBucketLimiter(rate=rate)

    tasks = []
    line_no = 0
    for text in iter_file_lines(file):
        line_no += 1
        tasks.append(asyncio.create_task(process_line(line_no, text)))

    await asyncio.gather(*tasks, return_exceptions=True)
    return FileSendResult(sent=sent, failed=failed, errors=list(errors_map.values()))
