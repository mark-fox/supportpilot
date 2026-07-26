from app.agent.escalation import decide_escalation
from app.agent.severity import SeverityLevel
from app.models import AgentRecommendation


def test_decide_escalation_returns_human_review_for_grounded_draft() -> None:
    result = decide_escalation(
        severity=SeverityLevel.HIGH,
        evidence_is_sufficient=True,
        response_was_drafted=True,
    )

    assert result.recommendation == AgentRecommendation.HUMAN_REVIEW
    assert result.confidence == 0.95


def test_decide_escalation_escalates_missing_evidence() -> None:
    result = decide_escalation(
        severity=SeverityLevel.MEDIUM,
        evidence_is_sufficient=False,
        response_was_drafted=False,
    )

    assert result.recommendation == AgentRecommendation.ESCALATE
    assert result.confidence == 0.95


def test_decide_escalation_escalates_missing_draft() -> None:
    result = decide_escalation(
        severity=SeverityLevel.LOW,
        evidence_is_sufficient=True,
        response_was_drafted=False,
    )

    assert result.recommendation == AgentRecommendation.ESCALATE
    assert result.confidence == 0.95


def test_decide_escalation_escalates_critical_case() -> None:
    result = decide_escalation(
        severity=SeverityLevel.CRITICAL,
        evidence_is_sufficient=True,
        response_was_drafted=True,
    )

    assert result.recommendation == AgentRecommendation.ESCALATE
    assert result.confidence == 0.9
