import os

import pytest

from app.db.session import check_database_connection

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_INTEGRATION_TESTS") != "1",
        reason="Set RUN_INTEGRATION_TESTS=1 to run database tests.",
    ),
]


@pytest.mark.asyncio
async def test_database_connection() -> None:
    await check_database_connection()
