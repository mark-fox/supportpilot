import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models import Ticket
from app.schemas import AgentRunSummary
from app.services.agent_runs import create_agent_run

router = APIRouter(
    prefix="/tickets",
    tags=["agent runs"],
)


@router.post(
    "/{ticket_id}/agent-runs",
    response_model=AgentRunSummary,
    status_code=status.HTTP_201_CREATED,
)
async def start_agent_run(
    ticket_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AgentRunSummary:
    """Create a pending agent run for an existing ticket."""

    ticket_exists = await session.scalar(
        select(Ticket.id).where(Ticket.id == ticket_id),
    )

    if ticket_exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    agent_run = await create_agent_run(
        session=session,
        ticket_id=ticket_id,
    )

    return AgentRunSummary.model_validate(agent_run)
