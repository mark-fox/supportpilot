import uuid

import pytest

from app.agent.graph import support_workflow


@pytest.mark.asyncio
async def test_support_workflow_executes_nodes_in_order() -> None:
    agent_run_id = uuid.uuid4()

    result = await support_workflow.ainvoke(
        {
            "agent_run_id": agent_run_id,
            "completed_nodes": [],
        },
    )

    assert result["agent_run_id"] == agent_run_id
    assert result["completed_nodes"] == [
        "classification",
        "severity_assessment",
        "knowledge_search",
        "order_lookup",
        "evidence_assessment",
        "response_draft",
        "escalation_decision",
    ]
