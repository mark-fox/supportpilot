import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db_session
from app.models import Order, Ticket
from app.schemas import TicketDetail, TicketSummary

router = APIRouter(
    prefix="/tickets",
    tags=["tickets"],
)


@router.get("", response_model=list[TicketSummary])
async def list_tickets(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[Ticket]:
    """Return all support tickets with their associated customer."""

    statement = (
        select(Ticket).options(selectinload(Ticket.customer)).order_by(Ticket.created_at.desc())
    )

    result = await session.execute(statement)

    return list(result.scalars().all())


@router.get("/{ticket_id}", response_model=TicketDetail)
async def get_ticket(
    ticket_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TicketDetail:
    """Return one support ticket with customer and order context."""

    ticket_statement = (
        select(Ticket).options(selectinload(Ticket.customer)).where(Ticket.id == ticket_id)
    )

    ticket_result = await session.execute(ticket_statement)
    ticket = ticket_result.scalar_one_or_none()

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    orders_statement = (
        select(Order)
        .where(Order.customer_id == ticket.customer_id)
        .order_by(Order.created_at.desc())
    )

    orders_result = await session.execute(orders_statement)
    orders = list(orders_result.scalars().all())

    return TicketDetail(
        id=ticket.id,
        subject=ticket.subject,
        description=ticket.description,
        status=ticket.status,
        priority=ticket.priority,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        customer=ticket.customer,
        customer_orders=orders,
    )
