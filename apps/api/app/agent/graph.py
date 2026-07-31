import uuid
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agent.classification import ClassificationResult, classify_ticket
from app.agent.severity import assess_ticket_severity
from app.models import Ticket


class SupportWorkflowState(TypedDict):
    """Shared state passed between SupportPilot workflow nodes."""

    agent_run_id: uuid.UUID
    ticket: Ticket
    classification: dict | None
    severity: dict | None
    completed_nodes: list[str]


def run_classification(
    state: SupportWorkflowState,
) -> dict[str, dict | list[str]]:
    """Classify the support ticket and update workflow state."""

    classification = classify_ticket(state["ticket"])

    return {
        "classification": classification.model_dump(mode="json"),
        "completed_nodes": [
            *state["completed_nodes"],
            "classification",
        ],
    }


def run_severity_assessment(
    state: SupportWorkflowState,
) -> dict[str, dict | list[str]]:
    """Assess severity using the classification result."""

    classification_data = state["classification"]

    if classification_data is None:
        raise ValueError(
            "Classification must complete before severity assessment.",
        )

    classification = ClassificationResult.model_validate(
        classification_data,
    )

    severity = assess_ticket_severity(
        ticket=state["ticket"],
        issue_type=classification.issue_type,
    )

    return {
        "severity": severity.model_dump(mode="json"),
        "completed_nodes": [
            *state["completed_nodes"],
            "severity_assessment",
        ],
    }


def record_knowledge_search(
    state: SupportWorkflowState,
) -> dict[str, list[str]]:
    """Temporarily record the knowledge-search node."""

    return {
        "completed_nodes": [
            *state["completed_nodes"],
            "knowledge_search",
        ],
    }


def record_order_lookup(
    state: SupportWorkflowState,
) -> dict[str, list[str]]:
    """Temporarily record the order-lookup node."""

    return {
        "completed_nodes": [
            *state["completed_nodes"],
            "order_lookup",
        ],
    }


def record_evidence_assessment(
    state: SupportWorkflowState,
) -> dict[str, list[str]]:
    """Temporarily record the evidence-assessment node."""

    return {
        "completed_nodes": [
            *state["completed_nodes"],
            "evidence_assessment",
        ],
    }


def record_response_draft(
    state: SupportWorkflowState,
) -> dict[str, list[str]]:
    """Temporarily record the response-draft node."""

    return {
        "completed_nodes": [
            *state["completed_nodes"],
            "response_draft",
        ],
    }


def record_escalation_decision(
    state: SupportWorkflowState,
) -> dict[str, list[str]]:
    """Temporarily record the escalation-decision node."""

    return {
        "completed_nodes": [
            *state["completed_nodes"],
            "escalation_decision",
        ],
    }


def build_support_workflow():
    """Build and compile the SupportPilot workflow graph."""

    builder = StateGraph(SupportWorkflowState)

    builder.add_node("classification", run_classification)
    builder.add_node(
        "severity_assessment",
        run_severity_assessment,
    )
    builder.add_node("knowledge_search", record_knowledge_search)
    builder.add_node("order_lookup", record_order_lookup)
    builder.add_node(
        "evidence_assessment",
        record_evidence_assessment,
    )
    builder.add_node("response_draft", record_response_draft)
    builder.add_node(
        "escalation_decision",
        record_escalation_decision,
    )

    builder.add_edge(START, "classification")
    builder.add_edge("classification", "severity_assessment")
    builder.add_edge("severity_assessment", "knowledge_search")
    builder.add_edge("knowledge_search", "order_lookup")
    builder.add_edge("order_lookup", "evidence_assessment")
    builder.add_edge("evidence_assessment", "response_draft")
    builder.add_edge("response_draft", "escalation_decision")
    builder.add_edge("escalation_decision", END)

    return builder.compile()


support_workflow = build_support_workflow()
