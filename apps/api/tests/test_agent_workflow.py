import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AgentRecommendation,
    AgentRun,
    AgentRunStatus,
    AgentStepType,
    KnowledgeArticle,
    KnowledgeCategory,
    Order,
    OrderStatus,
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


def create_order(customer_id: uuid.UUID) -> Order:
    """Create an order for workflow tests."""

    return Order(
        id=uuid.uuid4(),
        customer_id=customer_id,
        order_number="SP-10482",
        status=OrderStatus.PROCESSING,
        total_cents=12999,
        tracking_number=None,
        created_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_execute_agent_run_completes_seven_step_workflow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent_run = create_agent_run()
    article = create_knowledge_article()
    order = create_order(agent_run.ticket.customer_id)

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

    knowledge_search_mock = AsyncMock(return_value=[article])
    order_lookup_mock = AsyncMock(return_value=[order])

    monkeypatch.setattr(
        "app.services.agent_workflow.search_knowledge_articles",
        knowledge_search_mock,
    )
    monkeypatch.setattr(
        "app.services.agent_workflow.lookup_customer_orders",
        order_lookup_mock,
    )

    result = await execute_agent_run(
        session=session,
        agent_run_id=agent_run.id,
    )

    assert result is agent_run
    assert len(agent_run.steps) == 7

    classification_step = agent_run.steps[0]
    severity_step = agent_run.steps[1]
    knowledge_step = agent_run.steps[2]
    order_lookup_step = agent_run.steps[3]
    evidence_assessment_step = agent_run.steps[4]
    response_draft_step = agent_run.steps[5]
    escalation_step = agent_run.steps[6]

    assert classification_step.step_type == AgentStepType.CLASSIFICATION
    assert classification_step.output_data["issue_type"] == "billing"

    assert severity_step.step_type == AgentStepType.SEVERITY_ASSESSMENT
    assert severity_step.output_data["severity"] == "high"

    assert knowledge_step.step_type == AgentStepType.KNOWLEDGE_SEARCH
    assert knowledge_step.output_data["result_count"] == 1

    assert order_lookup_step.step_type == AgentStepType.ORDER_LOOKUP
    assert order_lookup_step.output_data["order_numbers"] == ["SP-10482"]

    assert evidence_assessment_step.step_type == AgentStepType.EVIDENCE_ASSESSMENT
    assert evidence_assessment_step.output_data["is_sufficient"] is True

    assert response_draft_step.step_type == AgentStepType.RESPONSE_DRAFT
    assert response_draft_step.output_data["was_drafted"] is True
    assert "SP-10482" in response_draft_step.output_data["drafted_response"]

    assert escalation_step.sequence_number == 7
    assert escalation_step.step_type == AgentStepType.ESCALATION_DECISION
    assert escalation_step.output_data["recommendation"] == "human_review"
    assert escalation_step.confidence == 0.95

    assert agent_run.status == AgentRunStatus.COMPLETED
    assert agent_run.completed_at is not None
    assert agent_run.recommendation == AgentRecommendation.HUMAN_REVIEW
    assert agent_run.confidence == 0.95
    assert agent_run.drafted_response is not None

    session.add_all.assert_called_once()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_agent_run_escalates_when_context_is_missing(
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

    monkeypatch.setattr(
        "app.services.agent_workflow.search_knowledge_articles",
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(
        "app.services.agent_workflow.lookup_customer_orders",
        AsyncMock(return_value=[]),
    )

    result = await execute_agent_run(
        session=session,
        agent_run_id=agent_run.id,
    )

    assert result is agent_run
    assert len(result.steps) == 7

    evidence_assessment_step = result.steps[4]
    response_draft_step = result.steps[5]
    escalation_step = result.steps[6]

    assert evidence_assessment_step.output_data["is_sufficient"] is False
    assert response_draft_step.output_data["was_drafted"] is False
    assert response_draft_step.output_data["drafted_response"] is None

    assert escalation_step.output_data["recommendation"] == "escalate"
    assert escalation_step.confidence == 0.95

    assert result.status == AgentRunStatus.COMPLETED
    assert result.recommendation == AgentRecommendation.ESCALATE
    assert result.confidence == 0.95
    assert result.drafted_response is None
    assert result.completed_at is not None


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
