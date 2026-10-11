import urllib.request
from app.services.destination_service import CANONICAL_DESTINATION_METADATA

for key, meta in CANONICAL_DESTINATION_METADATA.items():
    url = meta.get("cover_image")
    if url:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            res = urllib.request.urlopen(req)
            print(f"{key}: {res.getcode()}")
        except Exception as e:
            print(f"{key}: Error: {e}")
