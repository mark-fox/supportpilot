import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, OrderStatus
from app.services.orders import lookup_customer_orders


def create_test_order(customer_id: uuid.UUID) -> Order:
    """Create an in-memory order for lookup service tests."""

    return Order(
        id=uuid.uuid4(),
        customer_id=customer_id,
        order_number="SP-10482",
        status=OrderStatus.PROCESSING,
        total_cents=12999,
        tracking_number=None,
        created_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_lookup_customer_orders_returns_customer_orders() -> None:
    customer_id = uuid.uuid4()
    order = create_test_order(customer_id)

    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.scalars.return_value.all.return_value = [order]
    session.execute.return_value = result

    orders = await lookup_customer_orders(
        session=session,
        customer_id=customer_id,
    )

    assert orders == [order]

    statement = session.execute.call_args.args[0]
    assert statement._limit_clause.value == 5


@pytest.mark.asyncio
async def test_lookup_customer_orders_filters_by_order_number() -> None:
    customer_id = uuid.uuid4()
    order = create_test_order(customer_id)

    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.scalars.return_value.all.return_value = [order]
    session.execute.return_value = result

    orders = await lookup_customer_orders(
        session=session,
        customer_id=customer_id,
        order_number="SP-10482",
    )

    assert orders == [order]
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_customer_orders_rejects_blank_order_number() -> None:
    session = AsyncMock(spec=AsyncSession)

    orders = await lookup_customer_orders(
        session=session,
        customer_id=uuid.uuid4(),
        order_number="   ",
    )

    assert orders == []
    session.execute.assert_not_awaited()
