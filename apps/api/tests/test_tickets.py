import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.main import app
from app.models import Customer, Ticket, TicketPriority, TicketStatus

client = TestClient(app)


def create_test_ticket() -> Ticket:
    """Create an in-memory ticket for API response tests."""

    customer = Customer(
        id=uuid.uuid4(),
        full_name="Maya Thompson",
        email="maya.thompson@example.com",
        created_at=datetime.now(UTC),
    )

    return Ticket(
        id=uuid.uuid4(),
        customer_id=customer.id,
        customer=customer,
        subject="Duplicate charge on my latest order",
        description="My card appears to have been charged twice.",
        status=TicketStatus.OPEN,
        priority=TicketPriority.HIGH,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def override_database_session(
    session: AsyncSession,
):
    """Create a FastAPI dependency override for a mocked session."""

    async def override() -> AsyncGenerator[AsyncSession, None]:
        yield session

    return override


def test_get_ticket_returns_ticket_with_customer() -> None:
    ticket = create_test_ticket()

    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.scalar_one_or_none.return_value = ticket
    session.execute.return_value = result

    app.dependency_overrides[get_db_session] = override_database_session(session)

    try:
        response = client.get(f"/tickets/{ticket.id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == str(ticket.id)
    assert body["subject"] == ticket.subject
    assert body["status"] == "open"
    assert body["priority"] == "high"
    assert body["customer"]["full_name"] == "Maya Thompson"


def test_get_ticket_returns_not_found() -> None:
    ticket_id = uuid.uuid4()

    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result

    app.dependency_overrides[get_db_session] = override_database_session(session)

    try:
        response = client.get(f"/tickets/{ticket_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Ticket not found"}
