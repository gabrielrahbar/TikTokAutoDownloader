"""
Tests for the FastAPI backend (api_server.py).
Verifies endpoints return the standard JSON envelope.
"""

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from api_server import app


class TestHealthEndpoint(unittest.TestCase):
    """Health-check endpoint should always return success."""

    def setUp(self):
        self.client = TestClient(app)

    def test_health_returns_200(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

    def test_health_response_format(self):
        response = self.client.get("/health")
        body = response.json()
        self.assertTrue(body["success"])
        self.assertIn("status", body["data"])
        self.assertEqual(body["data"]["status"], "ok")
        self.assertIsNone(body["error"])

    def test_health_contains_version(self):
        response = self.client.get("/health")
        body = response.json()
        self.assertIn("version", body["data"])


class TestUserVideosEndpoint(unittest.TestCase):
    """GET /api/user/{username}/videos should return video list."""

    def setUp(self):
        self.client = TestClient(app)

    @patch("api_server._get_monitor")
    def test_user_videos_success(self, mock_get_monitor):
        """Verify response format when videos are returned."""
        mock_monitor = MagicMock()
        mock_monitor.get_user_videos.return_value = (
            [
                {"id": "123", "url": "https://tiktok.com/@u/video/123",
                 "title": "Test", "timestamp": 1700000000, "upload_date": "20231114"}
            ],
            None,  # no error
        )
        mock_get_monitor.return_value = mock_monitor

        response = self.client.get("/api/user/testuser/videos?count=1")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertIsNone(body["error"])
        self.assertEqual(body["data"]["count"], 1)
        self.assertEqual(len(body["data"]["videos"]), 1)
        self.assertEqual(body["data"]["videos"][0]["id"], "123")

    @patch("api_server._get_monitor")
    def test_user_videos_error_from_monitor(self, mock_get_monitor):
        """When the monitor returns an error, success should be false."""
        mock_monitor = MagicMock()
        mock_monitor.get_user_videos.return_value = ([], "Geo-restricted")
        mock_get_monitor.return_value = mock_monitor

        response = self.client.get("/api/user/blocked/videos")
        body = response.json()
        self.assertFalse(body["success"])
        self.assertIsNotNone(body["error"])

    @patch("api_server._get_monitor")
    def test_user_videos_empty(self, mock_get_monitor):
        """When user has no videos, list should be empty."""
        mock_monitor = MagicMock()
        mock_monitor.get_user_videos.return_value = ([], None)
        mock_get_monitor.return_value = mock_monitor

        response = self.client.get("/api/user/newuser/videos")
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["count"], 0)
        self.assertEqual(body["data"]["videos"], [])

    def test_user_videos_count_validation(self):
        """Count parameter should be validated (1-30)."""
        # count=0 should return 422
        response = self.client.get("/api/user/u/videos?count=0")
        self.assertEqual(response.status_code, 422)

        response = self.client.get("/api/user/u/videos?count=50")
        self.assertEqual(response.status_code, 422)


