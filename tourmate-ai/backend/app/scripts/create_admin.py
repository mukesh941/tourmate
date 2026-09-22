"""
Secure server-side administrator provisioning utility for TourMate AI.

Usage:
    python -m app.scripts.create_admin --email admin@example.com [--password <secret>] [--name "Admin User"]
Or:
    python create_admin.py --email admin@example.com

Security notes:
    - Never hardcodes passwords or sensitive credentials.
    - Uses bcrypt password hashing (app.core.security.hash_password).
    - Stores authoritative admin records in PostgreSQL (users table, role='admin').
    - Promotes existing accounts safely or registers a new admin account.
"""
import argparse
import asyncio
import getpass
import sys
from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.core.security import hash_password
from app.models.sql.user import User


async def provision_admin(email: str, password: str | None = None, name: str | None = None) -> None:
    email_clean = email.strip().lower()
    if not email_clean or "@" not in email_clean:
        print("[ERROR] A valid email address is required.", file=sys.stderr)
        sys.exit(1)

    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.email == email_clean)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if user:
            # User exists - promote to admin
            user.role = "admin"
            user.is_active = True
            if name:
                user.name = name.strip()
            if password:
                if len(password) < 8:
                    print("[ERROR] Password must be at least 8 characters long.", file=sys.stderr)
                    sys.exit(1)
                user.password_hash = hash_password(password)
            await session.commit()
            print(f"[SUCCESS] User '{user.email}' has been promoted to administrator (role='admin').")
        else:
            # User does not exist - must provide password
            if not password:
                print("[ERROR] Password is required to create a new administrator account.", file=sys.stderr)
                sys.exit(1)
            if len(password) < 8:
                print("[ERROR] Password must be at least 8 characters long.", file=sys.stderr)
                sys.exit(1)

            admin_user = User(
                email=email_clean,
                name=(name.strip() if name else "Administrator"),
                password_hash=hash_password(password),
                role="admin",
                preferred_language="en",
                is_active=True,
            )
            session.add(admin_user)
            await session.commit()
            print(f"[SUCCESS] Created new administrator account for '{email_clean}' with role='admin'.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Provision an administrator account for TourMate AI.")
    parser.add_argument("--email", type=str, help="Email address for the administrator.")
    parser.add_argument("--password", type=str, default=None, help="Password (min 8 chars). If omitted, prompt securely.")
    parser.add_argument("--name", type=str, default=None, help="Full name for the administrator.")
    args = parser.parse_args()

    email = args.email
    if not email:
        email = input("Administrator email: ").strip()

    password = args.password
    if not password:
        password = getpass.getpass("Administrator password (min 8 chars, press Enter to keep existing if promoting): ")
        if not password:
            password = None

    asyncio.run(provision_admin(email, password, args.name))


if __name__ == "__main__":
    main()
