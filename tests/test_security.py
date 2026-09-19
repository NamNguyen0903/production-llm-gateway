import hashlib
import hmac

import pytest

from app.core.security import (
    digest_api_key,
    generate_api_key,
    get_api_key_prefix,
    is_valid_api_key_format,
)

TEST_SECRET = "a" * 64
TEST_KEY = "gw_" + "b" * 64


def test_generated_key_has_expected_format() -> None:
    raw_key = generate_api_key()

    assert raw_key.startswith("gw_")
    assert len(raw_key) == 67
    assert is_valid_api_key_format(raw_key)


def test_generated_keys_differ() -> None:
    assert generate_api_key() != generate_api_key()


@pytest.mark.parametrize(
    "raw_key",
    [
        "",
        "gw_",
        "gw_" + "a" * 63,
        "gw_" + "a" * 65,
        "gw_" + "z" * 64,
        "wrong_" + "a" * 64,
        " " + TEST_KEY,
        TEST_KEY + "\n",
    ],
)
def test_invalid_key_format_is_rejected(raw_key: str) -> None:
    assert not is_valid_api_key_format(raw_key)


def test_digest_matches_hmac_sha256() -> None:
    expected = hmac.new(
        TEST_SECRET.encode("utf-8"),
        TEST_KEY.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    actual = digest_api_key(TEST_KEY, secret=TEST_SECRET)

    assert actual == expected
    assert len(actual) == 64


def test_digest_is_deterministic() -> None:
    first = digest_api_key(TEST_KEY, secret=TEST_SECRET)
    second = digest_api_key(TEST_KEY, secret=TEST_SECRET)

    assert first == second


def test_secret_changes_digest() -> None:
    first = digest_api_key(TEST_KEY, secret=TEST_SECRET)
    second = digest_api_key(TEST_KEY, secret="c" * 64)

    assert first != second


def test_key_changes_digest() -> None:
    first = digest_api_key(TEST_KEY, secret=TEST_SECRET)
    second = digest_api_key("gw_" + "d" * 64, secret=TEST_SECRET)

    assert first != second


def test_digest_rejects_short_secret() -> None:
    with pytest.raises(ValueError, match="at least 32 bytes"):
        digest_api_key(TEST_KEY, secret="short")


def test_digest_rejects_invalid_key() -> None:
    with pytest.raises(ValueError, match="Invalid API key format"):
        digest_api_key("invalid", secret=TEST_SECRET)


def test_display_prefix_is_not_the_full_key() -> None:
    prefix = get_api_key_prefix(TEST_KEY)

    assert prefix == TEST_KEY[:12]
    assert len(prefix) == 12
    assert prefix != TEST_KEY
