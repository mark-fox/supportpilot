import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agent.classification import ClassificationResult
from app.agent.drafting import draft_support_response
from app.agent.escalation import decide_escalation
from app.agent.evidence import assess_evidence
from app.agent.graph import support_workflow
from app.agent.severity import SeverityResult
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
    """Execute the deterministic support-agent workflow."""

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

    graph_result = await support_workflow.ainvoke(
        {
            "agent_run_id": agent_run.id,
            "ticket": agent_run.ticket,
            "classification": None,
            "severity": None,
            "completed_nodes": [],
        },
    )

    classification_data = graph_result["classification"]
    severity_data = graph_result["severity"]

    if classification_data is None or severity_data is None:
        raise RuntimeError(
            "LangGraph did not produce classification and severity results.",
        )

    classification = ClassificationResult.model_validate(
        classification_data,
    )
    severity = SeverityResult.model_validate(severity_data)

    classification_started_at = datetime.now(UTC)

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

    evidence_assessment_started_at = datetime.now(UTC)

    evidence_assessment = assess_evidence(
        issue_type=classification.issue_type,
        knowledge_result_count=len(knowledge_articles),
        order_result_count=len(customer_orders),
    )

    evidence_assessment_step = AgentStep(
        agent_run=agent_run,
        sequence_number=5,
        step_type=AgentStepType.EVIDENCE_ASSESSMENT,
        status=AgentStepStatus.COMPLETED,
        input_data={
            "issue_type": classification.issue_type.value,
            "knowledge_result_count": len(knowledge_articles),
            "order_result_count": len(customer_orders),
        },
        output_data=evidence_assessment.model_dump(mode="json"),
        evidence=[
            {
                "source": "knowledge_search",
                "result_count": len(knowledge_articles),
            },
            {
                "source": "order_lookup",
                "result_count": len(customer_orders),
            },
        ],
        confidence=evidence_assessment.confidence,
        started_at=evidence_assessment_started_at,
        completed_at=datetime.now(UTC),
    )

    response_draft_started_at = datetime.now(UTC)

    response_draft = draft_support_response(
        ticket=agent_run.ticket,
        issue_type=classification.issue_type,
        knowledge_articles=knowledge_articles,
        customer_orders=customer_orders,
        evidence_is_sufficient=evidence_assessment.is_sufficient,
    )

    response_draft_step = AgentStep(
        agent_run=agent_run,
        sequence_number=6,
        step_type=AgentStepType.RESPONSE_DRAFT,
        status=AgentStepStatus.COMPLETED,
        input_data={
            "issue_type": classification.issue_type.value,
            "evidence_is_sufficient": evidence_assessment.is_sufficient,
            "knowledge_article_ids": [str(article.id) for article in knowledge_articles],
            "order_ids": [str(order.id) for order in customer_orders],
        },
        output_data=response_draft.model_dump(mode="json"),
        evidence=[
            {
                "source": "knowledge_article",
                "id": str(article.id),
                "title": article.title,
            }
            for article in knowledge_articles
        ]
        + [
            {
                "source": "customer_order",
                "id": str(order.id),
                "order_number": order.order_number,
            }
            for order in customer_orders
        ],
        confidence=0.9 if response_draft.was_drafted else 0.0,
        started_at=response_draft_started_at,
        completed_at=datetime.now(UTC),
    )

    escalation_started_at = datetime.now(UTC)

    escalation_decision = decide_escalation(
        severity=severity.severity,
        evidence_is_sufficient=evidence_assessment.is_sufficient,
        response_was_drafted=response_draft.was_drafted,
    )

    escalation_step = AgentStep(
        agent_run=agent_run,
        sequence_number=7,
        step_type=AgentStepType.ESCALATION_DECISION,
        status=AgentStepStatus.COMPLETED,
        input_data={
            "severity": severity.severity.value,
            "evidence_is_sufficient": evidence_assessment.is_sufficient,
            "response_was_drafted": response_draft.was_drafted,
        },
        output_data=escalation_decision.model_dump(mode="json"),
        evidence=[],
        confidence=escalation_decision.confidence,
        started_at=escalation_started_at,
        completed_at=datetime.now(UTC),
    )

    agent_run.drafted_response = response_draft.drafted_response
    agent_run.recommendation = escalation_decision.recommendation
    agent_run.confidence = escalation_decision.confidence
    agent_run.status = AgentRunStatus.COMPLETED
    agent_run.completed_at = datetime.now(UTC)

    session.add_all(
        [
            classification_step,
            severity_step,
            knowledge_step,
            order_lookup_step,
            evidence_assessment_step,
            response_draft_step,
            escalation_step,
        ],
    )
    await session.commit()

    refreshed_statement = (
        select(AgentRun).options(selectinload(AgentRun.steps)).where(AgentRun.id == agent_run_id)
    )

    refreshed_result = await session.execute(refreshed_statement)

    return refreshed_result.scalar_one()
