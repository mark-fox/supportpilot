import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import AgentRun, AgentRunStatus


async def create_agent_run(
    session: AsyncSession,
    ticket_id: uuid.UUID,
) -> AgentRun:
    """Create and persist a pending agent run for one ticket."""

    agent_run = AgentRun(
        ticket_id=ticket_id,
        status=AgentRunStatus.PENDING,
    )

    session.add(agent_run)
    await session.commit()
    await session.refresh(agent_run)

    return agent_run


async def get_agent_run(
    session: AsyncSession,
    agent_run_id: uuid.UUID,
) -> AgentRun | None:
    """Return one agent run with its ordered workflow steps."""

    statement = (
        select(AgentRun).options(selectinload(AgentRun.steps)).where(AgentRun.id == agent_run_id)
    )

    result = await session.execute(statement)

    return result.scalar_one_or_none()
