#!/usr/bin/env python3
"""
TikTok Monitor - Automatically monitor and download new TikTok videos
Tracks last seen video and downloads only truly new ones using timestamps
Version: 2.2 - Added retry logic, professional logging, and desktop notifications
"""

import yt_dlp
import json
import time
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random
import argparse
from logger_manager import logger
from retry_utils import retry_on_network_error, retry_on_api_error, RetryContext, wait_with_jitter
from notification_manager import notifier, notify_video


class TikTokMonitor:
    def __init__(self, output_dir="./tiktok_downloads", db_file="tiktok_monitor.db"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.db_file = db_file
        self.init_database()
        
        # Load notification preference from database
        self._load_notification_preference()
        
        logger.info(f"Monitor initialized")
        logger.debug(f"Output directory: {output_dir}")
        logger.debug(f"Database: {db_file}")
        logger.debug(f"Notifications: {notifier.get_status_text()}")

    def init_database(self):
        """Initialize SQLite database for tracking videos and settings"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        # Videos table
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

        # Monitored users table
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
        
        # Settings table (for notifications and other preferences)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        conn.commit()
        conn.close()
        logger.success("Database initialized")

    def _load_notification_preference(self):
        """Load notification preference from database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT value FROM settings WHERE key = ?', ('notifications_enabled',))
            result = cursor.fetchone()
            
            if result and result[0] == '1':
                notifier.enable()
            else:
                notifier.disable()
                
        except Exception as e:
            logger.debug(f"Could not load notification preference: {e}")
            notifier.disable()  # Default: disabled
        finally:
            conn.close()

    def _save_notification_preference(self):
        """Save notification preference to database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        try:
            value = '1' if notifier.enabled else '0'
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value)
                VALUES (?, ?)
            ''', ('notifications_enabled', value))
            conn.commit()
            logger.debug(f"Saved notification preference: {notifier.enabled}")
        except Exception as e:
            logger.error(f"Could not save notification preference: {e}")
        finally:
            conn.close()

    def toggle_notifications(self):
        """Toggle desktop notifications on/off"""
        if not notifier.is_available():
            logger.error("Desktop notifications not available")
            logger.info("Install with: pip install plyer")
            return False
        
        new_state = notifier.toggle()
        self._save_notification_preference()
        
        status = "enabled" if new_state else "disabled"
        logger.info(f"Desktop notifications {status}")
        
        # Send test notification if enabled
        if new_state:
            notifier.send(
                title="🔔 Notifications Enabled",
                message="You will be notified when new videos are downloaded",
                timeout=5
            )
        
        return new_state

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
            logger.user_added(username)
            return True
        except Exception as e:
            logger.error(f"Error adding user @{username}: {e}")
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
                logger.warning(f"User @{username} not found in monitoring")
                return False

            cursor.execute('UPDATE monitored_users SET enabled = 0 WHERE username = ?', (username,))
            conn.commit()
            logger.user_removed(username)
            return True
        except Exception as e:
            logger.error(f"Error removing user @{username}: {e}")
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
                    logger.info("Operation cancelled")
                    return False

            cursor.execute('DELETE FROM videos WHERE author = ?', (username,))
            cursor.execute('DELETE FROM monitored_users WHERE username = ?', (username,))

            conn.commit()
            logger.info(f"User @{username} and {video_count} videos deleted from database")
            return True
        except Exception as e:
            logger.error(f"Error deleting user @{username}: {e}")
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
                logger.info(f"User @{username} re-enabled")
                return True
            else:
                logger.warning(f"User @{username} not found")
                return False
        except Exception as e:
            logger.error(f"Error enabling user @{username}: {e}")
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
        logger.debug(f"Saved metadata for video {video_id}")

    @retry_on_api_error(max_retries=5)
    def get_user_videos(self, username, max_videos=5):
        """
        Get latest videos from a user profile with retry logic
        Uses yt-dlp to extract video list without downloading
        """
        url = f"https://www.tiktok.com/@{username}"

        ydl_opts = {
            'quiet': True,
            'extract_flat': False,  # Need full metadata for timestamps
            'playlistend': max_videos,
            'geo_bypass': True,
            'geo_bypass_country': 'US',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
            'skip_download': True,
            'socket_timeout': 30,
            'retries': 3,
        }

        try:
            logger.debug(f"Fetching videos for @{username}")
            
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
                    logger.debug(f"Found {len(videos)} videos for @{username}")
                    return videos
                return []
                
        except Exception as e:
            logger.error(f"Error fetching videos for @{username}: {e}")
            raise  # Re-raise for retry logic

    @retry_on_network_error(max_retries=3)
    def download_video(self, url):
        """Download a single video with retry logic"""
        ydl_opts = {
            'format': 'best',
            'outtmpl': str(self.output_dir / '%(uploader)s_%(upload_date)s_%(title)s.%(ext)s'),
            'quiet': True,
            'geo_bypass': True,
            'geo_bypass_country': 'US',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return info, filename
                
        except Exception as e:
            logger.error(f"Download error for {url}: {e}")
            raise  # Re-raise for retry logic

    def monitor_user(self, username, download_new=True):
        """
        Monitor a user and download new videos with retry logic
        Uses timestamp-based filtering to avoid false positives
        """
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"🔍 Checking @{username}...")
        logger.info("=" * 60)

        # Use RetryContext for the entire monitoring process
        with RetryContext(max_retries=3, delay_range=(30, 60)) as retry:
            while retry.should_retry():
                try:
                    # Get last known video timestamp
                    last_timestamp = self.get_last_video_timestamp(username)

                    if last_timestamp > 0:
                        last_date = datetime.fromtimestamp(last_timestamp)
                        logger.info(f"📅 Last check: {last_date.strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        logger.info("📅 First time monitoring this user")

                    # Get latest videos
                    logger.debug("Fetching video metadata...")
                    videos = self.get_user_videos(username)

                    if not videos:
                        logger.warning(f"No videos found for @{username}")
                        retry.success()
                        return 0

                    logger.info(f"📊 Found {len(videos)} recent videos")

                    # Filter new videos
                    new_videos = []
                    for video in videos:
                        video_timestamp = video.get('timestamp', 0)
                        
                        # Video is new if timestamp > last_timestamp OR not in database
                        if video_timestamp > last_timestamp or not self.is_video_downloaded(video['id']):
                            if video_timestamp > 0 and video_timestamp <= last_timestamp:
                                continue  # Skip: timestamp exists but is older
                            new_videos.append(video)

                    if not new_videos:
                        logger.info(f"✅ No new videos for @{username}")
                        retry.success()
                        return 0

                    logger.new_videos_found(len(new_videos), username)
                    
                    # Display new videos info
                    for i, video in enumerate(new_videos, 1):
                        video_date = datetime.fromtimestamp(video['timestamp']) if video['timestamp'] > 0 else None
                        date_str = video_date.strftime('%Y-%m-%d %H:%M') if video_date else 'Unknown date'
                        logger.info(f"   {i}. [{date_str}] {video['title'][:50]}")

                    downloaded = 0
                    newest_timestamp = last_timestamp

                    # Download new videos
                    for i, video in enumerate(new_videos, 1):
                        if download_new:
                            logger.info(f"\n📥 [{i}/{len(new_videos)}] Downloading: {video['title'][:50]}...")

                            # Anti-bot delay between downloads
                            if i > 1:
                                delay = random.uniform(5, 15)
                                logger.debug(f"Anti-bot delay: {delay:.1f}s")
                                time.sleep(delay)

                            try:
                                info, filepath = self.download_video(video['url'])

                                if info and filepath:
                                    self.save_video_metadata(info, filepath)
                                    downloaded += 1
                                    logger.download_complete(filepath, username)
                                    
                                    # Send desktop notification (if enabled)
                                    notify_video(
                                        username=username,
                                        title=info.get('title', 'Unknown'),
                                        views=info.get('view_count'),
                                        likes=info.get('like_count')
                                    )

                                    video_timestamp = info.get('timestamp', 0)
                                    if video_timestamp > newest_timestamp:
                                        newest_timestamp = video_timestamp
                                        
                            except Exception as e:
                                logger.download_failed(video['url'], username, str(e))
                                # Continue with other videos

                    # Update timestamp
                    if newest_timestamp > last_timestamp:
                        self.update_last_video_timestamp(username, newest_timestamp)
                        logger.debug(f"Updated timestamp: {datetime.fromtimestamp(newest_timestamp)}")

                    # Update total count
                    conn = sqlite3.connect(self.db_file)
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE monitored_users 
                        SET total_videos = total_videos + ?, last_check = ?
                        WHERE username = ?
                    ''', (downloaded, datetime.utcnow().isoformat(), username))
                    conn.commit()
                    conn.close()

                    logger.info(f"\n✅ Monitoring complete: {downloaded} new videos downloaded")
                    retry.success()
                    return downloaded
                    
                except Exception as e:
                    logger.error(f"Error monitoring @{username}: {e}", exc_info=True)
                    retry.failed(e)

        return 0

    def start_monitoring(self, interval_minutes=30, max_iterations=None):
        """
        Start continuous monitoring loop with retry logic
        
        Args:
            interval_minutes: Minutes between each check
            max_iterations: Maximum number of iterations (None = infinite)
        """
        users = self.get_monitored_users()

        if not users:
            logger.warning("No users to monitor!")
            logger.info("Add users with: monitor.add_user_to_monitor('username')")
            return

        logger.monitoring_start(users, interval_minutes)

        iteration = 0
        consecutive_errors = 0
        max_consecutive_errors = 5

        try:
            while True:
                iteration += 1
                logger.info("")
                logger.info("#" * 60)
                logger.info(f"🔄 Iteration #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info("#" * 60)

                total_downloaded = 0
                
                for username in users:
                    try:
                        logger.monitoring_check(iteration, username)
                        downloaded = self.monitor_user(username, download_new=True)
                        total_downloaded += downloaded
                        consecutive_errors = 0  # Reset on success

                        # Anti-bot delay between different users
                        if len(users) > 1:
                            delay = random.uniform(10, 30)
                            logger.debug(f"Delay before next user: {delay:.1f}s")
                            time.sleep(delay)
                            
                    except Exception as e:
                        logger.error(f"Failed to monitor @{username}: {e}")
                        consecutive_errors += 1
                        
                        if consecutive_errors >= max_consecutive_errors:
                            logger.critical(f"Too many consecutive errors ({consecutive_errors}). Stopping.")
                            raise

                print("")
                print("=" * 60)
                print(f"✅ Iteration #{iteration} completed")
                print(f"📥 New videos downloaded: {total_downloaded}")
                print("=" * 60)

                # Check if should stop
                if max_iterations and iteration >= max_iterations:
                    print(f"\n🏁 Reached limit of {max_iterations} iterations")
                    break

                # Calculate next check with random variation (±10%)
                base_wait = interval_minutes * 60
                next_check = datetime.now() + timedelta(seconds=base_wait)
                print(f"\n⏰ Next check: {next_check.strftime('%H:%M:%S')}")
                print(f"💤 Waiting {base_wait / 60:.1f} minutes...\n")
                
                wait_with_jitter(base_wait, jitter_percent=0.1)

        except KeyboardInterrupt:
            logger.info("\n\n⚠️  Monitoring interrupted by user")
            logger.info("👋 Goodbye!")

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

        logger.info("\n╔═══════════════════════════════════════════════════════════╗")
        logger.info("║                  Monitor Statistics                         ║")
        logger.info("╚═══════════════════════════════════════════════════════════╝")
        logger.info(f"\n📊 Total videos downloaded: {total_videos}")
        logger.info(f"👥 Monitored users: {total_users}")

        if top_authors:
            logger.info(f"\n🏆 Top Authors:")
            for i, (author, count) in enumerate(top_authors, 1):
                logger.info(f"   {i}. @{author}: {count} videos")


def interactive_menu(monitor):
    """Interactive menu with user management and notifications"""
    while True:
        print(" ╔═══════════════════════════════════════════════════════════╗")
        print(" ║              TikTok Monitor - Main Menu v2.2              ║")
        print(" ║                                                           ║")
        print(" ╚═══════════════════════════════════════════════════════════╝")
        print("\n👥 USER MANAGEMENT")
        print("  1. ➕ Add user to monitor")
        print("  2. 📋 List monitored users")
        print("  3. ❌ Remove user from monitoring")
        print("  4. 🗑️  Delete user permanently")
        print("  5. ♻️  Re-enable disabled user")
        print("\n🔍 MONITORING")
        print("  6. 🔍 Check for new videos (once)")
        print("  7. 🤖 Start automatic monitoring")
        print("\n📊 STATISTICS & SETTINGS")
        print("  8. 📊 Show statistics")
        print(f"  9. 🔔 Toggle notifications (currently: {notifier.get_status_text()})")
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
                print(f"{'Username':<20} {'Status':<12} {'Last Check':<20} {'Last Timestamp':<20} {'Total':<8} {'In DB':<8}")
                print(f"{'=' * 100}")

                for username, last_check, total, enabled, last_ts, db_videos in users:
                    status = "🟢 Active" if enabled else "🔴 Disabled"
                    last_check_str = datetime.fromisoformat(last_check).strftime('%d/%m/%Y %H:%M') if last_check else 'Never'
                    last_ts_str = datetime.fromtimestamp(last_ts).strftime('%d/%m/%Y %H:%M') if last_ts > 0 else 'None'
                    print(f"@{username:<19} {status:<12} {last_check_str:<20} {last_ts_str:<20} {total:<8} {db_videos:<8}")

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
            monitor.start_monitoring(interval_minutes=interval)

        elif choice == '8':
            monitor.get_stats()

        elif choice == '9':
            monitor.toggle_notifications()

        elif choice == '0':
            logger.info("👋 Goodbye!")
            break

        else:
            print("\n❌ Invalid choice!")


def main():
    """Main function with interactive menu"""
    parser = argparse.ArgumentParser(
        description='TikTok Monitor v2.2 - With automatic retry, logging, and notifications',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  %(prog)s

  # Start automatic monitoring
  %(prog)s --auto --interval 30 --users charlidamelio khaby.lame

  # Check once only
  %(prog)s --check-once --users charlidamelio

  # Show statistics
  %(prog)s --stats

Features:
  - Automatic retry on network/API errors
  - Professional logging (logs/ folder)
  - Desktop notifications (enable from menu option 9)
  - Timestamp-based filtering (no duplicates)
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
            logger.warning("No users to monitor!")
            return

        for username in users:
            monitor.monitor_user(username)

    else:
        interactive_menu(monitor)


if __name__ == "__main__":
    main()
