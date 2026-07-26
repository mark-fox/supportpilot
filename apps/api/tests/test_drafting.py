import uuid
from datetime import UTC, datetime

from app.agent.classification import IssueType
from app.agent.drafting import draft_support_response
from app.models import (
    KnowledgeArticle,
    KnowledgeCategory,
    Order,
    OrderStatus,
    Ticket,
    TicketPriority,
    TicketStatus,
)


def create_ticket() -> Ticket:
    """Create an in-memory ticket for drafting tests."""

    return Ticket(
        id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        subject="Duplicate charge",
        description="My card was charged twice.",
        status=TicketStatus.OPEN,
        priority=TicketPriority.HIGH,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def create_article() -> KnowledgeArticle:
    """Create an approved article for drafting tests."""

    return KnowledgeArticle(
        id=uuid.uuid4(),
        title="Pending and duplicate card charges",
        category=KnowledgeCategory.BILLING,
        content=("Pending authorizations normally disappear within three to five business days."),
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def create_order(customer_id: uuid.UUID) -> Order:
    """Create an order for drafting tests."""

    return Order(
        id=uuid.uuid4(),
        customer_id=customer_id,
        order_number="SP-10482",
        status=OrderStatus.PROCESSING,
        total_cents=12999,
        tracking_number=None,
        created_at=datetime.now(UTC),
    )


def test_draft_support_response_uses_grounded_billing_context() -> None:
    ticket = create_ticket()
    article = create_article()
    order = create_order(ticket.customer_id)

    result = draft_support_response(
        ticket=ticket,
        issue_type=IssueType.BILLING,
        knowledge_articles=[article],
        customer_orders=[order],
        evidence_is_sufficient=True,
    )

    assert result.was_drafted is True
    assert result.drafted_response is not None
    assert "SP-10482" in result.drafted_response
    assert article.content in result.drafted_response


def test_draft_support_response_skips_when_evidence_is_insufficient() -> None:
    result = draft_support_response(
        ticket=create_ticket(),
        issue_type=IssueType.BILLING,
        knowledge_articles=[],
        customer_orders=[],
        evidence_is_sufficient=False,
    )

    assert result.was_drafted is False
    assert result.drafted_response is None


def test_draft_support_response_skips_unsupported_issue_type() -> None:
    ticket = create_ticket()
    article = create_article()
    order = create_order(ticket.customer_id)

    result = draft_support_response(
        ticket=ticket,
        issue_type=IssueType.OTHER,
        knowledge_articles=[article],
        customer_orders=[order],
        evidence_is_sufficient=True,
    )

    assert result.was_drafted is False
    assert result.drafted_response is None
