import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath("backend"))

from app.db.session import AsyncSessionLocal
from app.db.models import User, Page
from app.services import pages as pages_service
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).limit(1))
        u = res.scalar_one()
        p, created = await pages_service.add_or_upsert_page(db, u.id, 'cineglaam')
        print(f"Initial -> status={p.status}, followers={p.followers}")

    print("Waiting 3 seconds for background fetch task...")
    await asyncio.sleep(3.0)

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Page).where(Page.username == 'cineglaam'))
        p = res.scalar_one()
        print(f"After 3s -> username={p.username}, followers={p.followers}, status={p.status}, reels_sampled={p.reels_sampled}, error={p.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
