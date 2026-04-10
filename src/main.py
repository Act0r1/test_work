import logging

from fastapi import FastAPI

from src.api.errors import register_exception_handlers
from src.payments.router import router as payments_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(payments_router)
    logger.info("FastAPI application configured")
    return app


app = create_app()
