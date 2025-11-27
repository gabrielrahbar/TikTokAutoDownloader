# 🎬 TikTok Auto Downloader

[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://www.python.org/)
[![Licence](https://img.shields.io/github/license/Ileriayo/markdown-badges?style=for-the-badge)](./LICENSE)
[![yt-dlp](https://img.shields.io/badge/yt--dlp-2023.10.0%2B-red?style=for-the-badge)](https://github.com/yt-dlp/yt-dlp)
[![Integration Tests](https://img.shields.io/github/actions/workflow/status/gabrielrahbar/TikTokAutoDownloader/scheduled_ci_workflow.yml?style=for-the-badge)](https://github.com/gabrielrahbar/TikTokAutoDownloader/actions/workflows/scheduled_ci_workflow.yml)


Automatically monitor TikTok users and intelligently download only new videos. Features timestamp-based tracking to avoid duplicates and anti-bot behavior to appear human-like.

## ✨ Features

- 🤖 **Automatic monitoring** - Periodically checks for new videos
- 🎯 **Smart timestamp filtering** - Downloads only truly new videos (no duplicates)
- 🗄️ **SQLite database** - Tracks downloaded videos and metadata
- 🌍 **Automatic geo-bypass** - Circumvents geographical restrictions
- 🍪 **Cookie support** - For restricted or private videos
- ⏱️ **Anti-bot delays** - Randomized delays between downloads
- 🔔 **Desktop notifications** - Get alerted when new videos are downloaded
- 📝 **Professional logging** - Detailed logs with file and console output
- 🔄 **Automatic retry** - Handles network errors and rate limiting
- 📊 **Reports & statistics** - View downloads, views, likes
- 👥 **Multi-user** - Monitor multiple users simultaneously
- 🎨 **Interactive menu** - User-friendly CLI with guided options
- 📁 **Organized downloads** - Files named by author and date
- ⚙️ **Configuration file** - Customize settings with config.yaml

## Highly Recommended

### VPN Usage

**Even if you're not in a restricted country, using a VPN is strongly recommended:**

- ✅ **Better privacy** - Masks your IP address from TikTok
- ✅ **Avoid rate limiting** - Reduces risk of temporary bans
- ✅ **Consistent downloads** - More stable connection to TikTok servers
- ✅ **Geographic diversity** - Access content from different regions

**Recommended VPN locations:**
- 🇺🇸 United States (best compatibility)
- 🇨🇦 Canada
- 🇩🇪 Germany

**IMPORTANT ⚠️ Detailed restrictions list:** [View complete country restrictions list](docs/restricted_countries.md)

**Note:** Restrictions change frequently. Some videos may be unavailable in specific regions regardless of country-level restrictions.

**Setup:**
```bash
# 1. Connect to VPN (USA recommended)
# 2. Run the monitor
python tiktok_monitor.py --auto --users username

# The built-in geo-bypass will work better with VPN active
## 🚀 Installation

### Requirements
- Python 3.7 or higher
- pip (Python package manager)

### Quick Setup

```bash
# 1. Clone the repository
git clone https://github.com/gabrielrahbar/TikTokAutoDownloader.git
cd TikTokAutoDownloader

# 2. Install dependencies
pip install -r requirements.txt

# 3. Verify installation
python check_installation.py
```

If you see this output, you're ready:
```
✅ EVERYTHING OK! Installation completed successfully!
```

## 📖 Usage

### Mode 1: Interactive Menu (Recommended)

The easiest way to get started:

```bash
python tiktok_monitor.py
```

You'll see this menu:

```
╔════════════════════════════════════════════════════════════╗
║              TikTok Monitor - Main Menu v2.3               ║
╚════════════════════════════════════════════════════════════╝

👥 USER MANAGEMENT
  1. ➕ Add user to monitor
  2. 📋 List monitored users
  3. ❌ Remove user from monitoring
  ...
```

**Example workflow:**
1. Choose `1` to add a user (e.g., `charlidamelio`)
2. Choose `7` to start automatic monitoring
3. The bot will check every 30 minutes [Default] (you can choose it) and download new videos

### Mode 2: Command Line (Advanced)

```bash
# Add users and start automatic monitoring (every 30 min)
python tiktok_monitor.py --auto --interval 30 --users charlidamelio khaby.lame

# Check once only (no loop)
python tiktok_monitor.py --check-once --users charlidamelio

# Show statistics
python tiktok_monitor.py --stats
```

### Mode 3: Manual single download

To download a single video:

```bash
# Basic download
python tiktok_downloader_advanced.py https://www.tiktok.com/@user/video/123456789

# With cookies (for geo-restrictions)
python tiktok_downloader_advanced.py --cookies tiktok_cookies.txt URL

# Show cookie export instructions
python tiktok_downloader_advanced.py --help-cookies
```

## 🛠️ User Management CLI

Quick script to manage users without interactive menu:

```bash
# List all monitored users
python manage_users.py --list

# Add new user
python manage_users.py --add username

# Remove user (disable)
python manage_users.py --remove username

# Permanently delete (with confirmation)
python manage_users.py --delete username

# Re-enable disabled user
python manage_users.py --enable username
```
## ⚙️ Configuration File

Customizable settings using a `config.yaml` file in the project root.

```yaml
monitor:
  interval_minutes: 30
  output_dir: "./tiktok_downloads"

download:
  quality: "best" 
  geo_bypass: true

notifications:
  enabled: false
```

## 📊 Reports & Statistics

View detailed download report:

```bash
python view_report.py
```

Example output:
```
╔════════════════════════════════════════════════════════════╗
║                  TikTok Monitor Report                     ║
╚════════════════════════════════════════════════════════════╝

📊 GENERAL STATISTICS
────────────────────────────────────────────────────────────
Downloaded videos:  142
Total views:        1,245,890
Total likes:        89,234

👥 BY AUTHOR
────────────────────────────────────────────────────────────
@charlidamelio         45 videos  |  890,234 views  |  67,123 likes
@khaby.lame           38 videos  |  234,567 views  |  12,345 likes
...
```

## 🍪 Setting Up Cookies (for geo-restrictions)

If you get errors like "Video not available in your country":

### Method 1: Browser Extension (Easiest)

1. Install **"Get cookies.txt LOCALLY"** extension
   - [Chrome Web Store](https://chrome.google.com/webstore)
   - [Firefox Add-ons](https://addons.mozilla.org)

2. Go to [tiktok.com](https://www.tiktok.com) and login

3. Click extension icon → `Export`

4. Save as `tiktok_cookies.txt`

5. Use cookies:
   ```bash
   python tiktok_downloader_advanced.py --cookies tiktok_cookies.txt URL
   ```

### Method 2: VPN (_Recommended_)

Connect to a VPN (USA/UK) before running downloads. The automatic geo-bypass will handle the rest.

## 📁 Main Project Structure

```
TikTokAutoDownloader/
├── tiktok_monitor.py              # 🤖 Main monitor with interactive menu
├── tiktok_downloader_advanced.py  # 📥 Standalone downloader
├── manage_users.py                # 👥 CLI user management
├── view_report.py                 # 📊 Reports and statistics
├── check_installation.py          # ✅ Installation verification
├── requirements.txt               # 📦 Python dependencies
├── README.md                      # 📖 This guide
├── LICENSE                        # ⚖️ MIT License
├── .gitignore                     # 🚫 Files to ignore
├── tiktok_downloads/              # 📁 Downloaded videos (auto-created)
└── tiktok_monitor.db              # 🗄️ SQLite database (auto-created)
```

## ⚙️ How It Works

### Timestamp Filtering System

The monitor uses an intelligent timestamp-based system:

1. **First run**: Saves the timestamp of the most recent video
2. **Subsequent checks**: Downloads only videos with timestamp > last saved
3. **Anti-duplicates**: Also checks database for safety
4. **Update**: Always saves the timestamp of the newest downloaded video

This prevents the "false new videos" problem that other scrapers have.

### Anti-Bot Behavior

To avoid TikTok bans:
- ⏱️ Randomized delays between downloads (5-15 seconds)
- 🎲 Delays between different users (10-30 seconds)
- 🌐 User-Agent rotation
- 📅 Variable check intervals (±10%)

### Database Schema

The SQLite database tracks:
- **videos**: id, url, title, author, timestamp, likes, views, file_path
- **monitored_users**: username, last_check, last_video_timestamp, total_videos

## 🔧 Troubleshooting

### Problem: "yt-dlp not found"
```bash
pip install --upgrade yt-dlp
```

### Problem: "Video not available in your country"
Use cookies (see Cookies section above) or connect to a VPN.

### Problem: "Database is locked"
Close all monitor instances before restarting:
```bash
# Linux/Mac
pkill -f tiktok_monitor.py

# Windows (Task Manager)
Search "python" and close the processes
```

### Problem: Slow downloads or timeouts
Increase timeout by modifying yt-dlp options in code or use a more stable connection.

### Problem: "Too many requests"
The bot is going too fast. Increase delays in `tiktok_monitor.py`:
```python
# Around line ~300
delay = random.uniform(10, 20)  # Increase these values
```

### Verify Installation
```bash
python check_installation.py
```

## 🤝 Contributing

Contributions are welcome! 

1. Fork the project
2. Create a branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## ⚠️ Legal Notice

**For personal and educational use only.**

- ⚖️ Respect TikTok's Terms of Service
- 📝 Video rights belong to their respective authors
- 🚫 Do not use to redistribute content without permission
- ⚠️ The author is not responsible for misuse of this software

## 📝 Changelog

### v2.0
- ✨ Added timestamp-based filtering (no more duplicates)
- 🎯 Limited check to last 5 videos per user
- 🛠️ Improved anti-bot with randomized delays
- 📊 Added `view_report.py` for statistics
- 👥 Added `manage_users.py` for CLI
- ✅ Added `check_installation.py`

### v1.0
- 🎉 Initial release
- 🤖 Basic automatic monitoring
- 📥 Download with geo-bypass

## 📬 Contact

**Author**: gabrielrahbar

- GitHub: [@gabrielrahbar](https://github.com/gabrielrahbar)
- Issues: [Report a problem](https://github.com/gabrielrahbar/TikTokAutoDownloader/issues)

## 📄 License

This project is released under the MIT License. See the [LICENSE](LICENSE) file for details.

---

⭐ **If this project is useful to you, leave a star on GitHub!** ⭐

Made with ❤️ by gabrielrahbar
