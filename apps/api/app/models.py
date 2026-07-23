import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SupportPilot database models."""


class TicketStatus(StrEnum):
    """Current lifecycle state of a support ticket."""

    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class TicketPriority(StrEnum):
    """Operational priority assigned to a support ticket."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class OrderStatus(StrEnum):
    """Current fulfillment state of a customer order."""

    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class KnowledgeCategory(StrEnum):
    """Category used to organize support knowledge articles."""

    BILLING = "billing"
    SHIPPING = "shipping"
    ACCOUNT = "account"
    RETURNS = "returns"


class AgentRunStatus(StrEnum):
    """Current lifecycle state of an agent run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRecommendation(StrEnum):
    """Final action recommended by the agent."""

    HUMAN_REVIEW = "human_review"
    ESCALATE = "escalate"


class AgentStepType(StrEnum):
    """Supported stages in the ticket-processing workflow."""

    CLASSIFICATION = "classification"
    SEVERITY_ASSESSMENT = "severity_assessment"
    KNOWLEDGE_SEARCH = "knowledge_search"
    CUSTOMER_LOOKUP = "customer_lookup"
    ORDER_LOOKUP = "order_lookup"
    EVIDENCE_ASSESSMENT = "evidence_assessment"
    RESPONSE_DRAFT = "response_draft"
    ESCALATION_DECISION = "escalation_decision"


class AgentStepStatus(StrEnum):
    """Execution state of one agent workflow step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Customer(Base):
    """A customer who can submit one or more support tickets."""

    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
    )

    orders: Mapped[list["Order"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
    )


class Ticket(Base):
    """A customer support ticket processed by SupportPilot."""

    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[TicketStatus] = mapped_column(
        Enum(
            TicketStatus,
            name="ticket_status",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
        default=TicketStatus.OPEN,
        server_default=TicketStatus.OPEN.value,
        index=True,
    )
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(
            TicketPriority,
            name="ticket_priority",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
        default=TicketPriority.NORMAL,
        server_default=TicketPriority.NORMAL.value,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    customer: Mapped[Customer] = relationship(
        back_populates="tickets",
    )

    agent_runs: Mapped[list["AgentRun"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
    )


class Order(Base):
    """A customer order that may provide context for a support ticket."""

    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(
            OrderStatus,
            name="order_status",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
        index=True,
    )
    total_cents: Mapped[int] = mapped_column(
        nullable=False,
    )
    tracking_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    customer: Mapped[Customer] = relationship(
        back_populates="orders",
    )


class KnowledgeArticle(Base):
    """An approved support article available to the agent."""

    __tablename__ = "knowledge_articles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
    )
    category: Mapped[KnowledgeCategory] = mapped_column(
        Enum(
            KnowledgeCategory,
            name="knowledge_category",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        server_default="true",
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class AgentRun(Base):
    """One traceable execution of the support agent for a ticket."""

    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[AgentRunStatus] = mapped_column(
        Enum(
            AgentRunStatus,
            name="agent_run_status",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
        default=AgentRunStatus.PENDING,
        server_default=AgentRunStatus.PENDING.value,
        index=True,
    )
    recommendation: Mapped[AgentRecommendation | None] = mapped_column(
        Enum(
            AgentRecommendation,
            name="agent_recommendation",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=True,
    )
    confidence: Mapped[float | None] = mapped_column(
        nullable=True,
    )
    drafted_response: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    ticket: Mapped[Ticket] = relationship(
        back_populates="agent_runs",
    )
    steps: Mapped[list["AgentStep"]] = relationship(
        back_populates="agent_run",
        cascade="all, delete-orphan",
        order_by="AgentStep.sequence_number",
    )


class AgentStep(Base):
    """One auditable step within an agent run."""

    __tablename__ = "agent_steps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    step_type: Mapped[AgentStepType] = mapped_column(
        Enum(
            AgentStepType,
            name="agent_step_type",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
        index=True,
    )
    status: Mapped[AgentStepStatus] = mapped_column(
        Enum(
            AgentStepStatus,
            name="agent_step_status",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
        default=AgentStepStatus.PENDING,
        server_default=AgentStepStatus.PENDING.value,
    )
    input_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    output_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    evidence: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )
    confidence: Mapped[float | None] = mapped_column(
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    agent_run: Mapped[AgentRun] = relationship(
        back_populates="steps",
    )
