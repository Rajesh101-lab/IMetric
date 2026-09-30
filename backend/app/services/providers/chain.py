import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import ProviderUsage
from app.db.session import AsyncSessionLocal
from app.services.business_discovery import IGError, Kind, ig_client, NEGATIVE_CACHE
from app.services.providers.base import RawPageData
from app.services.providers.serpapi import SerpApiProvider

logger = logging.getLogger("app.services.providers.chain")


class ProviderUsageTracker:
    @staticmethod
    async def record_usage(agency_id: UUID, provider_name: str, ok: bool):
        day_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        async with AsyncSessionLocal() as session:
            try:
                stmt = select(ProviderUsage).where(
                    ProviderUsage.day_date == day_str,
                    ProviderUsage.provider_name == provider_name,
                    ProviderUsage.agency_id == agency_id
                )
                res = await session.execute(stmt)
                usage = res.scalar_one_or_none()

                if usage:
                    usage.calls += 1
                    if not ok:
                        usage.failures += 1
                else:
                    usage = ProviderUsage(
                        day_date=day_str,
                        provider_name=provider_name,
                        agency_id=agency_id,
                        calls=1,
                        failures=0 if ok else 1
                    )
                    session.add(usage)

                await session.commit()
            except Exception as e:
                logger.warning(f"Error recording provider usage: {e}")

    @staticmethod
    async def is_within_limits(agency_id: UUID, provider_name: str) -> bool:
        day_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        async with AsyncSessionLocal() as session:
            try:
                # Agency daily limit
                stmt_agency = select(ProviderUsage.calls).where(
                    ProviderUsage.day_date == day_str,
                    ProviderUsage.provider_name == provider_name,
                    ProviderUsage.agency_id == agency_id
                )
                res_agency = await session.execute(stmt_agency)
                agency_calls = res_agency.scalar_one_or_none() or 0

                if agency_calls >= settings.BACKUP_PER_AGENCY_DAILY_LIMIT:
                    logger.warning(f"Agency {agency_id} exceeded daily backup limit ({agency_calls}/{settings.BACKUP_PER_AGENCY_DAILY_LIMIT}).")
                    return False

                # Total global daily limit
                stmt_total = select(ProviderUsage.calls).where(
                    ProviderUsage.day_date == day_str,
                    ProviderUsage.provider_name == provider_name
                )
                res_total = await session.execute(stmt_total)
                total_calls = sum(res_total.scalars().all())

                if total_calls >= settings.BACKUP_DAILY_LIMIT:
                    logger.warning(f"Global daily backup limit exceeded ({total_calls}/{settings.BACKUP_DAILY_LIMIT}).")
                    return False

                if total_calls >= settings.BACKUP_DAILY_LIMIT * 0.8:
                    logger.warning(f"Global daily backup limit reached 80% ({total_calls}/{settings.BACKUP_DAILY_LIMIT}).")

                return True
            except Exception as e:
                logger.warning(f"Error checking provider limits: {e}")
                return True


class ProviderChain:
    def __init__(self):
        self.primary = ig_client
        self.backup = SerpApiProvider()

    async def fetch(self, username: str, agency_id: UUID, n_reels: int = 12) -> RawPageData:
        clean_user = username.strip().lower()

        # Check negative cache
        now = time.monotonic()
        if clean_user in NEGATIVE_CACHE and now < NEGATIVE_CACHE[clean_user]:
            raise IGError(
                kind=Kind.NOT_FOUND,
                message=f"We couldn't find @{clean_user}, or it isn't a Business or Creator account.",
                http_status=404,
                retryable=False
            )

        # 1. Try Primary Official Provider
        try:
            raw_dict = await self.primary.fetch_page_raw(clean_user, n_reels=n_reels)
            return RawPageData(
                followers=raw_dict.get("followers", 0),
                reels=raw_dict.get("reels", []),
                source="official",
                fallback_reason=None
            )
        except IGError as primary_err:
            logger.info(
                f"Primary provider failed for @{clean_user} (kind={primary_err.kind}). Checking backup eligibility..."
            )

            fallback_kinds = [k.strip().lower() for k in settings.BACKUP_FALLBACK_ON.split(",") if k.strip()]
            eligible = (
                settings.BACKUP_ENABLED
                and primary_err.kind.value in fallback_kinds
                and primary_err.kind != Kind.INVALID
                and not self.backup.is_circuit_open
                and await ProviderUsageTracker.is_within_limits(agency_id, self.backup.name)
            )

            if not eligible:
                if primary_err.kind == Kind.NOT_FOUND:
                    NEGATIVE_CACHE[clean_user] = time.monotonic() + settings.NEGATIVE_CACHE_TTL_SECONDS
                raise primary_err

            # 2. Try Backup Provider
            try:
                logger.info(f"Fallback triggered: Fetching @{clean_user} via {self.backup.name} provider.")
                backup_data = await self.backup.fetch(clean_user, n_reels=n_reels)
                backup_data.source = "backup"
                backup_data.fallback_reason = primary_err.kind.value

                await ProviderUsageTracker.record_usage(agency_id, self.backup.name, ok=True)
                return backup_data

            except IGError as backup_err:
                await ProviderUsageTracker.record_usage(agency_id, self.backup.name, ok=False)
                final_err = self._pick_error(primary_err, backup_err)

                if final_err.kind == Kind.NOT_FOUND:
                    NEGATIVE_CACHE[clean_user] = time.monotonic() + settings.NEGATIVE_CACHE_TTL_SECONDS
                raise final_err

    @staticmethod
    def _pick_error(primary: IGError, backup: IGError) -> IGError:
        if primary.kind == Kind.NOT_FOUND or backup.kind == Kind.NOT_FOUND:
            return primary if primary.kind == Kind.NOT_FOUND else backup
        return primary


# Global ProviderChain Singleton
provider_chain = ProviderChain()
