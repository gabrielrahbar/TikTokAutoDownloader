# Deploy Guide – TikTok Auto Downloader API

This guide explains how to deploy the FastAPI backend to **Render.com** (free tier) and connect the Android app.

---

## 1. Deploy to Render.com

### Prerequisites
- A free [Render.com](https://render.com) account
- This repository pushed to GitHub

### Steps

1. **Log in** to [dashboard.render.com](https://dashboard.render.com).
2. Click **New → Web Service**.
3. Connect your GitHub account and select the **TikTokAutoDownloader** repository.
4. Render will auto-detect `render.yaml`. Accept the defaults:
   - **Name:** `tiktok-downloader-api`
   - **Plan:** Free
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn api_server:app --host 0.0.0.0 --port $PORT`
5. Click **Create Web Service**.
6. Wait for the build to finish (2–5 minutes).
7. Your API will be live at:
   ```
   https://tiktok-downloader-api.onrender.com
   ```

### Verify

```bash
curl https://tiktok-downloader-api.onrender.com/health
```

Expected response:
```json
{"success": true, "data": {"status": "ok", "version": "1.0.0"}, "error": null}
```

> **Note:** On the free tier, the service spins down after 15 minutes of inactivity. The first request after spin-down takes ~30 seconds.

---

## 2. Update the Android App

Open `android/app/src/main/java/com/tiktokdownloader/data/remote/RetrofitClient.kt` and change the `BASE_URL`:

```kotlin
// Replace with your Render.com URL
private const val BASE_URL = "https://tiktok-downloader-api.onrender.com/"
```

Rebuild the app and the Android client will call your backend.

---

## 3. Test Locally (Optional)

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python api_server.py
```

The server starts on `http://localhost:8000`. Swagger docs are at `http://localhost:8000/docs`.

### Example Requests

```bash
# Health check
curl http://localhost:8000/health

# Get user videos
curl "http://localhost:8000/api/user/tiktok/videos?count=3"

# Get single video info
curl http://localhost:8000/api/video/7345678901234567890/info
```

---

## 4. API Reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/user/{username}/videos?count=5` | Get recent videos for a user |
| `GET` | `/api/video/{video_id}/info` | Get metadata for a single video |

All responses use the standard format:

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

---

## 5. Troubleshooting

| Issue | Solution |
|-------|----------|
| First request is slow (~30 s) | Normal on free tier – Render spins up the service |
| 502 Bad Gateway | Check Render logs; the build may have failed |
| `yt-dlp` errors | TikTok may be rate-limiting; wait a few minutes |
| Android timeout | Increase `readTimeout` in `RetrofitClient.kt` (currently 90 s) |
