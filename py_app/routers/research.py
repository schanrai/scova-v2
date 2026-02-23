from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from py_app.auth import get_settings, verify_jwt
from py_app.config import Settings
from py_app.schemas.research import ResearchRequest, ResearchResponse
from py_app.services.orchestration import run_research

router = APIRouter(prefix="/api", tags=["research"])


@router.get("/health")
def health() -> dict:
    """Health check for smoke tests and load balancers."""
    return {"status": "ok"}


@router.post("/research", response_model=ResearchResponse)
async def post_research(
    request: ResearchRequest,
    _user: Annotated[dict, Depends(verify_jwt)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ResearchResponse:
    """Run full research flow (6 LLM calls); requires valid Supabase JWT."""
    try:
        return await run_research(request, settings)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
