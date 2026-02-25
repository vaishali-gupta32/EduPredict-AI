"""
Database seed script: creates the default admin user.
Run: python db/seed.py  (from the backend/ directory)
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import AsyncSessionLocal, create_tables
from models.db_models import User
from core.security import hash_password
from sqlalchemy import select


async def seed():
    await create_tables()

    async with AsyncSessionLocal() as db:
        # Check if admin already exists
        result = await db.execute(select(User).where(User.email == "admin@college.edu"))
        existing = result.scalar_one_or_none()

        if existing:
            print("ℹ️  Admin user already exists.")
            return

        admin = User(
            email="admin@college.edu",
            password_hash=hash_password("Admin@1234"),
            full_name="System Administrator",
            role="admin",
            is_active=True,
        )
        db.add(admin)

        viewer = User(
            email="viewer@college.edu",
            password_hash=hash_password("Viewer@1234"),
            full_name="Faculty Viewer",
            role="viewer",
            is_active=True,
        )
        db.add(viewer)

        await db.commit()
        print("✅ Seeded users:")
        print("   admin@college.edu  / Admin@1234  (role: admin)")
        print("   viewer@college.edu / Viewer@1234 (role: viewer)")


if __name__ == "__main__":
    asyncio.run(seed())
