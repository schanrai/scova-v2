import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from py_app.auth import get_settings, verify_jwt
from py_app.config import Settings
from py_app.schemas.research import ResearchRequest, ResearchResponse
from py_app.services.orchestration import run_research
from py_app.validators.input_validator import validate_research_request

logger = logging.getLogger(__name__)
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
    validation_error = validate_research_request(
        request.company_name,
        request.region_focus,
        request.specific_region or "",
        request.division_focus or "",
        request.specific_division or "",
    )
    if validation_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_error,
        )
    try:
        return await run_research(request, settings)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except ValidationError as e:
        logger.exception("Response validation failed after LLM calls: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Response validation failed: {e.errors()}",
        ) from e
    except Exception as e:
        logger.exception("Research failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e
