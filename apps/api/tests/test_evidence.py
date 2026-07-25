from app.agent.classification import IssueType
from app.agent.evidence import assess_evidence


def test_assess_evidence_accepts_complete_context() -> None:
    result = assess_evidence(
        issue_type=IssueType.BILLING,
        knowledge_result_count=1,
        order_result_count=1,
    )

    assert result.is_sufficient is True
    assert result.confidence == 0.95
    assert result.missing_evidence == []


def test_assess_evidence_requires_approved_knowledge() -> None:
    result = assess_evidence(
        issue_type=IssueType.SHIPPING,
        knowledge_result_count=0,
        order_result_count=1,
    )

    assert result.is_sufficient is False
    assert result.confidence == 0.9
    assert result.missing_evidence == ["approved knowledge article"]


def test_assess_evidence_requires_order_context() -> None:
    result = assess_evidence(
        issue_type=IssueType.BILLING,
        knowledge_result_count=1,
        order_result_count=0,
    )

    assert result.is_sufficient is False
    assert result.missing_evidence == ["customer order context"]


def test_assess_evidence_rejects_unsupported_classification() -> None:
    result = assess_evidence(
        issue_type=IssueType.OTHER,
        knowledge_result_count=0,
        order_result_count=0,
    )

    assert result.is_sufficient is False
    assert result.missing_evidence == [
        "supported issue classification",
        "approved knowledge article",
        "customer order context",
    ]
