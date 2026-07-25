import uuid
from datetime import UTC, datetime

from app.agent.classification import IssueType
from app.agent.severity import SeverityLevel, assess_ticket_severity
from app.models import Ticket, TicketPriority, TicketStatus


def create_ticket(priority: TicketPriority) -> Ticket:
    """Create an in-memory ticket for severity tests."""

    return Ticket(
        id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        subject="Support request",
        description="Customer needs assistance.",
        status=TicketStatus.OPEN,
        priority=priority,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def test_assess_ticket_severity_marks_urgent_as_critical() -> None:
    ticket = create_ticket(TicketPriority.URGENT)

    result = assess_ticket_severity(
        ticket=ticket,
        issue_type=IssueType.SHIPPING,
    )

    assert result.severity == SeverityLevel.CRITICAL
    assert result.confidence == 0.95


def test_assess_ticket_severity_marks_high_priority_as_high() -> None:
    ticket = create_ticket(TicketPriority.HIGH)

    result = assess_ticket_severity(
        ticket=ticket,
        issue_type=IssueType.BILLING,
    )

    assert result.severity == SeverityLevel.HIGH
    assert result.confidence == 0.9


def test_assess_ticket_severity_elevates_normal_billing_issue() -> None:
    ticket = create_ticket(TicketPriority.NORMAL)

    result = assess_ticket_severity(
        ticket=ticket,
        issue_type=IssueType.BILLING,
    )

    assert result.severity == SeverityLevel.MEDIUM
    assert result.confidence == 0.85


def test_assess_ticket_severity_uses_low_for_general_issue() -> None:
    ticket = create_ticket(TicketPriority.NORMAL)

    result = assess_ticket_severity(
        ticket=ticket,
        issue_type=IssueType.OTHER,
    )

    assert result.severity == SeverityLevel.LOW
    assert result.confidence == 0.75
