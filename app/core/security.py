import hashlib
import hmac
import re
import secrets

API_KEY_PREFIX = "gw_"
API_KEY_RANDOM_BYTES = 32
API_KEY_DISPLAY_PREFIX_LENGTH = 12

_API_KEY_PATTERN = re.compile(r"gw_[0-9a-f]{64}")


def generate_api_key() -> str:
    return API_KEY_PREFIX + secrets.token_hex(API_KEY_RANDOM_BYTES)


def is_valid_api_key_format(raw_key: str) -> bool:
    return _API_KEY_PATTERN.fullmatch(raw_key) is not None


def digest_api_key(raw_key: str, *, secret: str) -> str:
    if not is_valid_api_key_format(raw_key):
        raise ValueError("Invalid API key format.")

    if len(secret.encode("utf-8")) < 32:
        raise ValueError("API key HMAC secret must contain at least 32 bytes.")

    return hmac.new(
        key=secret.encode("utf-8"),
        msg=raw_key.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


def get_api_key_prefix(raw_key: str) -> str:
    if not is_valid_api_key_format(raw_key):
        raise ValueError("Invalid API key format.")

    return raw_key[:API_KEY_DISPLAY_PREFIX_LENGTH]
