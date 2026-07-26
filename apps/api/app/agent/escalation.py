from pydantic import BaseModel, Field

from app.agent.severity import SeverityLevel
from app.models import AgentRecommendation


class EscalationDecisionResult(BaseModel):
    """Structured final recommendation produced by the agent."""

    recommendation: AgentRecommendation
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str


def decide_escalation(
    severity: SeverityLevel,
    evidence_is_sufficient: bool,
    response_was_drafted: bool,
) -> EscalationDecisionResult:
    """Choose whether a ticket is ready for review or requires escalation."""

    if not evidence_is_sufficient:
        return EscalationDecisionResult(
            recommendation=AgentRecommendation.ESCALATE,
            confidence=0.95,
            rationale=(
                "The case requires escalation because the workflow lacks "
                "sufficient grounded evidence."
            ),
        )

    if not response_was_drafted:
        return EscalationDecisionResult(
            recommendation=AgentRecommendation.ESCALATE,
            confidence=0.95,
            rationale=(
                "The case requires escalation because the workflow could not "
                "produce a supported response draft."
            ),
        )

    if severity == SeverityLevel.CRITICAL:
        return EscalationDecisionResult(
            recommendation=AgentRecommendation.ESCALATE,
            confidence=0.9,
            rationale=(
                "The case requires escalation because it was assessed as critical severity."
            ),
        )

    return EscalationDecisionResult(
        recommendation=AgentRecommendation.HUMAN_REVIEW,
        confidence=0.95,
        rationale=(
            "The workflow found sufficient evidence and produced a grounded "
            "draft that is ready for human review."
        ),
    )
