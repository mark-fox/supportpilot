import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models import Ticket
from app.schemas import AgentRunDetail, AgentRunSummary
from app.services.agent_runs import create_agent_run, get_agent_run

router = APIRouter(
    tags=["agent runs"],
)


@router.post(
    "/tickets/{ticket_id}/agent-runs",
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


@router.get(
    "/agent-runs/{agent_run_id}",
    response_model=AgentRunDetail,
)
async def read_agent_run(
    agent_run_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AgentRunDetail:
    """Return an agent run and its complete workflow trace."""

    agent_run = await get_agent_run(
        session=session,
        agent_run_id=agent_run_id,
    )

    if agent_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent run not found",
        )

    return AgentRunDetail.model_validate(agent_run)
