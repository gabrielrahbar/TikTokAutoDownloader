#!/usr/bin/env python3
"""
TikTok Monitor - Automatically monitor and download new TikTok videos
Tracks last seen video and downloads only truly new ones using timestamps
Version: 2.5 - Auto-stop when all users fail with non-retryable errors
"""

import yt_dlp
import json
import time
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random
import argparse
import os
import sys
import subprocess
from logger_manager import logger
from retry_utils import retry_on_network_error, retry_on_api_error, RetryContext, wait_with_jitter
from notification_manager import notifier, notify_video
from config_manager import get_config
from error_handler import ErrorHandler, handle_error, is_retryable_error, get_retry_wait_time
from daemon_manager import daemon


class TikTokMonitor:
    def __init__(self, output_dir=None, db_file=None):
        # Use config if not specified
        if output_dir is None:
            output_dir = get_config('monitor.output_dir', './tiktok_downloads')
        if db_file is None:
            db_file = get_config('database.db_file', 'tiktok_monitor.db')

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
                           INSERT
                           OR IGNORE INTO monitored_users (username, last_check, last_video_timestamp)
                VALUES (?, ?, ?)
                           ''', (username, datetime.now().isoformat(), 0))
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
                       SET last_video_timestamp = ?,
                           last_check           = ?
                       WHERE username = ?
                       ''', (timestamp, datetime.now().isoformat(), username))
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
            datetime.now().isoformat(),
            str(file_path),
            video_info.get('like_count', 0),
            video_info.get('view_count', 0)
        ))

        conn.commit()
        conn.close()
        logger.debug(f"Saved metadata for video {video_id}")

    def get_user_videos(self, username, max_videos=None):
        """
        Get latest videos from a user profile with user-friendly error handling

        Returns:
            tuple: (videos_list, error_object or None)
        """
        if max_videos is None:
            max_videos = get_config('monitor.max_videos_per_check', 5)

        url = f"https://www.tiktok.com/@{username}"

        ydl_opts = {
            'quiet': True,
            'extract_flat': False,
            'playlistend': max_videos,
            'geo_bypass': get_config('download.geo_bypass', True),
            'geo_bypass_country': get_config('download.geo_bypass_country', 'US'),
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
            'skip_download': True,
            'socket_timeout': 30,
            'retries': 3,
        }

        max_retries = 3
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(f"Fetching videos for @{username} (attempt {attempt}/{max_retries})")

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
                        videos.sort(key=lambda x: x['timestamp'], reverse=True)
                        logger.debug(f"Found {len(videos)} videos for @{username}")
                        return videos, None
                    return [], None

            except Exception as e:
                user_error = handle_error(e, url, username, show_technical=(attempt == max_retries))
                last_error = user_error

                if attempt < max_retries and is_retryable_error(user_error):
                    wait_time = get_retry_wait_time(user_error)
                    logger.warning(f"⏳ Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Failed to fetch videos for @{username}")
                    return [], last_error

        return [], last_error

    def download_video(self, url, username=None):
        """
        Download a single video with user-friendly error handling

        Returns:
            tuple: (info, filepath, error_object or None)
        """
        ydl_opts = {
            'format': get_config('download.quality', 'best'),
            'outtmpl': str(self.output_dir / '%(uploader)s_%(upload_date)s_%(title)s.%(ext)s'),
            'quiet': True,
            'geo_bypass': get_config('download.geo_bypass', True),
            'geo_bypass_country': get_config('download.geo_bypass_country', 'US'),
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
        }

        max_retries = 3
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                if attempt > 1:
                    logger.info(f"🔄 Retry attempt {attempt}/{max_retries}")

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    return info, filename, None

            except Exception as e:
                user_error = handle_error(e, url, username, show_technical=(attempt == max_retries))
                last_error = user_error

                if attempt < max_retries and is_retryable_error(user_error):
                    wait_time = get_retry_wait_time(user_error)
                    logger.warning(f"⏳ Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    if not is_retryable_error(user_error):
                        logger.error("❌ This error cannot be automatically resolved - skipping video")
                    return None, None, last_error

        return None, None, last_error

    def monitor_user(self, username, download_new=True):
        """
        Monitor a user and download new videos with user-friendly error handling

        Returns:
            tuple: (downloaded_count, error_object or None)
        """
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"🔍 Checking @{username}...")
        logger.info("=" * 60)

        try:
            # Get last check time from database
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('SELECT last_check FROM monitored_users WHERE username = ?', (username,))
            result = cursor.fetchone()
            conn.close()

            if result and result[0]:
                last_check_time = datetime.fromisoformat(result[0])
                logger.info(f"📅 Last check: {last_check_time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                logger.info("📅 First time monitoring this user")

            last_timestamp = self.get_last_video_timestamp(username)

            # Get latest videos
            logger.debug("Fetching video metadata...")
            videos, fetch_error = self.get_user_videos(username)

            if fetch_error:
                # Update last_check even on error
                conn = sqlite3.connect(self.db_file)
                cursor = conn.cursor()
                cursor.execute('''
                               UPDATE monitored_users
                               SET last_check = ?
                               WHERE username = ?
                               ''', (datetime.now().isoformat(), username))
                conn.commit()
                conn.close()

                return 0, fetch_error

            if not videos:
                logger.warning(f"No videos found for @{username}")

                # Update last_check
                conn = sqlite3.connect(self.db_file)
                cursor = conn.cursor()
                cursor.execute('''
                               UPDATE monitored_users
                               SET last_check = ?
                               WHERE username = ?
                               ''', (datetime.now().isoformat(), username))
                conn.commit()
                conn.close()

                return 0, None

            logger.info(f"📊 Found {len(videos)} recent videos")

            # Filter new videos
            new_videos = []
            for video in videos:
                video_timestamp = video.get('timestamp', 0)

                if video_timestamp > last_timestamp or not self.is_video_downloaded(video['id']):
                    if video_timestamp > 0 and video_timestamp <= last_timestamp:
                        continue
                    new_videos.append(video)

            if not new_videos:
                logger.info(f"✅ No new videos for @{username}")

                # Update last_check
                conn = sqlite3.connect(self.db_file)
                cursor = conn.cursor()
                cursor.execute('''
                               UPDATE monitored_users
                               SET last_check = ?
                               WHERE username = ?
                               ''', (datetime.now().isoformat(), username))
                conn.commit()
                conn.close()

                return 0, None

            logger.new_videos_found(len(new_videos), username)

            # Display new videos
            for i, video in enumerate(new_videos, 1):
                video_date = datetime.fromtimestamp(video['timestamp']) if video['timestamp'] > 0 else None
                date_str = video_date.strftime('%Y-%m-%d %H:%M') if video_date else 'Unknown date'
                logger.info(f"   {i}. [{date_str}] {video['title'][:50]}")

            downloaded = 0
            newest_timestamp = last_timestamp
            download_error = None

            # Download new videos
            for i, video in enumerate(new_videos, 1):
                if download_new:
                    logger.info(f"\n📥 [{i}/{len(new_videos)}] Downloading: {video['title'][:50]}...")

                    # Anti-bot delay
                    if i > 1:
                        delays = get_config('monitor.anti_bot_delays.between_downloads', [5, 15])
                        delay = random.uniform(delays[0], delays[1])
                        logger.debug(f"Anti-bot delay: {delay:.1f}s")
                        time.sleep(delay)

                    info, filepath, error = self.download_video(video['url'], username)

                    if error:
                        download_error = error
                        logger.warning(f"⚠️  Skipping video due to error")
                        continue

                    if info and filepath:
                        self.save_video_metadata(info, filepath)
                        downloaded += 1
                        logger.download_complete(filepath, username)

                        # Send notification
                        notify_video(
                            username=username,
                            title=info.get('title', 'Unknown'),
                            views=info.get('view_count'),
                            likes=info.get('like_count')
                        )

                        video_timestamp = info.get('timestamp', 0)
                        if video_timestamp > newest_timestamp:
                            newest_timestamp = video_timestamp
                    else:
                        logger.warning(f"⚠️  Skipping video due to error")

            # Update timestamp and count
            if newest_timestamp > last_timestamp:
                self.update_last_video_timestamp(username, newest_timestamp)
                logger.debug(f"Updated timestamp: {datetime.fromtimestamp(newest_timestamp)}")

            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('''
                           UPDATE monitored_users
                           SET total_videos = total_videos + ?,
                               last_check   = ?
                           WHERE username = ?
                           ''', (downloaded, datetime.now().isoformat(), username))
            conn.commit()
            conn.close()

            logger.info(f"\n✅ Monitoring complete: {downloaded}/{len(new_videos)} videos downloaded successfully")
            return downloaded, download_error

        except Exception as e:
            logger.error(f"Error monitoring @{username}: {e}", exc_info=True)
            return 0, None

    def start_monitoring(self, interval_minutes=None, max_iterations=None):
        """Start continuous monitoring loop with auto-stop on persistent failures"""
        if interval_minutes is None:
            interval_minutes = get_config('monitor.interval_minutes', 30)

        users = self.get_monitored_users()

        if not users:
            logger.warning("No users to monitor!")
            logger.info("Add users with: monitor.add_user_to_monitor('username')")
            return

        logger.monitoring_start(users, interval_minutes)

        iteration = 0
        consecutive_all_failed = 0  # Track consecutive iterations where ALL users failed
        max_consecutive_all_failed = 1 # Stop after 1 consecutive complete failures

        try:
            while True:
                iteration += 1
                logger.info("")
                logger.info("#" * 60)
                logger.info(f"🔄 Iteration #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info("#" * 60)

                total_downloaded = 0
                failed_users = []
                non_retryable_errors = []

                for username in users:
                    try:
                        logger.monitoring_check(iteration, username)
                        downloaded, error = self.monitor_user(username, download_new=True)
                        total_downloaded += downloaded

                        # Check if user failed with error (any kind)
                        if error:
                            failed_users.append(username)
                            # Track specifically non-retryable errors for reporting
                            if not is_retryable_error(error):
                                non_retryable_errors.append((username, error))

                        # Anti-bot delay between users
                        if len(users) > 1:
                            delays = get_config('monitor.anti_bot_delays.between_users', [10, 30])
                            delay = random.uniform(delays[0], delays[1])
                            logger.debug(f"Delay before next user: {delay:.1f}s")
                            time.sleep(delay)

                    except Exception as e:
                        logger.error(f"Failed to monitor @{username}: {e}")
                        failed_users.append(username)

                # Check if ALL users failed with non-retryable errors
                if len(failed_users) == len(users) and len(users) > 0:
                    consecutive_all_failed += 1

                    logger.warning("")
                    logger.warning("=" * 60)
                    logger.warning(f"⚠️  ALL {len(users)} users failed this iteration")
                    logger.warning(f"Consecutive failures: {consecutive_all_failed}/{max_consecutive_all_failed}")
                    logger.warning("=" * 60)

                    # Show error summary
                    if non_retryable_errors:
                        logger.warning("\n📋 Error Summary:")
                        for user, err in non_retryable_errors:
                            logger.warning(f"   @{user}: {err.error_type}")

                    # Send notification on first failure
                    if consecutive_all_failed == 1:
                        notifier.send(
                            title="⚠️ All Users Failed",
                            message=f"All {len(users)} users failed (cookies/geo-block?)\nCheck logs or fix issues",
                            timeout=0
                        )

                    # Stop monitoring after consecutive failures
                    if consecutive_all_failed >= max_consecutive_all_failed:
                        logger.critical("")
                        logger.critical("=" * 60)
                        logger.critical("🛑 STOPPING MONITOR")
                        logger.critical(f"All users failed for {consecutive_all_failed} consecutive iterations")
                        logger.critical("=" * 60)
                        logger.critical("")
                        logger.critical("💡 Common solutions:")
                        logger.critical("   1. Connect to a VPN (USA/Canada/Germany)")
                        logger.critical("   2. Export cookies from TikTok")
                        logger.critical("      Run: python tiktok_downloader_advanced.py --help-cookies")
                        logger.critical("   3. Check if usernames are correct")
                        logger.critical("   4. Wait a few hours and try again")
                        logger.critical("")

                        # Send critical notification
                        notifier.send(
                            title="🛑 Monitor STOPPED",
                            message=f"All users failed {consecutive_all_failed} times\nUse VPN or export cookies",
                            timeout=0
                        )

                        # Exit immediately - don't raise, just return
                        return
                else:
                    # Reset counter if at least one user succeeded
                    consecutive_all_failed = 0

                print("")
                print("=" * 60)
                print(f"✅ Iteration #{iteration} completed")
                print(f"📥 New videos downloaded: {total_downloaded}")
                if failed_users:
                    print(f"⚠️  Failed users: {len(failed_users)}/{len(users)}")
                print("=" * 60)

                if max_iterations and iteration >= max_iterations:
                    print(f"\n🏁 Reached limit of {max_iterations} iterations")
                    break

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
        logger.info("║                  Monitor Statistics                       ║")
        logger.info("╚═══════════════════════════════════════════════════════════╝")
        logger.info(f"\n📊 Total videos downloaded: {total_videos}")
        logger.info(f"👥 Monitored users: {total_users}")

        if top_authors:
            logger.info(f"\n🏆 Top Authors:")
            for i, (author, count) in enumerate(top_authors, 1):
                logger.info(f"   {i}. @{author}: {count} videos")


def interactive_menu(monitor):
    """Interactive menu with user management, notifications and daemon control"""
    while True:
        # Check daemon status
        daemon_status = daemon.get_status()
        daemon_indicator = "🟢 Running" if daemon_status['running'] else "🔴 Stopped"

        print("\n ╔════════════════════════════════════════════════════════╗")
        print(" ║           TikTok Monitor - Main Menu                   ║")
        print(f" ║         Background: {daemon_indicator:<35}║")
        print(" ║                                                        ║")
        print(" ╚════════════════════════════════════════════════════════╝")
        print("\n👥 USER MANAGEMENT")
        print("  1.  ➕ Add user to monitor")
        print("  2. 📋  List monitored users")
        print("  3.  ❌ Remove user from monitoring")
        print("  4. 🗑️  Delete user permanently")
        print("  5. ♻️  Re-enable disabled user")
        print("\n🔍 MONITORING")
        print("  6. 🔎  Check for new videos (once)")
        print("  7. 🤖  Start automatic monitoring (foreground)")
        print("\n🔧 BACKGROUND CONTROL")
        print("  8.  🚀  Start background")
        print("  9.  ⏹️  Stop background")
        print("  10. 📊  Background status")
        print("\n📊 STATISTICS & SETTINGS")
        print("  11. 📊  Show statistics")
        print(f"  12. 🔔  Toggle notifications (currently: {notifier.get_status_text()})")
        print("\n  0. 🚪  Exit")
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
            interval = int(interval) if interval.isdigit() else get_config('monitor.interval_minutes', 30)
            monitor.start_monitoring(interval_minutes=interval)

        elif choice == '8':
            # Start daemon
            if daemon.is_running():
                print("\n⚠️  Daemon is already running!")
                print("   Stop it first with option 9")
            else:
                interval = input("\nMinutes between checks [30]: ").strip()
                interval = int(interval) if interval.isdigit() else get_config('monitor.interval_minutes', 30)

                print("\n🚀 Starting daemon...")
                print("   The monitoring will continue in background")
                print("   You can close this terminal safely")

                # Use subprocess to start daemon
                cmd = [sys.executable, 'tiktok_monitor.py', '--daemon', '--interval', str(interval)]

                try:
                    subprocess.Popen(cmd,
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL,
                                     stdin=subprocess.DEVNULL)
                    time.sleep(2)  # Give it time to start

                    if daemon.is_running():
                        status = daemon.get_status()
                        print(f"\n✅ Daemon started successfully!")
                        print(f"   PID: {status['pid']}")
                    else:
                        print("\n❌ Failed to start daemon")
                except Exception as e:
                    print(f"\n❌ Error starting daemon: {e}")

        elif choice == '9':
            # Stop daemon
            daemon.stop_daemon()

        elif choice == '10':
            # Daemon status
            status = daemon.get_status()
            print("\n" + "=" * 60)
            print("DAEMON STATUS")
            print("=" * 60)
            print(status['message'])

            if status['running']:
                print(f"\n📋 Process Information:")
                print(f"   PID: {status['pid']}")
                print(f"   Started: {status['started']}")
                print(f"   CPU Usage: {status['cpu']:.1f}%")
                print(f"   Memory: {status['memory']:.1f} MB")
            print("=" * 60)

        elif choice == '11':
            monitor.get_stats()

        elif choice == '12':
            monitor.toggle_notifications()

        elif choice == '0':
            logger.info("👋 Goodbye!")
            break

        else:
            print("\n❌ Invalid choice!")


def main():
    """Main function with interactive menu and daemon support"""
    parser = argparse.ArgumentParser(
        description='TikTok Monitor v2.5 - Auto-stop on persistent errors',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (uses config.yaml if available)
  %(prog)s

  # Start automatic monitoring
  %(prog)s --auto --users charlidamelio khaby.lame

  # Start as daemon (background)
  %(prog)s --daemon --interval 45

  # Stop daemon
  %(prog)s --stop-daemon

  # Daemon status
  %(prog)s --daemon-status

  # Check once only
  %(prog)s --check-once --users charlidamelio

  # Show statistics
  %(prog)s --stats

New in v2.5:
  - Auto-stop when all users fail with non-retryable errors
  - No more wasted retries on cookies/geo-block errors
  - Desktop notifications on critical failures
  - Better error tracking and reporting
        """
    )

    parser.add_argument('--auto', action='store_true',
                        help='Start continuous automatic monitoring')
    parser.add_argument('--daemon', action='store_true',
                        help='Start as background daemon')
    parser.add_argument('--stop-daemon', action='store_true',
                        help='Stop running daemon')
    parser.add_argument('--daemon-status', action='store_true',
                        help='Show daemon status')
    parser.add_argument('--interval', type=int, default=None,
                        help='Minutes between checks (overrides config)')
    parser.add_argument('--users', nargs='+',
                        help='Users to monitor (without @)')
    parser.add_argument('--check-once', action='store_true',
                        help='Check once and exit')
    parser.add_argument('--stats', action='store_true',
                        help='Show statistics and exit')
    parser.add_argument('-o', '--output', default=None,
                        help='Output folder (overrides config)')

    args = parser.parse_args()

    # Handle daemon commands FIRST (before creating monitor)
    if args.stop_daemon:
        daemon.stop_daemon()
        return

    if args.daemon_status:
        status = daemon.get_status()
        print("\n" + "=" * 60)
        print("DAEMON STATUS")
        print("=" * 60)
        print(status['message'])

        if status['running']:
            print(f"\n📋 Process Information:")
            print(f"   PID: {status['pid']}")
            print(f"   Started: {status['started']}")
            print(f"   CPU Usage: {status['cpu']:.1f}%")
            print(f"   Memory: {status['memory']:.1f} MB")
        print("=" * 60)
        return

    output_dir = args.output if args.output is not None else get_config('monitor.output_dir', './tiktok_downloads')
    monitor = TikTokMonitor(output_dir=output_dir)

    if args.stats:
        monitor.get_stats()
        return

    if args.users:
        for username in args.users:
            monitor.add_user_to_monitor(username.lstrip('@'))

    # Handle daemon start
    if args.daemon:
        if daemon.is_running():
            print("\n⚠️  Daemon is already running!")
            print("   Stop it first with: python tiktok_monitor.py --stop-daemon")
            return

        # Build arguments for daemon subprocess
        daemon_args = ['--auto']
        if args.interval:
            daemon_args.extend(['--interval', str(args.interval)])
        if args.output:
            daemon_args.extend(['--output', args.output])

        # Start daemon
        result = daemon.start_daemon(daemon_args)

        # On Unix, if we're the child process, we continue with monitoring
        if result is None and os.name != 'nt':
            # We ARE the daemon child process
            monitor.start_monitoring(interval_minutes=args.interval)

        return

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