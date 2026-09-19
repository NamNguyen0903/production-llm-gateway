from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from pydantic import SecretStr
from sqlalchemy.exc import SQLAlchemyError

from app.cli import api_keys

TEST_KEY = "gw_" + "a" * 64


@pytest.mark.asyncio
@pytest.mark.parametrize("commit_fails", [False, True])
async def test_create_key_prints_only_after_commit(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    commit_fails: bool,
) -> None:
    settings = SimpleNamespace(
        api_key_hmac_secret=SecretStr("b" * 64),
    )
    monkeypatch.setattr(api_keys, "get_settings", lambda: settings)
    monkeypatch.setattr(api_keys, "generate_api_key", lambda: TEST_KEY)

    session = MagicMock()
    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=session)
    session_context.__aexit__ = AsyncMock(return_value=False)

    transaction = MagicMock()
    transaction.__aenter__ = AsyncMock()

    async def exit_transaction(*args: object) -> bool:
        # Trước khi commit hoàn tất, không được in raw key.
        assert TEST_KEY not in capsys.readouterr().out

        if commit_fails:
            raise SQLAlchemyError("simulated commit failure")

        return False

    transaction.__aexit__ = AsyncMock(side_effect=exit_transaction)
    session.begin.return_value = transaction

    monkeypatch.setattr(
        api_keys,
        "async_session_factory",
        lambda: session_context,
    )

    repository = MagicMock()
    repository.create = AsyncMock(
        return_value=SimpleNamespace(id=uuid4()),
    )
    monkeypatch.setattr(
        api_keys,
        "ApiKeyRepository",
        lambda session: repository,
    )

    if commit_fails:
        with pytest.raises(SQLAlchemyError):
            await api_keys.create_key(name="test-cli", expires_in_days=30)

        assert TEST_KEY not in capsys.readouterr().out
    else:
        await api_keys.create_key(name="test-cli", expires_in_days=30)

        assert capsys.readouterr().out.count(TEST_KEY) == 1

    create_arguments = repository.create.call_args.kwargs
    assert "raw_key" not in create_arguments
    assert create_arguments["key_digest"] != TEST_KEY
    assert len(create_arguments["key_digest"]) == 64
