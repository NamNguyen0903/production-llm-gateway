import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_database_connection(db_session: AsyncSession) -> None:
    result = await db_session.scalar(text("SELECT 1"))

    assert result == 1
