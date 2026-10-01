import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath("backend"))

from app.db.session import AsyncSessionLocal
from app.db.models import User
from app.services import pages as pages_service
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).limit(1))
        u = res.scalar_one()
        p, created = await pages_service.add_or_upsert_page(db, u.id, 'cineglaam')
        print(f"Result -> username={p.username}, followers={p.followers}, status={p.status}, reels_sampled={p.reels_sampled}")

if __name__ == "__main__":
    asyncio.run(main())
