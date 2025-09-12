import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from gpdApi import gpd_router
from healthCheckApi import health_router
from producer import setup_producer

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    try:
        logger.info('Starting producer setup...')
        kafka_producer = await setup_producer()
        app.state.producer = kafka_producer
        logger.info('Producer setup completed successfully')
        yield
        logger.info('Shutting down producer...')
        await kafka_producer.stop()
        logger.info('Producer shutdown completed')
    except Exception as e:
        logger.error(f"Error during lifespan: {e}")
        app.state.producer = None
        yield

app = FastAPI(lifespan=app_lifespan)
app.include_router(health_router)
app.include_router(gpd_router)
