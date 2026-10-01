import sys
import os
import asyncio
import httpx

sys.path.insert(0, os.path.abspath("backend"))
from app.core.config import settings
from app.services.business_discovery import ig_client

async def test_realtime_fetch():
    print("==================================================")
    print("     PAGE METRICS: REAL-TIME IG API TESTER       ")
    print("==================================================")
    print(f"Environment Check:")
    print(f" - Graph API Version: {settings.GRAPH_API_VERSION}")
    print(f" - IG Business Account ID: {settings.IG_BUSINESS_ACCOUNT_ID}")
    print(f" - META_ACCESS_TOKEN configured? {'YES (Length: ' + str(len(settings.META_ACCESS_TOKEN)) + ')' if settings.META_ACCESS_TOKEN else 'NO'}")
    print("--------------------------------------------------")

    test_username = "theflickguyy"  # User's connected IG handle
    print(f"Testing real-time metrics fetch for @{test_username}...")

    try:
        data = await ig_client.fetch_page_raw(test_username, n_reels=12)
        print("\n[SUCCESS] Real-time data fetched successfully from Meta Graph API!")
        print(f" - Followers: {data.get('followers')}")
        print(f" - Reels Sampled: {len(data.get('reels', []))}")
        for idx, reel in enumerate(data.get('reels', [])[:3], 1):
            print(f"   * Reel {idx}: Views={reel.get('views')}, Likes={reel.get('likes')}, Timestamp={reel.get('timestamp')}")
    except Exception as e:
        print(f"\n[ERROR] Real-time fetch failed: {e}")
        import traceback
        traceback.print_exc()

    print("==================================================")

if __name__ == "__main__":
    asyncio.run(test_realtime_fetch())
