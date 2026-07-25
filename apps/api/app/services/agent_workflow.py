import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agent.classification import classify_ticket
from app.models import (
    AgentRun,
    AgentRunStatus,
    AgentStep,
    AgentStepStatus,
    AgentStepType,
)


class AgentRunNotExecutableError(Exception):
    """Raised when an agent run cannot be executed."""


async def execute_agent_run(
    session: AsyncSession,
    agent_run_id: uuid.UUID,
) -> AgentRun | None:
    """Execute the currently implemented agent workflow steps."""

    statement = (
        select(AgentRun)
        .options(
            selectinload(AgentRun.ticket),
            selectinload(AgentRun.steps),
        )
        .where(AgentRun.id == agent_run_id)
    )

    result = await session.execute(statement)
    agent_run = result.scalar_one_or_none()

    if agent_run is None:
        return None

    if agent_run.status != AgentRunStatus.PENDING:
        raise AgentRunNotExecutableError(
            f"Agent run with status '{agent_run.status}' cannot be executed.",
        )

    started_at = datetime.now(UTC)

    agent_run.status = AgentRunStatus.RUNNING
    agent_run.started_at = started_at

    classification = classify_ticket(agent_run.ticket)

    classification_step = AgentStep(
        agent_run=agent_run,
        sequence_number=1,
        step_type=AgentStepType.CLASSIFICATION,
        status=AgentStepStatus.COMPLETED,
        input_data={
            "subject": agent_run.ticket.subject,
            "description": agent_run.ticket.description,
        },
        output_data=classification.model_dump(mode="json"),
        evidence=[],
        confidence=classification.confidence,
        started_at=started_at,
        completed_at=datetime.now(UTC),
    )

    session.add(classification_step)
    await session.commit()

    refreshed_statement = (
        select(AgentRun).options(selectinload(AgentRun.steps)).where(AgentRun.id == agent_run_id)
    )

    refreshed_result = await session.execute(refreshed_statement)

    return refreshed_result.scalar_one()
