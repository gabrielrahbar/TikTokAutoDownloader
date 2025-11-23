#!/usr/bin/env python3
"""
TikTok Monitor - Automatically monitor and download new TikTok videos
Tracks last seen video and downloads only truly new ones using timestamps
Version: 2.0 - Added timestamp-based filtering
"""

import yt_dlp
import json
import time
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random
import argparse


class TikTokMonitor:
    def __init__(self, output_dir="./tiktok_downloads", db_file="tiktok_monitor.db"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.db_file = db_file
        self.init_database()

    def init_database(self):
        """Initialize SQLite database for tracking videos"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                title TEXT,
                author TEXT,
                upload_date TEXT,
                upload_timestamp INTEGER,
                download_date TEXT,
                file_path TEXT,
                likes INTEGER,
                views INTEGER,
                status TEXT DEFAULT 'downloaded'
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitored_users (
                username TEXT PRIMARY KEY,
                last_check TEXT,
                last_video_id TEXT,
                last_video_timestamp INTEGER,
                total_videos INTEGER DEFAULT 0,
                enabled INTEGER DEFAULT 1
            )
        ''')

        conn.commit()
        conn.close()
        print(f"✅ Database initialized: {self.db_file}")

    def add_user_to_monitor(self, username):
        """Add a user to monitoring list"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR IGNORE INTO monitored_users (username, last_check, last_video_timestamp)
                VALUES (?, ?, ?)
            ''', (username, datetime.utcnow().isoformat(), 0))
            conn.commit()
            print(f"✅ User @{username} added to monitoring")
            return True
        except Exception as e:
            print(f"❌ Error adding user: {e}")
            return False
        finally:
            conn.close()

    def remove_user_from_monitor(self, username):
        """Remove a user from monitoring (disable)"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT username FROM monitored_users WHERE username = ?', (username,))
            if cursor.fetchone() is None:
                print(f"⚠️  User @{username} not found in monitoring")
                return False

            cursor.execute('UPDATE monitored_users SET enabled = 0 WHERE username = ?', (username,))
            conn.commit()
            print(f"✅ User @{username} removed from monitoring")
            return True
        except Exception as e:
            print(f"❌ Error removing user: {e}")
            return False
        finally:
            conn.close()

    def delete_user_permanently(self, username):
        """Permanently delete a user and their videos from database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT COUNT(*) FROM videos WHERE author = ?', (username,))
            video_count = cursor.fetchone()[0]

            if video_count > 0:
                confirm = input(f"\n⚠️  This will delete {video_count} videos of @{username} from database.\n"
                                f"Downloaded files will NOT be deleted.\n"
                                f"Confirm? (y/n): ")
                if confirm.lower() != 'y':
                    print("❌ Operation cancelled")
                    return False

            cursor.execute('DELETE FROM videos WHERE author = ?', (username,))
            cursor.execute('DELETE FROM monitored_users WHERE username = ?', (username,))

            conn.commit()
            print(f"✅ User @{username} and {video_count} videos deleted from database")
            return True
        except Exception as e:
            print(f"❌ Error deleting user: {e}")
            return False
        finally:
            conn.close()

    def enable_user(self, username):
        """Re-enable a previously disabled user"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        try:
            cursor.execute('UPDATE monitored_users SET enabled = 1 WHERE username = ?', (username,))
            if cursor.rowcount > 0:
                conn.commit()
                print(f"✅ User @{username} re-enabled")
                return True
            else:
                print(f"⚠️  User @{username} not found")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        finally:
            conn.close()

    def list_monitored_users(self, show_disabled=False):
        """List monitored users with details"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        query = '''
            SELECT 
                m.username, 
                m.last_check, 
                m.total_videos, 
                m.enabled,
                m.last_video_timestamp,
                COUNT(v.id) as db_videos
            FROM monitored_users m
            LEFT JOIN videos v ON m.username = v.author
        '''

        if not show_disabled:
            query += ' WHERE m.enabled = 1'

        query += ' GROUP BY m.username ORDER BY m.total_videos DESC'

        cursor.execute(query)
        users = cursor.fetchall()
        conn.close()

        return users

    def get_monitored_users(self):
        """Get list of active monitored users"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM monitored_users WHERE enabled = 1')
        users = [row[0] for row in cursor.fetchall()]
        conn.close()
        return users

    def get_last_video_timestamp(self, username):
        """Get timestamp of last seen video for a user"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT last_video_timestamp FROM monitored_users WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0

    def update_last_video_timestamp(self, username, timestamp):
        """Update the last seen video timestamp for a user"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE monitored_users 
            SET last_video_timestamp = ?, last_check = ?
            WHERE username = ?
        ''', (timestamp, datetime.utcnow().isoformat(), username))
        conn.commit()
        conn.close()

    def is_video_downloaded(self, video_id):
        """Check if a video has already been downloaded"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM videos WHERE id = ?', (video_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def save_video_metadata(self, video_info, file_path):
        """Save video metadata to database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        video_id = video_info.get('id', '')

        cursor.execute('''
            INSERT OR REPLACE INTO videos 
            (id, url, title, author, upload_date, upload_timestamp, download_date, file_path, likes, views)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            video_id,
            video_info.get('webpage_url', ''),
            video_info.get('title', ''),
            video_info.get('uploader', ''),
            video_info.get('upload_date', ''),
            video_info.get('timestamp', 0),
            datetime.utcnow().isoformat(),
            str(file_path),
            video_info.get('like_count', 0),
            video_info.get('view_count', 0)
        ))

        conn.commit()
        conn.close()

    def get_user_videos(self, username, max_videos=5):
        """
        Get latest videos from a user profile
        Uses yt-dlp to extract video list without downloading

        IMPORTANT: extract_flat=False to get reliable timestamps
        This is slower but necessary for accurate timestamp filtering
        """
        url = f"https://www.tiktok.com/@{username}"

        ydl_opts = {
            'quiet': True,
            'extract_flat': False,  # CHANGED: Need full metadata for timestamps
            'playlistend': max_videos,
            'geo_bypass': True,
            'geo_bypass_country': 'US',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
            'skip_download': True,  # Don't download, just extract info
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if 'entries' in info:
                    videos = []
                    for entry in info['entries']:
                        if entry:
                            videos.append({
                                'id': entry.get('id', ''),
                                'url': entry.get('webpage_url', ''),
                                'title': entry.get('title', ''),
                                'timestamp': entry.get('timestamp', 0),
                                'upload_date': entry.get('upload_date', ''),
                            })
                    # Sort by timestamp descending (newest first)
                    videos.sort(key=lambda x: x['timestamp'], reverse=True)
                    return videos
                return []
        except Exception as e:
            print(f"⚠️  Error getting videos from @{username}: {e}")
            return []

    def download_video(self, url):
        """Download a single video"""
        ydl_opts = {
            'format': 'best',
            'outtmpl': str(self.output_dir / '%(uploader)s_%(upload_date)s_%(title)s.%(ext)s'),
            'quiet': False,
            'geo_bypass': True,
            'geo_bypass_country': 'US',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return info, filename
        except Exception as e:
            print(f"❌ Download error: {e}")
            return None, None

    def monitor_user(self, username, download_new=True):
        """
        Monitor a user and download new videos
        Uses timestamp-based filtering to avoid false positives
        """
        print(f"\n{'=' * 60}")
        print(f"🔍 Checking @{username}...")
        print(f"{'=' * 60}")

        # Get last known video timestamp
        last_timestamp = self.get_last_video_timestamp(username)

        if last_timestamp > 0:
            last_date = datetime.fromtimestamp(last_timestamp)
            print(f"📅 Last check timestamp: {last_date.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"📅 First time monitoring this user")

        # Get latest videos (this is slower with extract_flat=False but more accurate)
        print(f"⏳ Fetching video metadata (may take 10-15 seconds)...")
        videos = self.get_user_videos(username)

        if not videos:
            print(f"⚠️  No videos found for @{username}")
            return 0

        print(f"📊 Found {len(videos)} recent videos")

        # Filter videos newer than last check
        new_videos = []
        for video in videos:
            video_timestamp = video.get('timestamp', 0)

            # Video is new if:
            # 1. It has a timestamp newer than our last check, OR
            # 2. It's not in our database (fallback for first run or missing timestamps)
            if video_timestamp > last_timestamp or not self.is_video_downloaded(video['id']):
                # Double check: if timestamp is valid, use it; otherwise rely on DB check only
                if video_timestamp > 0 and video_timestamp <= last_timestamp:
                    continue  # Skip: timestamp exists but is older
                new_videos.append(video)

        if not new_videos:
            print(f"✅ No new videos for @{username}")
            return 0

        # Display new videos info
        print(f"\n🆕 {len(new_videos)} new video(s) to download:")
        for i, video in enumerate(new_videos, 1):
            video_date = datetime.fromtimestamp(video['timestamp']) if video['timestamp'] > 0 else None
            date_str = video_date.strftime('%Y-%m-%d %H:%M') if video_date else 'Unknown date'
            print(f"   {i}. [{date_str}] {video['title'][:50]}")

        downloaded = 0
        newest_timestamp = last_timestamp

        for i, video in enumerate(new_videos, 1):
            if download_new:
                print(f"\n📥 [{i}/{len(new_videos)}] Downloading: {video['title'][:50]}...")

                # Anti-bot delay between downloads
                if i > 1:
                    delay = random.uniform(5, 15)
                    print(f"⏳ Waiting {delay:.1f}s to avoid bot detection...")
                    time.sleep(delay)

                info, filepath = self.download_video(video['url'])

                if info and filepath:
                    self.save_video_metadata(info, filepath)
                    downloaded += 1
                    print(f"✅ Downloaded: {filepath}")

                    # Track newest timestamp
                    video_timestamp = info.get('timestamp', 0)
                    if video_timestamp > newest_timestamp:
                        newest_timestamp = video_timestamp
            else:
                print(f"ℹ️  New video found: {video['title'][:50]}")

        # Update last seen timestamp
        if newest_timestamp > last_timestamp:
            self.update_last_video_timestamp(username, newest_timestamp)
            print(
                f"\n📌 Updated last check timestamp: {datetime.fromtimestamp(newest_timestamp).strftime('%Y-%m-%d %H:%M:%S')}")

        # Update total video count
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE monitored_users 
            SET total_videos = total_videos + ?, last_check = ?
            WHERE username = ?
        ''', (downloaded, datetime.utcnow().isoformat(), username))
        conn.commit()
        conn.close()

        return downloaded

    def start_monitoring(self, interval_minutes=30, max_iterations=None):
        """
        Start continuous monitoring loop

        Args:
            interval_minutes: Minutes between each check
            max_iterations: Maximum number of iterations (None = infinite)
        """
        users = self.get_monitored_users()

        if not users:
            print("⚠️  No users to monitor!")
            print("Use: monitor.add_user_to_monitor('username')")
            return

        print("╔════════════════════════════════════════════════════════════╗")
        print("║       TikTok Monitor - Automatic Monitoring (v2.0)         ║")
        print("║          With Timestamp-Based Filtering (Last 5)           ║")
        print("╚════════════════════════════════════════════════════════════╝")
        print(f"\n📋 Monitored users: {', '.join('@' + u for u in users)}")
        print(f"⏰ Check interval: {interval_minutes} minutes")
        print(f"📹 Videos checked: last 5 per user")
        print(f"🎯 Filter method: timestamp-based (accurate)")
        print(f"📁 Output: {self.output_dir}")
        print(f"\n🚀 Starting monitoring...\n")

        iteration = 0
        try:
            while True:
                iteration += 1
                print(f"\n{'#' * 60}")
                print(f"🔄 Iteration #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'#' * 60}")

                total_downloaded = 0
                for username in users:
                    downloaded = self.monitor_user(username, download_new=True)
                    total_downloaded += downloaded

                    # Anti-bot delay between different users
                    if len(users) > 1:
                        delay = random.uniform(10, 30)
                        print(f"\n⏳ Pause {delay:.1f}s before next user...")
                        time.sleep(delay)

                print(f"\n{'=' * 60}")
                print(f"✅ Iteration #{iteration} completed")
                print(f"📥 New videos downloaded: {total_downloaded}")
                print(f"{'=' * 60}")

                # Check if we should stop
                if max_iterations and iteration >= max_iterations:
                    print(f"\n🏁 Reached limit of {max_iterations} iterations")
                    break

                # Calculate next check with random variation (±10%)
                base_wait = interval_minutes * 60
                random_variation = random.uniform(-0.1, 0.1) * base_wait
                wait_seconds = base_wait + random_variation

                next_check = datetime.now() + timedelta(seconds=wait_seconds)
                print(f"\n⏰ Next check: {next_check.strftime('%H:%M:%S')}")
                print(f"💤 Waiting {wait_seconds / 60:.1f} minutes...\n")

                time.sleep(wait_seconds)

        except KeyboardInterrupt:
            print("\n\n⚠️  Monitoring interrupted by user")
            print("👋 Goodbye!")

    def get_stats(self):
        """Display statistics"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM videos')
        total_videos = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM monitored_users WHERE enabled = 1')
        total_users = cursor.fetchone()[0]

        cursor.execute('''
            SELECT author, COUNT(*) as count 
            FROM videos 
            GROUP BY author 
            ORDER BY count DESC 
            LIMIT 5
        ''')
        top_authors = cursor.fetchall()

        conn.close()

        print("\n╔════════════════════════════════════════════════════════════╗")
        print("║                  Monitor Statistics                         ║")
        print("║              (Timestamp-based filtering)                    ║")
        print("╚════════════════════════════════════════════════════════════╝")
        print(f"\n📊 Total videos downloaded: {total_videos}")
        print(f"👥 Monitored users: {total_users}")

        if top_authors:
            print(f"\n🏆 Top Authors:")
            for i, (author, count) in enumerate(top_authors, 1):
                print(f"   {i}. @{author}: {count} videos")

        print()


def interactive_menu(monitor):
    """Interactive menu with user management"""
    while True:
        print("\n╔════════════════════════════════════════════════════════════╗")
        print("║              TikTok Monitor - Main Menu v2.0               ║")
        print("║         (Timestamp filtering - last 5 per user)            ║")
        print("╚════════════════════════════════════════════════════════════╝")
        print("\n👥 USER MANAGEMENT")
        print("  1. ➕ Add user to monitor")
        print("  2. 📋 List monitored users")
        print("  3. ❌ Remove user from monitoring")
        print("  4. 🗑️  Delete user permanently")
        print("  5. ♻️  Re-enable disabled user")
        print("\n🔍 MONITORING")
        print("  6. 🔍 Check for new videos (once)")
        print("  7. 🤖 Start automatic monitoring")
        print("\n📊 STATISTICS")
        print("  8. 📊 Show statistics")
        print("\n  0. 🚪 Exit")
        print()

        choice = input("Choice: ").strip()

        if choice == '1':
            username = input("\nEnter username (without @): ").strip().lstrip('@')
            if username:
                monitor.add_user_to_monitor(username)

        elif choice == '2':
            show_all = input("\nShow disabled users too? (y/n) [n]: ").strip().lower() == 'y'
            users = monitor.list_monitored_users(show_disabled=show_all)

            if users:
                print(f"\n{'=' * 100}")
                print(
                    f"{'Username':<20} {'Status':<12} {'Last Check':<20} {'Last Timestamp':<20} {'Total':<8} {'In DB':<8}")
                print(f"{'=' * 100}")

                for username, last_check, total, enabled, last_ts, db_videos in users:
                    status = "🟢 Active" if enabled else "🔴 Disabled"
                    last_check_str = datetime.fromisoformat(last_check).strftime(
                        '%d/%m/%Y %H:%M') if last_check else 'Never'
                    last_ts_str = datetime.fromtimestamp(last_ts).strftime('%d/%m/%Y %H:%M') if last_ts > 0 else 'None'

                    print(
                        f"@{username:<19} {status:<12} {last_check_str:<20} {last_ts_str:<20} {total:<8} {db_videos:<8}")

                print(f"{'=' * 100}")
                print(f"Total: {len(users)} users")
            else:
                print("\n⚠️  No monitored users")

        elif choice == '3':
            username = input("\nUsername to remove (without @): ").strip().lstrip('@')
            if username:
                monitor.remove_user_from_monitor(username)

        elif choice == '4':
            username = input("\nUsername to DELETE PERMANENTLY (without @): ").strip().lstrip('@')
            if username:
                monitor.delete_user_permanently(username)

        elif choice == '5':
            username = input("\nUsername to re-enable (without @): ").strip().lstrip('@')
            if username:
                monitor.enable_user(username)

        elif choice == '6':
            users = [u[0] for u in monitor.list_monitored_users() if u[3] == 1]
            if not users:
                print("\n⚠️  Add users to monitor first!")
            else:
                for username in users:
                    monitor.monitor_user(username)

        elif choice == '7':
            interval = input("\nMinutes between checks [30]: ").strip()
            interval = int(interval) if interval.isdigit() else 30
            print(f"\n💡 Will check last 5 videos per user using timestamp filtering")
            monitor.start_monitoring(interval_minutes=interval)

        elif choice == '8':
            monitor.get_stats()

        elif choice == '0':
            print("\n👋 Goodbye!")
            break

        else:
            print("\n❌ Invalid choice!")


def main():
    """Main function with interactive menu"""
    parser = argparse.ArgumentParser(
        description='TikTok Monitor v2.0 - Timestamp-based filtering (last 5 videos)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add users and start interactive monitoring
  %(prog)s

  # Start automatic monitoring (check every 30 min)
  %(prog)s --auto --interval 30 --users charlidamelio khaby.lame

  # Check once only
  %(prog)s --check-once --users charlidamelio

  # Show statistics
  %(prog)s --stats

NOTE: Monitor automatically checks only last 5 videos per user with timestamp filtering.
This prevents "false new" videos from appearing on subsequent checks.
        """
    )

    parser.add_argument('--auto', action='store_true',
                        help='Start continuous automatic monitoring')
    parser.add_argument('--interval', type=int, default=30,
                        help='Minutes between checks (default: 30)')
    parser.add_argument('--users', nargs='+',
                        help='Users to monitor (without @)')
    parser.add_argument('--check-once', action='store_true',
                        help='Check once and exit')
    parser.add_argument('--stats', action='store_true',
                        help='Show statistics and exit')
    parser.add_argument('-o', '--output', default='./tiktok_downloads',
                        help='Output folder (default: ./tiktok_downloads)')

    args = parser.parse_args()

    monitor = TikTokMonitor(output_dir=args.output)

    if args.stats:
        monitor.get_stats()
        return

    if args.users:
        for username in args.users:
            monitor.add_user_to_monitor(username.lstrip('@'))

    if args.auto:
        monitor.start_monitoring(interval_minutes=args.interval)

    elif args.check_once:
        users = monitor.get_monitored_users()
        if not users:
            print("⚠️  No users to monitor!")
            return

        for username in users:
            monitor.monitor_user(username)

    else:
        interactive_menu(monitor)


if __name__ == "__main__":
    main()