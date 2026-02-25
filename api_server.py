#!/usr/bin/env python3
"""
TikTok Auto Downloader - FastAPI Backend
REST API that wraps the existing Python download logic.
Designed for deployment on Render.com free tier.
"""

import os
import sys
import traceback
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Pydantic models for standard JSON responses
# ---------------------------------------------------------------------------

class VideoItem(BaseModel):
    id: str = ""
    url: str = ""
    title: str = ""
    author: str = ""
    upload_date: str = ""
    upload_timestamp: int = 0
    likes: int = 0
    views: int = 0
    download_url: str = ""


class ApiResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="TikTok Auto Downloader API",
    description="REST API wrapping the TikTok monitoring and download logic.",
    version="1.0.0",
)

# CORS – allow all origins so the Android app can call from any host
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helper: lazy-initialise TikTokMonitor (heavy import, keep out of top level)
# ---------------------------------------------------------------------------

_monitor = None


def _get_monitor():
    """Lazy-initialise the TikTokMonitor singleton."""
    global _monitor
    if _monitor is None:
        from tiktok_monitor import TikTokMonitor
        _monitor = TikTokMonitor()
    return _monitor


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=ApiResponse)
async def health_check():
    """Health-check endpoint for Render / uptime monitors."""
    return ApiResponse(success=True, data={"status": "ok", "version": "1.0.0"})


@app.get("/api/user/{username}/videos", response_model=ApiResponse)
async def get_user_videos(
    username: str,
    count: int = Query(default=5, ge=1, le=30, description="Max videos to return"),
):
    """
    Fetch recent public videos for a TikTok user.

    Wraps ``TikTokMonitor.get_user_videos()`` which uses yt-dlp under the hood
    with geo-bypass and retry logic.
    """
    try:
        monitor = _get_monitor()
        videos, error = monitor.get_user_videos(username, max_videos=count)

        if error is not None:
            return ApiResponse(
                success=False,
                data={"videos": [], "count": 0},
                error=str(error),
            )

        video_list = []
        for v in videos:
            video_list.append(
                VideoItem(
                    id=v.get("id", ""),
                    url=v.get("url", ""),
                    title=v.get("title", ""),
                    author=username,
                    upload_date=v.get("upload_date", ""),
                    upload_timestamp=v.get("timestamp", 0),
                ).model_dump()
            )

        return ApiResponse(
            success=True,
            data={"videos": video_list, "count": len(video_list)},
        )

    except Exception as exc:
        traceback.print_exc()
        return ApiResponse(success=False, error=str(exc))


@app.get("/api/video/{video_id}/info", response_model=ApiResponse)
async def get_video_info(video_id: str):
    """
    Fetch metadata for a single TikTok video.

    Uses yt-dlp ``extract_info`` without downloading the file.
    """
    try:
        import yt_dlp

        url = f"https://www.tiktok.com/video/{video_id}"

        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "geo_bypass": True,
            "geo_bypass_country": "US",
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36"
                ),
            },
            "socket_timeout": 30,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if info is None:
            return ApiResponse(success=False, error="Video not found")

        video = VideoItem(
            id=info.get("id", video_id),
            url=info.get("webpage_url", url),
            title=info.get("title", ""),
            author=info.get("uploader", ""),
            upload_date=info.get("upload_date", ""),
            upload_timestamp=info.get("timestamp", 0),
            likes=info.get("like_count", 0) or 0,
            views=info.get("view_count", 0) or 0,
            download_url=info.get("url", ""),
        )

        return ApiResponse(success=True, data={"video": video.model_dump()})

    except Exception as exc:
        traceback.print_exc()
        return ApiResponse(success=False, error=str(exc))


# ---------------------------------------------------------------------------
# Entry-point (for local development: python api_server.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=True)
