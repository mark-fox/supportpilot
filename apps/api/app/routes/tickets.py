from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db_session
from app.models import Ticket
from app.schemas import TicketSummary

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
