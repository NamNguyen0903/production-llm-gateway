from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    digest_api_key,
    generate_api_key,
    get_api_key_prefix,
)
from app.db.models.api_key import ApiKey
from app.repositories.api_key_repository import ApiKeyRepository
from app.services.authentication_service import (
    AuthenticationService,
    InvalidApiKeyError,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

TEST_SECRET = "b" * 64


async def test_create_authenticate_and_revoke(
    db_session: AsyncSession,
) -> None:
    repository = ApiKeyRepository(db_session)
    raw_key = generate_api_key()
    digest = digest_api_key(raw_key, secret=TEST_SECRET)

    record = await repository.create(
        name="integration-client",
        key_prefix=get_api_key_prefix(raw_key),
        key_digest=digest,
        expires_at=None,
    )
    api_key_id = record.id
    await db_session.commit()

    # Buộc lần đọc tiếp theo lấy dữ liệu từ database.
    db_session.expunge_all()

    stored = await repository.get_by_digest(digest)

    assert stored is not None
    assert stored.id == api_key_id
    assert stored.key_digest == digest
    assert stored.key_digest != raw_key
    assert not hasattr(stored, "raw_key")

    service = AuthenticationService(
        repository,
        hmac_secret=TEST_SECRET,
    )
    identity = await service.authenticate(raw_key)
    assert identity.id == api_key_id

    revoked_at = datetime.now(UTC)
    assert await repository.revoke(
        api_key_id=api_key_id,
        revoked_at=revoked_at,
    )
    await db_session.commit()

    # Revoke lại phải giữ nguyên thời điểm thu hồi ban đầu.
    assert await repository.revoke(
        api_key_id=api_key_id,
        revoked_at=revoked_at + timedelta(hours=1),
    )
    await db_session.commit()
    db_session.expunge_all()

    stored = await db_session.get(ApiKey, api_key_id)

    assert stored is not None
    assert stored.status == "revoked"
    assert stored.revoked_at == revoked_at

    with pytest.raises(InvalidApiKeyError):
        await service.authenticate(raw_key)


async def test_duplicate_digest_is_rejected(
    db_session: AsyncSession,
) -> None:
    repository = ApiKeyRepository(db_session)
    raw_key = generate_api_key()
    digest = digest_api_key(raw_key, secret=TEST_SECRET)

    await repository.create(
        name="first",
        key_prefix=get_api_key_prefix(raw_key),
        key_digest=digest,
        expires_at=None,
    )
    await db_session.commit()

    with pytest.raises(IntegrityError):
        async with db_session.begin_nested():
            await repository.create(
                name="duplicate",
                key_prefix=get_api_key_prefix(raw_key),
                key_digest=digest,
                expires_at=None,
            )


async def test_revoke_unknown_uuid_returns_false(
    db_session: AsyncSession,
) -> None:
    repository = ApiKeyRepository(db_session)

    found = await repository.revoke(
        api_key_id=uuid4(),
        revoked_at=datetime.now(UTC),
    )

    assert found is False
