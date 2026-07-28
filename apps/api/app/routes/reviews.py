import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.schemas import HumanReviewCreate, HumanReviewSummary
from app.services.reviews import (
    AgentRunNotReviewableError,
    create_human_review,
)

router = APIRouter(
    prefix="/agent-runs",
    tags=["human reviews"],
)


@router.post(
    "/{agent_run_id}/reviews",
    response_model=HumanReviewSummary,
    status_code=status.HTTP_201_CREATED,
)
async def submit_human_review(
    agent_run_id: uuid.UUID,
    review_data: HumanReviewCreate,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> HumanReviewSummary:
    """Record a human decision for a completed agent run."""

    try:
        review = await create_human_review(
            session=session,
            agent_run_id=agent_run_id,
            action=review_data.action,
            reviewer_note=review_data.reviewer_note,
            revised_response=review_data.revised_response,
        )
    except AgentRunNotReviewableError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent run not found",
        )

    return HumanReviewSummary.model_validate(review)
