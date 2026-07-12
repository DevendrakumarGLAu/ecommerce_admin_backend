"""Creates a dev admin account so you can log into the Angular admin panel.

There is no API endpoint for creating an admin (POST /auth/register always
creates a `customer`), so this script writes directly to the database using
the same repository/hashing code the app itself uses.

Usage (from the ecommerce-backend/ directory, after `pip install -r requirements.txt`
and `alembic upgrade head` have been run against a working DATABASE_URL):

    python scripts/seed_admin.py
    python scripts/seed_admin.py --email me@example.com --password "MyPassword123" --first-name Jane --last-name Doe

Bootstrapping the first super admin (needed to promote/manage other admins from
the Users screen — there's no way to create one via the API):

    python scripts/seed_admin.py --role super_admin --email owner@example.com --password "MyPassword123"

Safe to re-run: if the email already exists, it just reports that instead of
creating a duplicate.
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import AsyncSessionLocal  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.user import UserRole  # noqa: E402
from app.repositories.user_repository import UserRepository  # noqa: E402

DEFAULT_EMAIL = "admin@firozabadbangles.com"
DEFAULT_PASSWORD = "Admin@12345"


async def seed_admin(email: str, password: str, first_name: str, last_name: str, role: UserRole) -> None:
    async with AsyncSessionLocal() as db:
        users = UserRepository(db)

        existing = await users.get_by_email(email)
        if existing is not None:
            print(f"A user with email '{email}' already exists (role={existing.role}). Nothing to do.")
            return

        await users.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=None,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )
        await users.commit()

        print(f"{role.value.replace('_', ' ').title()} account created:")
        print(f"  Email:    {email}")
        print(f"  Password: {password}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", default=DEFAULT_EMAIL)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    parser.add_argument("--first-name", default="Admin")
    parser.add_argument("--last-name", default="User")
    parser.add_argument("--role", choices=["admin", "super_admin"], default="admin")
    args = parser.parse_args()

    asyncio.run(seed_admin(args.email, args.password, args.first_name, args.last_name, UserRole(args.role)))


if __name__ == "__main__":
    main()
