import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.schemas import OrderLookupResponse
from app.services.orders import lookup_customer_orders

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
)


@router.get("/lookup", response_model=OrderLookupResponse)
async def lookup_orders(
    customer_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    order_number: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=50,
            description="Optional exact order number.",
        ),
    ] = None,
) -> OrderLookupResponse:
    """Look up order context belonging to one customer."""

    results = await lookup_customer_orders(
        session=session,
        customer_id=customer_id,
        order_number=order_number,
    )

    return OrderLookupResponse(
        customer_id=customer_id,
        order_number=order_number,
        results=results,
    )
