import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.main import app
from app.models import AgentRun, AgentRunStatus
from app.services.agent_runs import create_agent_run

client = TestClient(app)


def override_database_session(
    session: AsyncSession,
):
    """Create a FastAPI dependency override for a mocked session."""

    async def override() -> AsyncGenerator[AsyncSession, None]:
        yield session

    return override


@pytest.mark.asyncio
async def test_create_agent_run_persists_pending_run() -> None:
    ticket_id = uuid.uuid4()
    session = AsyncMock(spec=AsyncSession)

    async def refresh_agent_run(agent_run: AgentRun) -> None:
        agent_run.id = uuid.uuid4()
        agent_run.created_at = datetime.now(UTC)

    session.refresh.side_effect = refresh_agent_run

    agent_run = await create_agent_run(
        session=session,
        ticket_id=ticket_id,
    )

    assert agent_run.ticket_id == ticket_id
    assert agent_run.status == AgentRunStatus.PENDING
    assert agent_run.recommendation is None
    assert agent_run.confidence is None
    assert agent_run.drafted_response is None

    session.add.assert_called_once_with(agent_run)
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(agent_run)


def test_start_agent_run_returns_created_run(monkeypatch: pytest.MonkeyPatch) -> None:
    ticket_id = uuid.uuid4()
    run_id = uuid.uuid4()
    created_at = datetime.now(UTC)

    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = ticket_id

    agent_run = AgentRun(
        id=run_id,
        ticket_id=ticket_id,
        status=AgentRunStatus.PENDING,
        created_at=created_at,
    )

    create_run_mock = AsyncMock(return_value=agent_run)

    monkeypatch.setattr(
        "app.routes.agent_runs.create_agent_run",
        create_run_mock,
    )

    app.dependency_overrides[get_db_session] = override_database_session(session)

    try:
        response = client.post(f"/tickets/{ticket_id}/agent-runs")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201

    body = response.json()

    assert body["id"] == str(run_id)
    assert body["ticket_id"] == str(ticket_id)
    assert body["status"] == "pending"
    assert body["recommendation"] is None

    create_run_mock.assert_awaited_once_with(
        session=session,
        ticket_id=ticket_id,
    )


def test_start_agent_run_returns_not_found() -> None:
    ticket_id = uuid.uuid4()

    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = None

    app.dependency_overrides[get_db_session] = override_database_session(session)

    try:
        response = client.post(f"/tickets/{ticket_id}/agent-runs")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Ticket not found"}
