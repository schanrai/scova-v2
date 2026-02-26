import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from py_app.config import Settings
from py_app.routers import research

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Scova v2 API", version="0.1.0")

# In development, allow frontend (localhost:3000) to call this API directly to avoid Next.js proxy timeout
_settings = Settings()
if _settings.environment == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )

app.include_router(research.router)

logger.info("Scova v2 API started")
