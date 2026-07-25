import uuid

from sqlalchemy.ext.asyncio import AsyncSession

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
