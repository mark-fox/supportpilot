import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agent.classification import classify_ticket
from app.agent.severity import assess_ticket_severity
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

    agent_run.status = AgentRunStatus.RUNNING
    agent_run.started_at = datetime.now(UTC)

    classification_started_at = datetime.now(UTC)
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
        started_at=classification_started_at,
        completed_at=datetime.now(UTC),
    )

    severity_started_at = datetime.now(UTC)
    severity = assess_ticket_severity(
        ticket=agent_run.ticket,
        issue_type=classification.issue_type,
    )

    severity_step = AgentStep(
        agent_run=agent_run,
        sequence_number=2,
        step_type=AgentStepType.SEVERITY_ASSESSMENT,
        status=AgentStepStatus.COMPLETED,
        input_data={
            "ticket_priority": agent_run.ticket.priority.value,
            "issue_type": classification.issue_type.value,
        },
        output_data=severity.model_dump(mode="json"),
        evidence=[],
        confidence=severity.confidence,
        started_at=severity_started_at,
        completed_at=datetime.now(UTC),
    )

    session.add_all(
        [
            classification_step,
            severity_step,
        ],
    )
    await session.commit()

    refreshed_statement = (
        select(AgentRun).options(selectinload(AgentRun.steps)).where(AgentRun.id == agent_run_id)
    )

    refreshed_result = await session.execute(refreshed_statement)

    return refreshed_result.scalar_one()
