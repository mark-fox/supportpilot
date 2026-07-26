from pydantic import BaseModel

from app.agent.classification import IssueType
from app.models import KnowledgeArticle, Order, Ticket


class DraftResponseResult(BaseModel):
    """Structured response-drafting result."""

    drafted_response: str | None
    was_drafted: bool
    rationale: str


def draft_support_response(
    ticket: Ticket,
    issue_type: IssueType,
    knowledge_articles: list[KnowledgeArticle],
    customer_orders: list[Order],
    evidence_is_sufficient: bool,
) -> DraftResponseResult:
    """Create a temporary deterministic response grounded in collected evidence."""

    if not evidence_is_sufficient:
        return DraftResponseResult(
            drafted_response=None,
            was_drafted=False,
            rationale=(
                "A response was not drafted because the workflow lacks "
                "sufficient grounded evidence."
            ),
        )

    article = knowledge_articles[0]
    order = customer_orders[0]

    if issue_type == IssueType.BILLING:
        drafted_response = (
            f"Hello,\n\n"
            f"Thank you for contacting us about order {order.order_number}. "
            "I reviewed the order and the guidance for duplicate card charges. "
            f"{article.content}\n\n"
            "Please continue monitoring the charges. If both charges fully post, "
            "reply to this message so our billing team can review the transaction.\n\n"
            "Best,\nSupport Team"
        )
    elif issue_type == IssueType.SHIPPING:
        drafted_response = (
            f"Hello,\n\n"
            f"Thank you for contacting us about order {order.order_number}. "
            f"The order is currently marked as {order.status.value}. "
            f"{article.content}\n\n"
            "Please let us know if the package remains missing after the recommended "
            "waiting period so the case can be escalated for further review.\n\n"
            "Best,\nSupport Team"
        )
    elif issue_type == IssueType.ACCOUNT:
        drafted_response = (
            f"Hello,\n\n"
            f"Thank you for reaching out. {article.content}\n\n"
            "Please let us know if you are unable to make the change from your "
            "account settings.\n\n"
            "Best,\nSupport Team"
        )
    else:
        return DraftResponseResult(
            drafted_response=None,
            was_drafted=False,
            rationale=("The current deterministic drafting rules do not support this issue type."),
        )

    return DraftResponseResult(
        drafted_response=drafted_response,
        was_drafted=True,
        rationale=(
            "The response was drafted using approved knowledge and customer-specific order context."
        ),
    )
