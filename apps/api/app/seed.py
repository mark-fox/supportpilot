import asyncio
import sys

from sqlalchemy import select

from app.database import async_session_factory
from app.models import (
    Customer,
    KnowledgeArticle,
    KnowledgeCategory,
    Order,
    OrderStatus,
    Ticket,
    TicketPriority,
)


async def seed_database() -> None:
    """Insert initial development data when the database is empty."""

    async with async_session_factory() as session:
        existing_ticket = await session.scalar(select(Ticket.id).limit(1))

        if existing_ticket is not None:
            print("Seed skipped: support tickets already exist.")
            return

        maya = Customer(
            full_name="Maya Thompson",
            email="maya.thompson@example.com",
        )
        daniel = Customer(
            full_name="Daniel Kim",
            email="daniel.kim@example.com",
        )
        priya = Customer(
            full_name="Priya Shah",
            email="priya.shah@example.com",
        )

        tickets = [
            Ticket(
                customer=maya,
                subject="Duplicate charge on my latest order",
                description=(
                    "I placed one order yesterday, but my card appears to have been "
                    "charged twice. Both charges are still showing as pending. Please "
                    "confirm whether I will be billed twice."
                ),
                priority=TicketPriority.HIGH,
            ),
            Ticket(
                customer=daniel,
                subject="Package marked delivered but not received",
                description=(
                    "The tracking page says my package was delivered this afternoon, "
                    "but it is not at my front door or mailbox. I also checked with my "
                    "neighbors and they do not have it."
                ),
                priority=TicketPriority.URGENT,
            ),
            Ticket(
                customer=priya,
                subject="How do I update my billing address?",
                description=(
                    "I recently moved and need to change the billing address saved on "
                    "my account before placing another order."
                ),
                priority=TicketPriority.NORMAL,
            ),
        ]

        orders = [
            Order(
                customer=maya,
                order_number="SP-10482",
                status=OrderStatus.PROCESSING,
                total_cents=12999,
            ),
            Order(
                customer=daniel,
                order_number="SP-10477",
                status=OrderStatus.DELIVERED,
                total_cents=8499,
                tracking_number="1Z999AA10123456784",
            ),
            Order(
                customer=priya,
                order_number="SP-10391",
                status=OrderStatus.DELIVERED,
                total_cents=4599,
                tracking_number="9400111899223856928499",
            ),
        ]

        knowledge_articles = [
            KnowledgeArticle(
                title="Pending and duplicate card charges",
                category=KnowledgeCategory.BILLING,
                content=(
                    "A customer may temporarily see more than one pending card charge "
                    "when a payment authorization is retried. Pending authorizations "
                    "normally disappear within three to five business days. Support "
                    "must verify the related order before promising a refund. If more "
                    "than one charge has fully posted, escalate the case to billing."
                ),
            ),
            KnowledgeArticle(
                title="Package marked delivered but missing",
                category=KnowledgeCategory.SHIPPING,
                content=(
                    "Ask the customer to check entrances, parcel lockers, household "
                    "members, and nearby neighbors. Carriers may mark a package as "
                    "delivered several hours before arrival. If the package remains "
                    "missing after 24 hours, escalate the ticket for a carrier claim "
                    "or replacement review."
                ),
            ),
            KnowledgeArticle(
                title="Updating an account billing address",
                category=KnowledgeCategory.ACCOUNT,
                content=(
                    "Customers can update their saved billing address from Account "
                    "Settings under Payment and Billing. Changing the saved address "
                    "does not alter orders that have already been submitted."
                ),
            ),
        ]

        session.add_all([*tickets, *orders, *knowledge_articles])
        await session.commit()

        print(
            f"Seed complete: created {len(tickets)} support tickets, "
            f"{len(orders)} orders, and "
            f"{len(knowledge_articles)} knowledge articles."
        )


if __name__ == "__main__":
    if sys.platform == "win32":
        with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
            runner.run(seed_database())
    else:
        asyncio.run(seed_database())
