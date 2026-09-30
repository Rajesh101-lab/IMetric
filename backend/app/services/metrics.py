import statistics
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.schemas.metrics import PageMetrics


def compute_metrics(
    followers: int,
    reels: List[Dict[str, Any]],
    username: str,
    fetched_at: Optional[datetime] = None,
    sample_size: Optional[int] = None,
) -> PageMetrics:
    """
    Pure computation function for Instagram metrics.
    - Sample = most recent N reels (N configurable, default REEL_SAMPLE_SIZE)
    - avgviews = mean(views), medianviews = median(views), avglikes = mean(likes)
    - liketoviewratio = avglikes / avgviews (0 if avgviews == 0)
    - avgviewsperfollower = avgviews / followers (0 if followers == 0)
    - lastreellikes/lastreelviews = newest reel (None if 0 reels)
    """
    n = sample_size if sample_size is not None else settings.REEL_SAMPLE_SIZE
    sample = reels[:n] if reels else []
    sample_count = len(sample)

    if not sample_count:
        return PageMetrics(
            username=username.lower(),
            followers=followers,
            lastreellikes=None,
            lastreelviews=None,
            avgviews=0.0,
            medianviews=0.0,
            avglikes=0.0,
            liketoviewratio=0.0,
            avgviewsperfollower=0.0,
            reelssampled=0,
            fetched_at=fetched_at or datetime.now(timezone.utc),
        )

    views_list = [float(r.get("views", 0)) for r in sample]
    likes_list = [float(r.get("likes", 0)) for r in sample]

    avg_views = float(statistics.mean(views_list))
    median_views = float(statistics.median(views_list))
    avg_likes = float(statistics.mean(likes_list))

    like_to_view_ratio = (avg_likes / avg_views) if avg_views > 0 else 0.0
    avg_views_per_follower = (avg_views / float(followers)) if followers > 0 else 0.0

    last_reel = sample[0]
    last_likes = int(last_reel.get("likes", 0)) if last_reel.get("likes") is not None else None
    last_views = int(last_reel.get("views", 0)) if last_reel.get("views") is not None else None

    return PageMetrics(
        username=username.lower(),
        followers=max(0, followers),
        lastreellikes=last_likes,
        lastreelviews=last_views,
        avgviews=round(avg_views, 4),
        medianviews=round(median_views, 4),
        avglikes=round(avg_likes, 4),
        liketoviewratio=round(like_to_view_ratio, 6),
        avgviewsperfollower=round(avg_views_per_follower, 6),
        reelssampled=sample_count,
        fetched_at=fetched_at or datetime.now(timezone.utc),
    )
