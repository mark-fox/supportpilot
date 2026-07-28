import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AgentRun,
    AgentRunStatus,
    HumanReviewAction,
    Ticket,
    TicketPriority,
    TicketStatus,
)
from app.services.reviews import (
    AgentRunNotReviewableError,
    create_human_review,
)


def create_completed_agent_run() -> AgentRun:
    """Create a completed agent run with its ticket."""

    ticket = Ticket(
        id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        subject="Duplicate charge",
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
        status=AgentRunStatus.COMPLETED,
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )
    agent_run.reviews = []

    return agent_run


@pytest.mark.asyncio
async def test_create_human_review_approves_run_and_resolves_ticket() -> None:
    agent_run = create_completed_agent_run()

    query_result = MagicMock()
    query_result.scalar_one_or_none.return_value = agent_run

    session = AsyncMock(spec=AsyncSession)
    session.execute.return_value = query_result

    async def refresh_review(review) -> None:
        review.id = uuid.uuid4()
        review.created_at = datetime.now(UTC)

    session.refresh.side_effect = refresh_review

    review = await create_human_review(
        session=session,
        agent_run_id=agent_run.id,
        action=HumanReviewAction.APPROVE,
    )

    assert review is not None
    assert review.action == HumanReviewAction.APPROVE
    assert agent_run.ticket.status == TicketStatus.RESOLVED

    session.add.assert_called_once_with(review)
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(review)


@pytest.mark.asyncio
async def test_create_human_review_requests_revision() -> None:
    agent_run = create_completed_agent_run()

    query_result = MagicMock()
    query_result.scalar_one_or_none.return_value = agent_run

    session = AsyncMock(spec=AsyncSession)
    session.execute.return_value = query_result

    async def refresh_review(review) -> None:
        review.id = uuid.uuid4()
        review.created_at = datetime.now(UTC)

    session.refresh.side_effect = refresh_review

    review = await create_human_review(
        session=session,
        agent_run_id=agent_run.id,
        action=HumanReviewAction.REQUEST_REVISION,
        reviewer_note="Clarify the expected refund timeline.",
    )

    assert review is not None
    assert review.reviewer_note == "Clarify the expected refund timeline."
    assert agent_run.ticket.status == TicketStatus.IN_REVIEW


@pytest.mark.asyncio
async def test_create_human_review_requires_revision_note() -> None:
    agent_run = create_completed_agent_run()

    query_result = MagicMock()
    query_result.scalar_one_or_none.return_value = agent_run

    session = AsyncMock(spec=AsyncSession)
    session.execute.return_value = query_result

    with pytest.raises(
        AgentRunNotReviewableError,
        match="reviewer note is required",
    ):
        await create_human_review(
            session=session,
            agent_run_id=agent_run.id,
            action=HumanReviewAction.REQUEST_REVISION,
        )

    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_human_review_rejects_duplicate_review() -> None:
    agent_run = create_completed_agent_run()
    agent_run.reviews = [MagicMock()]

    query_result = MagicMock()
    query_result.scalar_one_or_none.return_value = agent_run

    session = AsyncMock(spec=AsyncSession)
    session.execute.return_value = query_result

    with pytest.raises(
        AgentRunNotReviewableError,
        match="already has a human review",
    ):
        await create_human_review(
            session=session,
            agent_run_id=agent_run.id,
            action=HumanReviewAction.APPROVE,
        )

    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_human_review_returns_none_for_missing_run() -> None:
    query_result = MagicMock()
    query_result.scalar_one_or_none.return_value = None

    session = AsyncMock(spec=AsyncSession)
    session.execute.return_value = query_result

    review = await create_human_review(
        session=session,
        agent_run_id=uuid.uuid4(),
        action=HumanReviewAction.ESCALATE,
    )

    assert review is None
    session.commit.assert_not_awaited()
