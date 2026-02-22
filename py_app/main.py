import logging
import sys

from fastapi import FastAPI

from py_app.routers import research

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Scova v2 API", version="0.1.0")
app.include_router(research.router)

logger.info("Scova v2 API started")
