import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order


async def lookup_customer_orders(
    session: AsyncSession,
    customer_id: uuid.UUID,
    order_number: str | None = None,
    limit: int = 5,
) -> list[Order]:
    """Return constrained order context for one customer."""

    statement = select(Order).where(Order.customer_id == customer_id)

    if order_number is not None:
        normalized_order_number = order_number.strip()

        if not normalized_order_number:
            return []

        statement = statement.where(
            Order.order_number == normalized_order_number,
        )

    statement = statement.order_by(Order.created_at.desc()).limit(limit)

    result = await session.execute(statement)

    return list(result.scalars().all())
