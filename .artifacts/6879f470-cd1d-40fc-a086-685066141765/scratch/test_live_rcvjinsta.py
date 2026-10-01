import sys
import os
import httpx

sys.path.insert(0, os.path.abspath("backend"))
from app.core.config import settings

def test_rcvjinsta():
    token = settings.META_ACCESS_TOKEN
    ig_id = settings.IG_BUSINESS_ACCOUNT_ID
    version = settings.GRAPH_API_VERSION
    target = "rcvjinsta"

    print(f"Testing live Business Discovery for @{target}...")
    url = f"https://graph.facebook.com/{version}/{ig_id}"
    fields = f"business_discovery.username({target}){{followers_count,media_count}}"
    params = {
        "fields": fields,
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
    test_rcvjinsta()
