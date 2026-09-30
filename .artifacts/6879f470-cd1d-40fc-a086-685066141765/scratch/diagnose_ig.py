import sys
import os
import httpx

sys.path.insert(0, os.path.abspath("backend"))
from app.core.config import settings

def diagnose():
    token = settings.META_ACCESS_TOKEN
    ig_id = settings.IG_BUSINESS_ACCOUNT_ID
    version = settings.GRAPH_API_VERSION
    username = "nike"

    print(f"--- Instagram API Diagnostic ---")
    print(f"Graph Version: {version}")
    print(f"IG Business Account ID: {ig_id}")
    print(f"Token length: {len(token) if token else 0}")

    if not token or not ig_id:
        print("ERROR: META_ACCESS_TOKEN or IG_BUSINESS_ACCOUNT_ID is missing in .env!")
        return

    url = f"https://graph.facebook.com/{version}/{ig_id}"
    fields = f"business_discovery.username({username}){{followers_count,media_count,media.limit(10){{media_product_type,timestamp,like_count,comments_count,play_count}}}}"
    params = {
        "fields": fields,
        "access_token": token
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(url, params=params)
        print(f"HTTP Status Code: {resp.status_code}")
        print("Response JSON:")
        import json
        print(json.dumps(resp.json(), indent=2))
    except Exception as e:
        print(f"HTTP Request Exception: {e}")

if __name__ == "__main__":
    diagnose()
