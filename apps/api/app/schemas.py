import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models import (
    AgentRecommendation,
    AgentRunStatus,
    AgentStepStatus,
    AgentStepType,
    HumanReviewAction,
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


class OrderLookupResponse(BaseModel):
    """Structured order context returned by the order lookup tool."""

    customer_id: uuid.UUID
    order_number: str | None
    results: list[OrderSummary]


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


class AgentRunSummary(BaseModel):
    """Summary of one traceable support-agent execution."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ticket_id: uuid.UUID
    status: AgentRunStatus
    recommendation: AgentRecommendation | None
    confidence: float | None
    drafted_response: str | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class AgentStepSummary(BaseModel):
    """One ordered, auditable step from an agent workflow."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sequence_number: int
    step_type: AgentStepType
    status: AgentStepStatus
    input_data: dict | None
    output_data: dict | None
    evidence: list | None
    confidence: float | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class AgentRunDetail(AgentRunSummary):
    """An agent run with its complete ordered workflow trace."""

    steps: list[AgentStepSummary]


class HumanReviewCreate(BaseModel):
    """Human decision submitted for a completed agent run."""

    action: HumanReviewAction
    reviewer_note: str | None = None
    revised_response: str | None = None


class HumanReviewSummary(BaseModel):
    """Saved human review decision."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_run_id: uuid.UUID
    action: HumanReviewAction
    reviewer_note: str | None
    revised_response: str | None
    created_at: datetime
