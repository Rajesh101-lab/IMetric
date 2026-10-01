import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy import func, select, update, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import ProviderUsage
from app.db.session import AsyncSessionLocal
from app.services.business_discovery import IGError, Kind, ig_client, NEGATIVE_CACHE
from app.services.providers.base import RawPageData
from app.services.providers.serpapi import SerpApiProvider

logger = logging.getLogger("app.services.providers.chain")
_BACKUP_QUOTA_LOCK_ID = 0x4241434B555051
_BACKUP_QUOTA_LOCK = asyncio.Lock()


class ProviderUsageTracker:
    @staticmethod
    async def reserve_call(agency_id: UUID, provider_name: str) -> bool:
        day_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        async with _BACKUP_QUOTA_LOCK:
            async with AsyncSessionLocal() as session:
                try:
                    async with session.begin():
                        if session.bind and session.bind.dialect.name == "postgresql":
                            await session.execute(
                                text("SELECT pg_advisory_xact_lock(:lock_id)"),
                                {"lock_id": _BACKUP_QUOTA_LOCK_ID},
                            )

                        agency_result = await session.execute(
                            select(func.coalesce(func.sum(ProviderUsage.calls), 0)).where(
                                ProviderUsage.day_date == day_str,
                                ProviderUsage.provider_name == provider_name,
                                ProviderUsage.agency_id == agency_id,
                            )
                        )
                        agency_calls = int(agency_result.scalar_one())
                        global_result = await session.execute(
                            select(func.coalesce(func.sum(ProviderUsage.calls), 0)).where(
                                ProviderUsage.day_date == day_str,
                                ProviderUsage.provider_name == provider_name,
                            )
                        )
                        global_calls = int(global_result.scalar_one())

                        if agency_calls >= settings.BACKUP_PER_AGENCY_DAILY_LIMIT:
                            return False
                        if global_calls >= settings.BACKUP_DAILY_LIMIT:
                            return False

                        usage_result = await session.execute(
                            select(ProviderUsage)
                            .where(
                                ProviderUsage.day_date == day_str,
                                ProviderUsage.provider_name == provider_name,
                                ProviderUsage.agency_id == agency_id,
                            )
                            .with_for_update()
                        )
                        usage = usage_result.scalar_one_or_none()
                        if usage is None:
                            session.add(ProviderUsage(
                                day_date=day_str,
                                provider_name=provider_name,
                                agency_id=agency_id,
                                calls=1,
                                failures=0,
                            ))
                        else:
                            usage.calls += 1
                    return True
                except Exception:
                    logger.exception("Could not reserve provider quota; rejecting backup call")
                    return False

    @staticmethod
    async def record_failure(agency_id: UUID, provider_name: str):
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
                    usage.failures += 1
                await session.commit()
            except Exception:
                logger.exception("Could not record provider failure")


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
                and await ProviderUsageTracker.reserve_call(agency_id, self.backup.name)
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
                await ProviderUsageTracker.record_failure(agency_id, self.backup.name)
                final_err = self._pick_error(primary_err, backup_err)

                if final_err.kind == Kind.NOT_FOUND:
                    NEGATIVE_CACHE[clean_user] = time.monotonic() + settings.NEGATIVE_CACHE_TTL_SECONDS
                raise final_err
            except Exception:
                await ProviderUsageTracker.record_failure(agency_id, self.backup.name)
                raise primary_err

    @staticmethod
    def _pick_error(primary: IGError, backup: IGError) -> IGError:
        if primary.kind == Kind.NOT_FOUND or backup.kind == Kind.NOT_FOUND:
            return primary if primary.kind == Kind.NOT_FOUND else backup
        return primary


# Global ProviderChain Singleton
provider_chain = ProviderChain()
