import uuid
from datetime import UTC, datetime

from app.agent.classification import IssueType, classify_ticket
from app.models import Ticket, TicketPriority, TicketStatus


def create_ticket(subject: str, description: str) -> Ticket:
    """Create an in-memory ticket for classification tests."""

    return Ticket(
        id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        subject=subject,
        description=description,
        status=TicketStatus.OPEN,
        priority=TicketPriority.NORMAL,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def test_classify_ticket_identifies_billing_issue() -> None:
    ticket = create_ticket(
        subject="Duplicate card charge",
        description="My payment appears twice.",
    )

    result = classify_ticket(ticket)

    assert result.issue_type == IssueType.BILLING
    assert result.confidence == 0.9
    assert "charge" in result.rationale


def test_classify_ticket_identifies_shipping_issue() -> None:
    ticket = create_ticket(
        subject="Package not received",
        description="Tracking says delivered.",
    )

    result = classify_ticket(ticket)

    assert result.issue_type == IssueType.SHIPPING
    assert result.confidence == 0.9


def test_classify_ticket_uses_other_for_unknown_issue() -> None:
    ticket = create_ticket(
        subject="General question",
        description="I would like more information.",
    )

    result = classify_ticket(ticket)

    assert result.issue_type == IssueType.OTHER
    assert result.confidence == 0.5
