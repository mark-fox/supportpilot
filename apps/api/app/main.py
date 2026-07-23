from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db_session
from app.routes.knowledge import router as knowledge_router
from app.routes.orders import router as orders_router
from app.routes.tickets import router as tickets_router

settings = get_settings()

app = FastAPI(
    title="SupportPilot API",
    description="Backend services for the SupportPilot support operations platform.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(knowledge_router)
app.include_router(orders_router)
app.include_router(tickets_router)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Return the current health status of the API."""
    return {"status": "healthy"}


@app.get("/health/database", tags=["system"])
async def database_health_check(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, str]:
    """Confirm that the API can communicate with PostgreSQL."""

    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection unavailable",
        ) from exc

    return {"status": "healthy", "database": "connected"}
