import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    AgentRun,
    AgentRunStatus,
    HumanReview,
    HumanReviewAction,
    TicketStatus,
)


class AgentRunNotReviewableError(Exception):
    """Raised when a human review cannot be recorded."""


async def create_human_review(
    session: AsyncSession,
    agent_run_id: uuid.UUID,
    action: HumanReviewAction,
    reviewer_note: str | None = None,
    revised_response: str | None = None,
) -> HumanReview | None:
    """Record a human decision for one completed agent run."""

    statement = (
        select(AgentRun)
        .options(
            selectinload(AgentRun.ticket),
            selectinload(AgentRun.reviews),
        )
        .where(AgentRun.id == agent_run_id)
    )

    result = await session.execute(statement)
    agent_run = result.scalar_one_or_none()

    if agent_run is None:
        return None

    if agent_run.status != AgentRunStatus.COMPLETED:
        raise AgentRunNotReviewableError(
            "Only completed agent runs can be reviewed.",
        )

    if agent_run.reviews:
        raise AgentRunNotReviewableError(
            "This agent run already has a human review.",
        )

    if action == HumanReviewAction.REQUEST_REVISION and not reviewer_note:
        raise AgentRunNotReviewableError(
            "A reviewer note is required when requesting revision.",
        )

    if revised_response is not None and not revised_response.strip():
        raise AgentRunNotReviewableError(
            "The revised response cannot be blank.",
        )

    review = HumanReview(
        agent_run_id=agent_run.id,
        action=action,
        reviewer_note=reviewer_note,
        revised_response=revised_response,
    )

    if action == HumanReviewAction.APPROVE:
        agent_run.ticket.status = TicketStatus.RESOLVED
    elif action == HumanReviewAction.REQUEST_REVISION:
        agent_run.ticket.status = TicketStatus.IN_REVIEW
    else:
        agent_run.ticket.status = TicketStatus.ESCALATED

    session.add(review)
    await session.commit()
    await session.refresh(review)

    return review
