from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import KnowledgeArticle


async def search_knowledge_articles(
    session: AsyncSession,
    query: str,
    limit: int = 3,
) -> list[KnowledgeArticle]:
    """Search active approved knowledge articles using constrained text matching."""

    normalized_query = query.strip()

    if not normalized_query:
        return []

    search_pattern = f"%{normalized_query}%"

    statement = (
        select(KnowledgeArticle)
        .where(
            KnowledgeArticle.is_active.is_(True),
            or_(
                KnowledgeArticle.title.ilike(search_pattern),
                KnowledgeArticle.content.ilike(search_pattern),
            ),
        )
        .order_by(KnowledgeArticle.title)
        .limit(limit)
    )

    result = await session.execute(statement)

    return list(result.scalars().all())
