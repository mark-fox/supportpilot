import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models import (
    KnowledgeCategory,
    OrderStatus,
    TicketPriority,
    TicketStatus,
)


class CustomerSummary(BaseModel):
    """Customer information included with a ticket response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str


class OrderSummary(BaseModel):
    """Order context included with a detailed ticket response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_number: str
    status: OrderStatus
    total_cents: int
    tracking_number: str | None
    created_at: datetime


class KnowledgeArticleSummary(BaseModel):
    """Approved knowledge article returned by a support search."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    category: KnowledgeCategory
    content: str


class KnowledgeSearchResponse(BaseModel):
    """Structured results returned by the knowledge search tool."""

    query: str
    results: list[KnowledgeArticleSummary]


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


class TicketDetail(TicketSummary):
    """Complete ticket information used by the support workspace."""

    customer_orders: list[OrderSummary]
