import argparse
import asyncio
import getpass
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.rbac import Role
from app.models.user import User
from app.services.audit import record_audit
from app.services.users import DuplicateEmailError, create_user

MIN_PASSWORD_LENGTH = 12


async def create_admin_account(
    session_factory: async_sessionmaker,
    *,
    email: str,
    full_name: str,
    password: str,
) -> User:
    """Tạo tài khoản ADMIN đầu tiên. Ghi audit với actor là None vì đây là thao tác bootstrap."""
    async with session_factory() as session:
        user = await create_user(
            session,
            email=email,
            full_name=full_name,
            password=password,
            role=Role.ADMIN,
        )
        await record_audit(
            session,
            actor_id=None,
            action="user.create_admin_bootstrap",
            entity_type="user",
            entity_id=str(user.id),
            changes={"email": user.email},
        )
        await session.commit()
        return user


async def _run_create_admin(engine: AsyncEngine, email: str, full_name: str, password: str) -> int:
    try:
        user = await create_admin_account(
            async_sessionmaker(engine, expire_on_commit=False),
            email=email,
            full_name=full_name,
            password=password,
        )
    except DuplicateEmailError:
        print(f"Email {email} đã tồn tại")
        return 1
    finally:
        await engine.dispose()
    print(f"Đã tạo tài khoản ADMIN: {user.email}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pmis")
    subcommands = parser.add_subparsers(dest="command", required=True)
    admin_parser = subcommands.add_parser("create-admin", help="Tạo tài khoản ADMIN đầu tiên")
    admin_parser.add_argument("--email", required=True)
    admin_parser.add_argument("--name", required=True, dest="full_name")
    args = parser.parse_args(argv)

    password = getpass.getpass("Mật khẩu (tối thiểu 12 ký tự): ")
    if len(password) < MIN_PASSWORD_LENGTH:
        print("Mật khẩu quá ngắn")
        return 1

    engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
    return asyncio.run(_run_create_admin(engine, args.email, args.full_name, password))


if __name__ == "__main__":
    raise SystemExit(main())
