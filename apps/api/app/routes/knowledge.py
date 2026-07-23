from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.schemas import KnowledgeSearchResponse
from app.services.knowledge import search_knowledge_articles

router = APIRouter(
    prefix="/knowledge",
    tags=["knowledge"],
)


@router.get("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    query: Annotated[
        str,
        Query(
            min_length=2,
            max_length=200,
            description="Support issue or policy phrase to search for.",
        ),
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> KnowledgeSearchResponse:
    """Search approved support knowledge articles."""

    results = await search_knowledge_articles(
        session=session,
        query=query,
    )

    return KnowledgeSearchResponse(
        query=query,
        results=results,
    )