class TestVideoInfoEndpoint(unittest.TestCase):
    """GET /api/video/{video_id}/info should return video metadata."""

    def setUp(self):
        self.client = TestClient(app)

    def test_video_info_success(self):
        """Verify successful video info response."""
        import sys

        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "id": "999",
            "webpage_url": "https://tiktok.com/video/999",
            "title": "Cool video",
            "uploader": "creator",
            "upload_date": "20240101",
            "timestamp": 1704067200,
            "like_count": 500,
            "view_count": 10000,
            "url": "https://cdn.tiktok.com/video.mp4",
        }

        mock_yt_dlp = MagicMock()
        mock_yt_dlp.YoutubeDL.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_yt_dlp.YoutubeDL.return_value.__exit__ = MagicMock(return_value=False)

        # Temporarily inject mock yt_dlp into sys.modules
        original = sys.modules.get("yt_dlp")
        sys.modules["yt_dlp"] = mock_yt_dlp
        try:
            response = self.client.get("/api/video/999/info")
        finally:
            if original is not None:
                sys.modules["yt_dlp"] = original
            else:
                sys.modules.pop("yt_dlp", None)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        video = body["data"]["video"]
        self.assertEqual(video["id"], "999")
        self.assertEqual(video["title"], "Cool video")
        self.assertEqual(video["likes"], 500)


    def test_video_info_with_username(self):
        """When username is provided, URL should include @username."""
        import sys

        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "id": "888",
            "webpage_url": "https://tiktok.com/@cooluser/video/888",
            "title": "Username video",
            "uploader": "cooluser",
            "upload_date": "20240201",
            "timestamp": 1706745600,
            "like_count": 100,
            "view_count": 5000,
            "url": "https://cdn.tiktok.com/video888.mp4",
        }

        mock_yt_dlp = MagicMock()
        mock_yt_dlp.YoutubeDL.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_yt_dlp.YoutubeDL.return_value.__exit__ = MagicMock(return_value=False)

        original = sys.modules.get("yt_dlp")
        sys.modules["yt_dlp"] = mock_yt_dlp
        try:
            response = self.client.get("/api/video/888/info?username=cooluser")
        finally:
            if original is not None:
                sys.modules["yt_dlp"] = original
            else:
                sys.modules.pop("yt_dlp", None)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])

        # Verify the URL passed to yt-dlp includes the username
        call_args = mock_ydl.extract_info.call_args
        used_url = call_args[0][0]
        self.assertIn("@cooluser", used_url)
        self.assertEqual(used_url, "https://www.tiktok.com/@cooluser/video/888")

    def test_video_info_without_username_fallback(self):
        """Without username, fallback URL is used (backward compat)."""
        import sys

        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "id": "777",
            "webpage_url": "https://tiktok.com/video/777",
            "title": "Fallback video",
            "uploader": "",
            "upload_date": "20240301",
            "timestamp": 1709251200,
            "like_count": 0,
            "view_count": 0,
            "url": "",
        }

        mock_yt_dlp = MagicMock()
        mock_yt_dlp.YoutubeDL.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_yt_dlp.YoutubeDL.return_value.__exit__ = MagicMock(return_value=False)

        original = sys.modules.get("yt_dlp")
        sys.modules["yt_dlp"] = mock_yt_dlp
        try:
            response = self.client.get("/api/video/777/info")
        finally:
            if original is not None:
                sys.modules["yt_dlp"] = original
            else:
                sys.modules.pop("yt_dlp", None)

        self.assertEqual(response.status_code, 200)

        # Verify the URL passed to yt-dlp uses the old fallback format
        call_args = mock_ydl.extract_info.call_args
        used_url = call_args[0][0]
        self.assertEqual(used_url, "https://www.tiktok.com/video/777")


    def test_video_info_with_username_with_at_prefix(self):
        """Username that already contains '@' should not be double-prefixed."""
        import sys

        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "id": "777",
            "webpage_url": "https://tiktok.com/@cooluser/video/777",
            "title": "Video with username",
            "uploader": "cooluser",
            "upload_date": "20240302",
            "timestamp": 1709337600,
            "like_count": 10,
            "view_count": 100,
            "url": "",
        }

        mock_yt_dlp = MagicMock()
        mock_yt_dlp.YoutubeDL.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_yt_dlp.YoutubeDL.return_value.__exit__ = MagicMock(return_value=False)

        original = sys.modules.get("yt_dlp")
        sys.modules["yt_dlp"] = mock_yt_dlp
        try:
            response = self.client.get("/api/video/777/info?username=@cooluser")
        finally:
            if original is not None:
                sys.modules["yt_dlp"] = original
            else:
                sys.modules.pop("yt_dlp", None)

        self.assertEqual(response.status_code, 200)

        # Verify the URL passed to yt-dlp uses exactly one '@' prefix
        call_args = mock_ydl.extract_info.call_args
        used_url = call_args[0][0]
        self.assertEqual(used_url, "https://www.tiktok.com/@cooluser/video/777")

    def test_video_info_with_full_url_video_id(self):
        """When video_id starts with http, it should be used as-is."""
        import sys
        import asyncio

        from api_server import get_video_info

        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "id": "123",
            "webpage_url": "https://tiktok.com/@user/video/123",
            "title": "Full URL video",
            "uploader": "user",
            "upload_date": "20240303",
            "timestamp": 1709424000,
            "like_count": 5,
            "view_count": 50,
            "url": "",
        }

        mock_yt_dlp = MagicMock()
        mock_yt_dlp.YoutubeDL.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_yt_dlp.YoutubeDL.return_value.__exit__ = MagicMock(return_value=False)

        # Full URLs can't be passed as path params (slashes break routing),
        # so test the async function directly.
        original = sys.modules.get("yt_dlp")
        sys.modules["yt_dlp"] = mock_yt_dlp
        try:
            full_url = "https://tiktok.com/@user/video/123"
            result = asyncio.get_event_loop().run_until_complete(
                get_video_info(video_id=full_url)
            )
        finally:
            if original is not None:
                sys.modules["yt_dlp"] = original
            else:
                sys.modules.pop("yt_dlp", None)

        self.assertTrue(result.success)

        # Verify yt-dlp received the full URL as-is
        call_args = mock_ydl.extract_info.call_args
        used_url = call_args[0][0]
        self.assertEqual(used_url, full_url)


class TestResponseEnvelope(unittest.TestCase):
    """All endpoints must return the standard { success, data, error } envelope."""

    def setUp(self):
        self.client = TestClient(app)

    def test_envelope_keys_present(self):
        response = self.client.get("/health")
        body = response.json()
        self.assertIn("success", body)
        self.assertIn("data", body)
        self.assertIn("error", body)


if __name__ == "__main__":
    unittest.main()
