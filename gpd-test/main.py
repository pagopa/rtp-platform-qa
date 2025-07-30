from fastapi import FastAPI, HTTPException, Request
from contextlib import asynccontextmanager
from producer import setup_producer
from dto import RTPMessage
from dotenv import load_dotenv
import os, json

load_dotenv()

EVENTHUB_TOPIC = os.environ["EVENTHUB_TOPIC"]

@asynccontextmanager
async def app_lifespan(fastapi_app: FastAPI):
    kafka_producer = await setup_producer()
    app.state.producer = kafka_producer
    yield
    await kafka_producer.stop()

app = FastAPI(lifespan=app_lifespan)

@app.post("/send/gpd/message")
async def send_msg(message: RTPMessage, request: Request):
    try:
        producer = request.app.state.producer
        await producer.send_and_wait(
            EVENTHUB_TOPIC,
            json.dumps(message.model_dump(by_alias=True)).encode("utf-8")
        )
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
