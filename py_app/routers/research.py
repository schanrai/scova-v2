from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["research"])


@router.get("/health")
def health() -> dict:
    """Health check for smoke tests and load balancers."""
    return {"status": "ok"}
