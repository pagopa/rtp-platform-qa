import asyncio

from fastapi import UploadFile, File, Query, Request, HTTPException, APIRouter
from dto import RTPMessage
import os, json, logging

gpd_router = APIRouter()
logger = logging.getLogger("gpd-producer")
EVENTHUB_TOPIC = os.environ.get("EVENTHUB_TOPIC", "default-topic")

def sanitize_log_value(value) -> str:
    return str(value).replace("\n", "").replace("\r", "")

@gpd_router.post("/send/gpd/message")
async def send_msg(request: Request, validate: bool = Query(default=True)):
    payload = await request.json()
    logger.info(
        "Received message - id: %s, operation: %s, iuv: %s, status: %s",
        sanitize_log_value(payload.get("id")),
        sanitize_log_value(payload.get("operation")),
        sanitize_log_value(payload.get("iuv")),
        sanitize_log_value(payload.get("status")),
    )

    if validate:
        try:
            _ = RTPMessage(**payload)
        except Exception as e:
            logger.warning("Validation failed: %s", e)
            raise HTTPException(
                status_code=422,
                detail={
                    "status": "error",
                    "message": f"Payload validation failed: {e}"
                }
            )

    try:
        producer = request.app.state.producer
        if producer is None:
            raise ConnectionError("Kafka producer is not available")

        await producer.send_and_wait(
            EVENTHUB_TOPIC,
            json.dumps(payload).encode("utf-8")
        )

        logger.info("Message sent successfully")
        return {"status": "success"}

    except Exception as e:
        logger.exception("Error sending message: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(e)
            }
        )

@gpd_router.post("/send/gpd/file")
async def send_file(
    request: Request,
    file: UploadFile = File(..., description="NDJSON file: one RTPMessage JSON per line"),
    bulk: bool = Query(default=False, description="If true, send all messages at once without concurrency control"),
    concurrency: int = Query(default=10, ge=1, le=200),
):
    producer = getattr(request.app.state, "producer", None)
    if producer is None:
        raise HTTPException(
            status_code=503,
            detail={"status": "error", "message": "Kafka producer is not available"},
        )

    total, sent = 0, 0
    failures = []
    sem = None if bulk else asyncio.Semaphore(concurrency)
    tasks = []

    async def process_line(line: int, text: str):
        nonlocal sent
        stripped = text.strip()
        if not stripped or stripped.startswith("#"):
            return
        try:
            payload = json.loads(stripped)
            _ = RTPMessage(**payload)  # validate
        except Exception as e:
            failures.append({"line": line, "reason": f"Validation error: {e}", "preview": stripped[:200]})
            return
        try:
            if bulk:
                # no concurrency, send immediately
                await producer.send_and_wait(EVENTHUB_TOPIC, json.dumps(payload).encode("utf-8"))
            else:
                async with sem:
                    await producer.send_and_wait(EVENTHUB_TOPIC, json.dumps(payload).encode("utf-8"))
            sent += 1
        except Exception as e:
            failures.append({"line": line, "reason": f"Send failed: {str(e)}", "preview": stripped[:200]})

    line = 0
    for raw in file.file:
        line += 1
        text = raw.decode("utf-8", errors="replace")
        if text.strip() and not text.lstrip().startswith("#"):
            total += 1
        tasks.append(asyncio.create_task(process_line(line, text)))

    await asyncio.gather(*tasks, return_exceptions=True)
    return {
        "status": "completed",
        "total": total,
        "sent": sent,
        "failed": len(failures),
        "errors": failures[:200],
    }
