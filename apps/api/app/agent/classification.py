from enum import StrEnum

from pydantic import BaseModel, Field

from app.models import Ticket


class IssueType(StrEnum):
    """Supported ticket classifications produced by the agent."""

    BILLING = "billing"
    SHIPPING = "shipping"
    ACCOUNT = "account"
    RETURNS = "returns"
    OTHER = "other"


class ClassificationResult(BaseModel):
    """Structured result produced by the classification step."""

    issue_type: IssueType
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str


def classify_ticket(ticket: Ticket) -> ClassificationResult:
    """Classify a ticket using temporary deterministic rules."""

    searchable_text = f"{ticket.subject} {ticket.description}".lower()

    classification_rules = (
        (
            IssueType.BILLING,
            ("charge", "charged", "payment", "billing", "refund"),
        ),
        (
            IssueType.SHIPPING,
            ("package", "delivery", "delivered", "shipping", "tracking"),
        ),
        (
            IssueType.ACCOUNT,
            ("account", "address", "password", "login", "profile"),
        ),
        (
            IssueType.RETURNS,
            ("return", "replacement", "exchange"),
        ),
    )

    for issue_type, keywords in classification_rules:
        matched_keywords = [keyword for keyword in keywords if keyword in searchable_text]

        if matched_keywords:
            return ClassificationResult(
                issue_type=issue_type,
                confidence=0.9,
                rationale=(f"Matched support keywords: {', '.join(matched_keywords)}."),
            )

    return ClassificationResult(
        issue_type=IssueType.OTHER,
        confidence=0.5,
        rationale="No supported issue-specific keywords were found.",
    )
