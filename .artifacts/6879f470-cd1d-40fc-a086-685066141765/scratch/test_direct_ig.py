import sys
import os
import httpx

sys.path.insert(0, os.path.abspath("backend"))
from app.core.config import settings

def test_direct():
    token = settings.META_ACCESS_TOKEN
    ig_id = settings.IG_BUSINESS_ACCOUNT_ID
    version = settings.GRAPH_API_VERSION

    print(f"Testing direct query on IG Business ID: {ig_id}")
    url = f"https://graph.facebook.com/{version}/{ig_id}"
    params = {
        "fields": "username,followers_count,media_count,media.limit(12){media_product_type,timestamp,like_count,comments_count,play_count}",
        "access_token": token
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(url, params=params)
        print(f"Status Code: {resp.status_code}")
        print("Response:", resp.text)
    except Exception as e:
        print("Exception:", e)

if __name__ == "__main__":
    test_direct()
