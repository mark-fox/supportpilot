from enum import StrEnum

from pydantic import BaseModel, Field

from app.agent.classification import IssueType
from app.models import Ticket, TicketPriority


class SeverityLevel(StrEnum):
    """Operational severity assigned by the support agent."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SeverityResult(BaseModel):
    """Structured result produced by the severity assessment step."""

    severity: SeverityLevel
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str


def assess_ticket_severity(
    ticket: Ticket,
    issue_type: IssueType,
) -> SeverityResult:
    """Assess ticket severity using temporary deterministic rules."""

    if ticket.priority == TicketPriority.URGENT:
        return SeverityResult(
            severity=SeverityLevel.CRITICAL,
            confidence=0.95,
            rationale="The ticket is explicitly marked urgent.",
        )

    if ticket.priority == TicketPriority.HIGH:
        return SeverityResult(
            severity=SeverityLevel.HIGH,
            confidence=0.9,
            rationale="The ticket is explicitly marked high priority.",
        )

    if issue_type in {IssueType.BILLING, IssueType.SHIPPING}:
        return SeverityResult(
            severity=SeverityLevel.MEDIUM,
            confidence=0.85,
            rationale=(
                f"{issue_type.value.capitalize()} issues may involve financial "
                "loss or fulfillment failure."
            ),
        )

    if ticket.priority == TicketPriority.LOW:
        return SeverityResult(
            severity=SeverityLevel.LOW,
            confidence=0.9,
            rationale="The ticket is explicitly marked low priority.",
        )

    return SeverityResult(
        severity=SeverityLevel.LOW,
        confidence=0.75,
        rationale="No indicators of elevated operational impact were found.",
    )
