import argparse
import asyncio
import sys
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.security import (
    digest_api_key,
    generate_api_key,
    get_api_key_prefix,
)
from app.db.session import (
    async_session_factory,
    close_database_connection,
)
from app.repositories.api_key_repository import ApiKeyRepository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage Gateway API keys.")
    commands = parser.add_subparsers(dest="command", required=True)

    create_parser = commands.add_parser("create")
    create_parser.add_argument("--name", required=True)
    create_parser.add_argument("--expires-in-days", type=int, default=None)

    revoke_parser = commands.add_parser("revoke")
    revoke_parser.add_argument("--id", type=UUID, required=True)

    return parser


async def create_key(
    *,
    name: str,
    expires_in_days: int | None,
) -> None:
    settings = get_settings()

    if settings.api_key_hmac_secret is None:
        raise ValueError("API_KEY_HMAC_SECRET must be configured before creating API keys.")

    secret = settings.api_key_hmac_secret.get_secret_value()

    raw_key = generate_api_key()
    key_digest = digest_api_key(raw_key, secret=secret)

    expires_at = (
        datetime.now(UTC) + timedelta(days=expires_in_days) if expires_in_days is not None else None
    )

    async with async_session_factory() as session:
        async with session.begin():
            repository = ApiKeyRepository(session)

            api_key = await repository.create(
                name=name,
                key_prefix=get_api_key_prefix(raw_key),
                key_digest=key_digest,
                expires_at=expires_at,
            )

            api_key_id = api_key.id

    # Transaction đã commit trước khi hiển thị raw key.
    print(f"API key ID: {api_key_id}")
    print("Store this key securely. It will not be displayed again.")
    print(f"API key: {raw_key}")


async def revoke_key(api_key_id: UUID) -> int:
    async with async_session_factory() as session:
        async with session.begin():
            repository = ApiKeyRepository(session)

            found = await repository.revoke(
                api_key_id=api_key_id,
                revoked_at=datetime.now(UTC),
            )

    if not found:
        print("API key ID not found.", file=sys.stderr)
        return 1

    print(f"API key revoked: {api_key_id}")
    return 0


async def run_command(args: argparse.Namespace) -> int:
    try:
        if args.command == "create":
            await create_key(
                name=args.name,
                expires_in_days=args.expires_in_days,
            )
            return 0

        return await revoke_key(args.id)
    finally:
        await close_database_connection()


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "create":
        args.name = args.name.strip()

        if not 1 <= len(args.name) <= 100:
            parser.error("--name must contain 1 to 100 characters.")

        if args.expires_in_days is not None and not 1 <= args.expires_in_days <= 3650:
            parser.error("--expires-in-days must be between 1 and 3650.")

    try:
        return asyncio.run(run_command(args))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (SQLAlchemyError, OSError, TimeoutError):
        print(
            "Database operation failed. Check database availability.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
