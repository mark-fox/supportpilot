import uuid
from datetime import UTC, datetime

import pytest

from app.agent.graph import support_workflow
from app.models import Ticket, TicketPriority, TicketStatus


def create_ticket() -> Ticket:
    """Create a ticket for LangGraph workflow tests."""

    return Ticket(
        id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        subject="Duplicate charge on my order",
        description="My card was charged twice.",
        status=TicketStatus.OPEN,
        priority=TicketPriority.HIGH,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_support_workflow_produces_classification_and_severity() -> None:
    agent_run_id = uuid.uuid4()
    ticket = create_ticket()

    result = await support_workflow.ainvoke(
        {
            "agent_run_id": agent_run_id,
            "ticket": ticket,
            "classification": None,
            "severity": None,
            "completed_nodes": [],
        },
    )

    assert result["agent_run_id"] == agent_run_id

    assert result["classification"] == {
        "issue_type": "billing",
        "confidence": 0.9,
        "rationale": "Matched support keywords: charge, charged.",
    }

    assert result["severity"] == {
        "severity": "high",
        "confidence": 0.9,
        "rationale": "The ticket is explicitly marked high priority.",
    }

    assert result["completed_nodes"] == [
        "classification",
        "severity_assessment",
        "knowledge_search",
        "order_lookup",
        "evidence_assessment",
        "response_draft",
        "escalation_decision",
    ]
