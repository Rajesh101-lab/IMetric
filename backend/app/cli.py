import asyncio
import getpass
import sys
import uuid
import argparse
from sqlalchemy import select
from app.core.security import (
    hash_password,
    validate_password_policy,
    normalize_username,
    validate_username_format,
)
from app.db.session import AsyncSessionLocal
from app.db.models import User
from app.services.auth import invalidate_all_user_sessions
from app.services.business_discovery import IGError, ig_client
from app.services.providers.chain import provider_chain


async def cli_create_user(agency_id: str):
    clean_id = normalize_username(agency_id)
    if not validate_username_format(clean_id):
        print(f"Error: Invalid Agency ID '{agency_id}'. Must match ^[A-Za-z0-9._]{{1,30}}$")
        sys.exit(1)

    password = getpass.getpass("Enter password for agency account: ")
    password_confirm = getpass.getpass("Confirm password: ")

    if password != password_confirm:
        print("Error: Passwords do not match.")
        sys.exit(1)

    policy_err = validate_password_policy(password, clean_id)
    if policy_err:
        print(f"Password Policy Error: {policy_err}")
        sys.exit(1)

    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.username == clean_id)
        res = await db.execute(stmt)
        if res.scalar_one_or_none() is not None:
            print(f"Error: Agency ID '{clean_id}' already exists.")
            sys.exit(1)

        phash = hash_password(password)
        user = User(
            username=clean_id,
            password_hash=phash,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        print(f"Successfully created agency account '{clean_id}'.")


async def cli_reset_password(agency_id: str):
    clean_id = normalize_username(agency_id)

    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.username == clean_id)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            print(f"Error: Agency ID '{clean_id}' not found.")
            sys.exit(1)

        password = getpass.getpass("Enter NEW password: ")
        password_confirm = getpass.getpass("Confirm NEW password: ")

        if password != password_confirm:
            print("Error: Passwords do not match.")
            sys.exit(1)

        policy_err = validate_password_policy(password, clean_id)
        if policy_err:
            print(f"Password Policy Error: {policy_err}")
            sys.exit(1)

        user.password_hash = hash_password(password)
        user.failed_login_count = 0
        user.locked_until = None
        await db.commit()

        # Invalidate all active sessions for this user
        await invalidate_all_user_sessions(db, user.id)
        print(f"Password reset successfully for agency '{clean_id}'. All active sessions invalidated.")


async def cli_deactivate_user(agency_id: str):
    clean_id = normalize_username(agency_id)

    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.username == clean_id)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            print(f"Error: Agency ID '{clean_id}' not found.")
            sys.exit(1)

        user.is_active = False
        await db.commit()

        # Invalidate all active sessions for this user
        await invalidate_all_user_sessions(db, user.id)
        print(f"Agency account '{clean_id}' deactivated. All active sessions invalidated.")


async def cli_check_instagram(username: str):
    print(f"Checking Instagram Graph API for handle @{username}...")
    try:
        data = await ig_client.fetch_page_raw(username)
        print(f"SUCCESS! Followers: {data.get('followers')}, Reels sampled: {len(data.get('reels', []))}")
    except IGError as err:
        print(f"CLASSIFIED ERROR: Kind={err.kind.value}, HTTP Status={err.http_status}, Message={err.message}")


async def cli_check_providers(username: str):
    print(f"Checking ProviderChain for handle @{username}...")
    try:
        raw_data = await provider_chain.fetch(username, agency_id=uuid.uuid4())
        print(f"FETCH SUCCESS! Source={raw_data.source}, FallbackReason={raw_data.fallback_reason}")
        print(f"Followers={raw_data.followers}, Reels count={len(raw_data.reels)}")
    except IGError as err:
        print(f"FETCH FAILED: Kind={err.kind.value}, HTTP Status={err.http_status}, Message={err.message}")


def main():
    parser = argparse.ArgumentParser(description="IMetric Agency Account CLI Admin")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create-user", help="Create a new agency account")
    create_parser.add_argument("agency_id", help="Agency ID (username)")

    reset_parser = subparsers.add_parser("reset-password", help="Reset password for an agency account")
    reset_parser.add_argument("agency_id", help="Agency ID (username)")

    deactivate_parser = subparsers.add_parser("deactivate-user", help="Deactivate an agency account")
    deactivate_parser.add_argument("agency_id", help="Agency ID (username)")

    check_ig = subparsers.add_parser("check-instagram", help="Test Instagram fetch and error classification")
    check_ig.add_argument("username", help="Instagram username to test")

    check_prov = subparsers.add_parser("check-providers", help="Test ProviderChain fetch and fallback")
    check_prov.add_argument("username", help="Instagram username to test")

    args = parser.parse_args()

    if args.command == "create-user":
        asyncio.run(cli_create_user(args.agency_id))
    elif args.command == "reset-password":
        asyncio.run(cli_reset_password(args.agency_id))
    elif args.command == "deactivate-user":
        asyncio.run(cli_deactivate_user(args.agency_id))
    elif args.command == "check-instagram":
        asyncio.run(cli_check_instagram(args.username))
    elif args.command == "check-providers":
        asyncio.run(cli_check_providers(args.username))


if __name__ == "__main__":
    main()
