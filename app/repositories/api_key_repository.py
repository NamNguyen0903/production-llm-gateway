from datetime import datetime
from typing import cast
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.api_key import ApiKey


class ApiKeyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_digest(self, key_digest: str) -> ApiKey | None:
        statement = select(ApiKey).where(
            ApiKey.key_digest == key_digest,
        )

        return cast(
            ApiKey | None,
            await self._session.scalar(statement),
        )

    async def create(
        self,
        *,
        name: str,
        key_prefix: str,
        key_digest: str,
        expires_at: datetime | None,
    ) -> ApiKey:
        api_key = ApiKey(
            name=name,
            key_prefix=key_prefix,
            key_digest=key_digest,
            status="active",
            rate_limit_rpm=30,
            expires_at=expires_at,
        )

        self._session.add(api_key)
        await self._session.flush()

        return api_key

    async def revoke(
        self,
        *,
        api_key_id: UUID,
        revoked_at: datetime,
    ) -> bool:
        statement = (
            update(ApiKey)
            .where(
                ApiKey.id == api_key_id,
                ApiKey.status == "active",
            )
            .values(
                status="revoked",
                revoked_at=revoked_at,
            )
            .returning(ApiKey.id)
        )

        updated_id = await self._session.scalar(statement)

        if updated_id is not None:
            return True

        existing = await self._session.get(ApiKey, api_key_id)
        return existing is not None
