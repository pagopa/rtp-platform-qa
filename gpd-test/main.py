from fastapi import FastAPI, HTTPException, Request
from contextlib import asynccontextmanager
from producer import setup_producer
from dto import RTPMessage
from dotenv import load_dotenv
import os, json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

EVENTHUB_TOPIC = os.environ.get("EVENTHUB_TOPIC", "default-topic")


@asynccontextmanager
async def app_lifespan(fastapi_app: FastAPI):
    try:
        logger.info("Starting producer setup...")
        kafka_producer = await setup_producer()
        app.state.producer = kafka_producer
        logger.info("Producer setup completed successfully")
        yield
        logger.info("Shutting down producer...")
        await kafka_producer.stop()
        logger.info("Producer shutdown completed")
    except Exception as e:
        logger.error(f"Error during lifespan: {e}")
        # Set a flag to indicate producer is not available
        app.state.producer = None
        yield


app = FastAPI(lifespan=app_lifespan)

@app.post("/send/gpd/message")
async def send_msg(message: RTPMessage, request: Request):
    try:
        producer = request.app.state.producer
        if producer is None:
            raise HTTPException(status_code=503, detail="Producer not available")

        await producer.send_and_wait(
            EVENTHUB_TOPIC,
            json.dumps(message.model_dump(by_alias=True)).encode("utf-8")
        )
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))