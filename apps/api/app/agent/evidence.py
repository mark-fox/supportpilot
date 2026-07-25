from pydantic import BaseModel, Field

from app.agent.classification import IssueType


class EvidenceAssessmentResult(BaseModel):
    """Structured assessment of the context collected by agent tools."""

    is_sufficient: bool
    confidence: float = Field(ge=0.0, le=1.0)
    missing_evidence: list[str]
    rationale: str


def assess_evidence(
    issue_type: IssueType,
    knowledge_result_count: int,
    order_result_count: int,
) -> EvidenceAssessmentResult:
    """Determine whether collected evidence supports a grounded response."""

    missing_evidence: list[str] = []

    if issue_type == IssueType.OTHER:
        missing_evidence.append("supported issue classification")

    if knowledge_result_count == 0:
        missing_evidence.append("approved knowledge article")

    if order_result_count == 0:
        missing_evidence.append("customer order context")

    if missing_evidence:
        return EvidenceAssessmentResult(
            is_sufficient=False,
            confidence=0.9,
            missing_evidence=missing_evidence,
            rationale=(
                f"The workflow is missing required evidence: {', '.join(missing_evidence)}."
            ),
        )

    return EvidenceAssessmentResult(
        is_sufficient=True,
        confidence=0.95,
        missing_evidence=[],
        rationale=(
            "The workflow found a supported classification, approved policy, "
            "and customer-specific order context."
        ),
    )
