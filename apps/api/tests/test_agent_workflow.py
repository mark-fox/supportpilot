import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AgentRun,
    AgentRunStatus,
    AgentStepType,
    KnowledgeArticle,
    KnowledgeCategory,
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


def create_knowledge_article() -> KnowledgeArticle:
    """Create an approved article for workflow tests."""

    return KnowledgeArticle(
        id=uuid.uuid4(),
        title="Pending and duplicate card charges",
        category=KnowledgeCategory.BILLING,
        content=(
            "Pending duplicate authorizations normally disappear within "
            "three to five business days."
        ),
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_execute_agent_run_persists_first_three_steps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent_run = create_agent_run()
    article = create_knowledge_article()

    initial_result = MagicMock()
    initial_result.scalar_one_or_none.return_value = agent_run

    session = AsyncMock(spec=AsyncSession)

    refreshed_result = MagicMock()

    def return_refreshed_run() -> AgentRun:
        added_steps = session.add_all.call_args.args[0]
        agent_run.steps = list(added_steps)
        return agent_run

    refreshed_result.scalar_one.side_effect = return_refreshed_run

    session.execute.side_effect = [
        initial_result,
        refreshed_result,
    ]

    search_mock = AsyncMock(return_value=[article])

    monkeypatch.setattr(
        "app.services.agent_workflow.search_knowledge_articles",
        search_mock,
    )

    result = await execute_agent_run(
        session=session,
        agent_run_id=agent_run.id,
    )

    assert result is agent_run
    assert agent_run.status == AgentRunStatus.RUNNING
    assert agent_run.started_at is not None
    assert len(agent_run.steps) == 3

    classification_step = agent_run.steps[0]
    severity_step = agent_run.steps[1]
    knowledge_step = agent_run.steps[2]

    assert classification_step.sequence_number == 1
    assert classification_step.step_type == AgentStepType.CLASSIFICATION
    assert classification_step.output_data["issue_type"] == "billing"
    assert classification_step.confidence == 0.9

    assert severity_step.sequence_number == 2
    assert severity_step.step_type == AgentStepType.SEVERITY_ASSESSMENT
    assert severity_step.output_data["severity"] == "high"
    assert severity_step.confidence == 0.9

    assert knowledge_step.sequence_number == 3
    assert knowledge_step.step_type == AgentStepType.KNOWLEDGE_SEARCH
    assert knowledge_step.output_data["result_count"] == 1
    assert knowledge_step.output_data["article_titles"] == [
        "Pending and duplicate card charges",
    ]
    assert knowledge_step.evidence == [
        {
            "article_id": str(article.id),
            "title": article.title,
            "category": "billing",
            "content": article.content,
        },
    ]
    assert knowledge_step.confidence == 1.0

    search_mock.assert_awaited_once_with(
        session=session,
        query=agent_run.ticket.subject,
    )
    session.add_all.assert_called_once()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_agent_run_records_empty_knowledge_search(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent_run = create_agent_run()

    initial_result = MagicMock()
    initial_result.scalar_one_or_none.return_value = agent_run

    session = AsyncMock(spec=AsyncSession)

    refreshed_result = MagicMock()

    def return_refreshed_run() -> AgentRun:
        added_steps = session.add_all.call_args.args[0]
        agent_run.steps = list(added_steps)
        return agent_run

    refreshed_result.scalar_one.side_effect = return_refreshed_run

    session.execute.side_effect = [
        initial_result,
        refreshed_result,
    ]

    search_mock = AsyncMock(return_value=[])

    monkeypatch.setattr(
        "app.services.agent_workflow.search_knowledge_articles",
        search_mock,
    )

    result = await execute_agent_run(
        session=session,
        agent_run_id=agent_run.id,
    )

    knowledge_step = result.steps[2]

    assert knowledge_step.output_data["result_count"] == 0
    assert knowledge_step.evidence == []
    assert knowledge_step.confidence == 0.0


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
