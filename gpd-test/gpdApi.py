from fastapi import APIRouter, HTTPException, Request, Query
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