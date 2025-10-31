import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from middleware.access_log import access_log_middleware
from middleware.errors import add_exception_handlers
from middleware.request_id import request_id_middleware
from services.producer import ProducerService

from api.gpd import router as gpd_router
from api.health import router as health_router

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('gpd-producer')


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info('Starting ProducerService...')
        producer_service = ProducerService()
        await producer_service.start()
        app.state.producer_service = producer_service
        logger.info('ProducerService started')
    except Exception as e:
        logger.exception('Failed to start ProducerService: %s', e)
        app.state.producer_service = None

    yield

    producer_service: ProducerService | None = getattr(app.state, 'producer_service', None)
    if producer_service:
        logger.info('Stopping ProducerService...')
        await producer_service.stop()
        logger.info('ProducerService stopped')


def create_app() -> FastAPI:
    app = FastAPI(title='GPD Producer', lifespan=lifespan)

    app.middleware('http')(request_id_middleware)
    app.middleware('http')(access_log_middleware)
    add_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(gpd_router)

    return app


app = create_app()
