import asyncio
import os
import sys

# Add parent directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import AsyncSessionLocal
from backend.crud import create_user, get_user_by_email
from backend.schemas import UserCreate

async def seed_default_user():
    async with AsyncSessionLocal() as db:
        email = "admin@example.com"
        password = "admin"
        
        user = await get_user_by_email(db, email)
        if user:
            print(f"User {email} already exists.")
            return

        print(f"Creating default user: {email}")
        new_user = UserCreate(email=email, password=password, role="admin", org_name="SRE Admin Org")
        await create_user(db, new_user)
        print("User created successfully.")

if __name__ == "__main__":
    asyncio.run(seed_default_user())
