import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agent.classification import classify_ticket
from app.agent.severity import assess_ticket_severity
from app.models import (
    AgentRun,
    AgentRunStatus,
    AgentStep,
    AgentStepStatus,
    AgentStepType,
)
from app.services.knowledge import search_knowledge_articles
from app.services.orders import lookup_customer_orders


class AgentRunNotExecutableError(Exception):
    """Raised when an agent run cannot be executed."""


async def execute_agent_run(
    session: AsyncSession,
    agent_run_id: uuid.UUID,
) -> AgentRun | None:
    """Execute the currently implemented agent workflow steps."""

    statement = (
        select(AgentRun)
        .options(
            selectinload(AgentRun.ticket),
            selectinload(AgentRun.steps),
        )
        .where(AgentRun.id == agent_run_id)
    )

    result = await session.execute(statement)
    agent_run = result.scalar_one_or_none()

    if agent_run is None:
        return None

    if agent_run.status != AgentRunStatus.PENDING:
        raise AgentRunNotExecutableError(
            f"Agent run with status '{agent_run.status}' cannot be executed.",
        )

    agent_run.status = AgentRunStatus.RUNNING
    agent_run.started_at = datetime.now(UTC)

    classification_started_at = datetime.now(UTC)
    classification = classify_ticket(agent_run.ticket)

    classification_step = AgentStep(
        agent_run=agent_run,
        sequence_number=1,
        step_type=AgentStepType.CLASSIFICATION,
        status=AgentStepStatus.COMPLETED,
        input_data={
            "subject": agent_run.ticket.subject,
            "description": agent_run.ticket.description,
        },
        output_data=classification.model_dump(mode="json"),
        evidence=[],
        confidence=classification.confidence,
        started_at=classification_started_at,
        completed_at=datetime.now(UTC),
    )

    severity_started_at = datetime.now(UTC)
    severity = assess_ticket_severity(
        ticket=agent_run.ticket,
        issue_type=classification.issue_type,
    )

    severity_step = AgentStep(
        agent_run=agent_run,
        sequence_number=2,
        step_type=AgentStepType.SEVERITY_ASSESSMENT,
        status=AgentStepStatus.COMPLETED,
        input_data={
            "ticket_priority": agent_run.ticket.priority.value,
            "issue_type": classification.issue_type.value,
        },
        output_data=severity.model_dump(mode="json"),
        evidence=[],
        confidence=severity.confidence,
        started_at=severity_started_at,
        completed_at=datetime.now(UTC),
    )

    knowledge_started_at = datetime.now(UTC)
    knowledge_query = agent_run.ticket.subject

    knowledge_articles = await search_knowledge_articles(
        session=session,
        query=knowledge_query,
    )

    knowledge_evidence = [
        {
            "article_id": str(article.id),
            "title": article.title,
            "category": article.category.value,
            "content": article.content,
        }
        for article in knowledge_articles
    ]

    knowledge_step = AgentStep(
        agent_run=agent_run,
        sequence_number=3,
        step_type=AgentStepType.KNOWLEDGE_SEARCH,
        status=AgentStepStatus.COMPLETED,
        input_data={
            "query": knowledge_query,
            "active_articles_only": True,
            "result_limit": 3,
        },
        output_data={
            "result_count": len(knowledge_articles),
            "article_titles": [article.title for article in knowledge_articles],
        },
        evidence=knowledge_evidence,
        confidence=1.0 if knowledge_articles else 0.0,
        started_at=knowledge_started_at,
        completed_at=datetime.now(UTC),
    )

    order_lookup_started_at = datetime.now(UTC)

    customer_orders = await lookup_customer_orders(
        session=session,
        customer_id=agent_run.ticket.customer_id,
    )

    order_evidence = [
        {
            "order_id": str(order.id),
            "order_number": order.order_number,
            "status": order.status.value,
            "total_cents": order.total_cents,
            "tracking_number": order.tracking_number,
            "created_at": order.created_at.isoformat(),
        }
        for order in customer_orders
    ]

    order_lookup_step = AgentStep(
        agent_run=agent_run,
        sequence_number=4,
        step_type=AgentStepType.ORDER_LOOKUP,
        status=AgentStepStatus.COMPLETED,
        input_data={
            "customer_id": str(agent_run.ticket.customer_id),
            "order_number": None,
            "result_limit": 5,
        },
        output_data={
            "result_count": len(customer_orders),
            "order_numbers": [order.order_number for order in customer_orders],
        },
        evidence=order_evidence,
        confidence=1.0 if customer_orders else 0.0,
        started_at=order_lookup_started_at,
        completed_at=datetime.now(UTC),
    )

    session.add_all(
        [
            classification_step,
            severity_step,
            knowledge_step,
            order_lookup_step,
        ],
    )
    await session.commit()

    refreshed_statement = (
        select(AgentRun).options(selectinload(AgentRun.steps)).where(AgentRun.id == agent_run_id)
    )

    refreshed_result = await session.execute(refreshed_statement)

    return refreshed_result.scalar_one()
