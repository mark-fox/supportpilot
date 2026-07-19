from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.routes.tickets import router as tickets_router

app = FastAPI(
    title="SupportPilot API",
    description="Backend services for the SupportPilot support operations platform.",
    version="0.1.0",
)

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
