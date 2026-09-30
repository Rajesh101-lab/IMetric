from dataclasses import dataclass
from typing import List, Optional, Protocol, Dict, Any


@dataclass
class RawPageData:
    followers: int
    reels: List[Dict[str, Any]]
    source: str = "official"
    fallback_reason: Optional[str] = None


class MetricsProvider(Protocol):
    name: str

    async def fetch(self, username: str, n_reels: int = 12) -> RawPageData:
        ...
