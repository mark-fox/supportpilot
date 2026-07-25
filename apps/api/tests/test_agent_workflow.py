import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AgentRun,
    AgentRunStatus,
    Ticket,
    TicketPriority,
    TicketStatus,
)
from app.services.agent_workflow import (
    AgentRunNotExecutableError,
    execute_agent_run,
)


def create_agent_run() -> AgentRun:
    """Create an in-memory pending run with its ticket."""

    ticket = Ticket(
        id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        subject="Duplicate charge on my order",
        description="My card was charged twice.",
        status=TicketStatus.OPEN,
        priority=TicketPriority.HIGH,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    agent_run = AgentRun(
        id=uuid.uuid4(),
        ticket_id=ticket.id,
        ticket=ticket,
        status=AgentRunStatus.PENDING,
        created_at=datetime.now(UTC),
    )
    agent_run.steps = []

    return agent_run


@pytest.mark.asyncio
async def test_execute_agent_run_persists_classification_step() -> None:
    agent_run = create_agent_run()

    initial_result = MagicMock()
    initial_result.scalar_one_or_none.return_value = agent_run

    refreshed_result = MagicMock()

    def return_refreshed_run() -> AgentRun:
        added_step = session.add.call_args.args[0]
        agent_run.steps = [added_step]
        return agent_run

    refreshed_result.scalar_one.side_effect = return_refreshed_run

    session = AsyncMock(spec=AsyncSession)
    session.execute.side_effect = [
        initial_result,
        refreshed_result,
    ]

    result = await execute_agent_run(
        session=session,
        agent_run_id=agent_run.id,
    )

    assert result is agent_run
    assert agent_run.status == AgentRunStatus.RUNNING
    assert agent_run.started_at is not None
    assert len(agent_run.steps) == 1

    step = agent_run.steps[0]

    assert step.sequence_number == 1
    assert step.output_data["issue_type"] == "billing"
    assert step.confidence == 0.9

    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_agent_run_rejects_non_pending_run() -> None:
    agent_run = create_agent_run()
    agent_run.status = AgentRunStatus.RUNNING

    result = MagicMock()
    result.scalar_one_or_none.return_value = agent_run

    session = AsyncMock(spec=AsyncSession)
    session.execute.return_value = result

    with pytest.raises(AgentRunNotExecutableError):
        await execute_agent_run(
            session=session,
            agent_run_id=agent_run.id,
        )

    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_execute_agent_run_returns_none_when_missing() -> None:
    result = MagicMock()
    result.scalar_one_or_none.return_value = None

    session = AsyncMock(spec=AsyncSession)
    session.execute.return_value = result

    agent_run = await execute_agent_run(
        session=session,
        agent_run_id=uuid.uuid4(),
    )

    assert agent_run is None
    session.commit.assert_not_awaited()
