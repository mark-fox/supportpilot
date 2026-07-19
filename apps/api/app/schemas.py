import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models import TicketPriority, TicketStatus


class CustomerSummary(BaseModel):
    """Customer information included with a ticket response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str


class TicketSummary(BaseModel):
    """Ticket information returned by the ticket queue endpoint."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subject: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    created_at: datetime
    updated_at: datetime
    customer: CustomerSummary
