import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import KnowledgeArticle, KnowledgeCategory
from app.services.knowledge import search_knowledge_articles


@pytest.mark.asyncio
async def test_search_knowledge_articles_returns_matching_articles() -> None:
    article = KnowledgeArticle(
        id=uuid.uuid4(),
        title="Package marked delivered but missing",
        category=KnowledgeCategory.SHIPPING,
        content="Wait 24 hours before escalating for a carrier claim.",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.scalars.return_value.all.return_value = [article]
    session.execute.return_value = result

    articles = await search_knowledge_articles(
        session=session,
        query="delivered",
    )

    assert len(articles) == 1
    assert articles[0].title == "Package marked delivered but missing"

    statement = session.execute.call_args.args[0]
    assert statement._limit_clause.value == 3


@pytest.mark.asyncio
async def test_search_knowledge_articles_returns_empty_for_blank_query() -> None:
    session = AsyncMock(spec=AsyncSession)

    articles = await search_knowledge_articles(
        session=session,
        query="   ",
    )

    assert articles == []
    session.execute.assert_not_awaited()
