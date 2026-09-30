import httpx
from fastapi import APIRouter, HTTPException, Query, Response
from typing import Optional

router = APIRouter()

@router.get("/proxy")
async def proxy_image(url: str = Query(..., description="URL of the image to proxy")):
    try:
        # Use a generic User-Agent to satisfy Wikimedia Commons
        headers = {
            "User-Agent": "TourMateAI/1.0 (https://tourmate.example.com/; contact@tourmate.example.com) httpx/0.24.1",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        }
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=headers, follow_redirects=True, timeout=10.0)
            
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail="Failed to fetch image")
                
            return Response(
                content=res.content,
                media_type=res.headers.get("content-type", "image/jpeg"),
                headers={
                    "Cache-Control": "public, max-age=86400",
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
