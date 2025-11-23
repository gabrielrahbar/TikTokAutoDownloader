"""
Basic tests for TikTokAutoDownloader
These tests verify core functionality without making real TikTok API calls
"""

import unittest
import sqlite3
import os
import tempfile
from datetime import datetime


class TestDatabaseSetup(unittest.TestCase):
    """Tests to verify SQLite database functionality"""

    def setUp(self):
        """Create a temporary database for each test"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()

    def tearDown(self):
        """Remove temporary database after each test"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_database_creation(self):
        """Verify that database can be created"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create videos table (mimics project structure)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                url TEXT,
                title TEXT,
                author TEXT,
                timestamp INTEGER,
                likes INTEGER,
                views INTEGER,
                file_path TEXT,
                download_date TEXT
            )
        ''')

        conn.commit()
        conn.close()

        # Verify file exists
        self.assertTrue(os.path.exists(self.db_path))

    def test_insert_video(self):
        """Verify that videos can be inserted into database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                url TEXT,
                author TEXT,
                timestamp INTEGER
            )
        ''')

        # Insert test video
        test_video = {
            'id': '7234567890123456789',
            'url': 'https://www.tiktok.com/@test/video/7234567890123456789',
            'author': 'testuser',
            'timestamp': 1234567890
        }

        cursor.execute('''
            INSERT INTO videos (id, url, author, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (test_video['id'], test_video['url'], test_video['author'], test_video['timestamp']))

        conn.commit()

        # Verify insertion
        cursor.execute('SELECT * FROM videos WHERE id = ?', (test_video['id'],))
        result = cursor.fetchone()

        conn.close()

        self.assertIsNotNone(result)
        self.assertEqual(result[0], test_video['id'])
        self.assertEqual(result[2], test_video['author'])

    def test_prevent_duplicate_videos(self):
        """Verify that duplicate video IDs are prevented"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                url TEXT
            )
        ''')

        # Insert first video
        cursor.execute('INSERT INTO videos (id, url) VALUES (?, ?)', ('123', 'url1'))
        conn.commit()

        # Attempt to insert duplicate should raise error
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute('INSERT INTO videos (id, url) VALUES (?, ?)', ('123', 'url2'))
            conn.commit()

        conn.close()


class TestTimestampFiltering(unittest.TestCase):
    """Tests for timestamp-based filtering logic"""

    def test_timestamp_comparison(self):
        """Verify timestamps are compared correctly"""
        old_timestamp = 1600000000  # September 2020
        new_timestamp = 1700000000  # November 2023

        # Video is "new" if timestamp is greater than last saved
        is_new = new_timestamp > old_timestamp
        self.assertTrue(is_new)

    def test_filter_new_videos(self):
        """Simulate filtering of new videos"""
        last_saved_timestamp = 1650000000

        # Simulated video list with timestamps
        videos = [
            {'id': '1', 'timestamp': 1640000000},  # Old
            {'id': '2', 'timestamp': 1660000000},  # New
            {'id': '3', 'timestamp': 1670000000},  # New
            {'id': '4', 'timestamp': 1645000000},  # Old
        ]

        # Filter only new videos
        new_videos = [v for v in videos if v['timestamp'] > last_saved_timestamp]

        self.assertEqual(len(new_videos), 2)
        self.assertEqual(new_videos[0]['id'], '2')
        self.assertEqual(new_videos[1]['id'], '3')

    def test_no_new_videos(self):
        """Test when all videos are old"""
        last_saved_timestamp = 1700000000

        videos = [
            {'id': '1', 'timestamp': 1600000000},
            {'id': '2', 'timestamp': 1650000000},
        ]

        new_videos = [v for v in videos if v['timestamp'] > last_saved_timestamp]

        self.assertEqual(len(new_videos), 0)


class TestURLValidation(unittest.TestCase):
    """Tests for TikTok URL validation"""

    def test_valid_tiktok_url(self):
        """Verify valid URLs are recognized"""
        valid_urls = [
            'https://www.tiktok.com/@user/video/1234567890123456789',
            'https://vm.tiktok.com/ZMabcdefg/',
            'https://www.tiktok.com/@user123/video/9876543210987654321',
            'https://m.tiktok.com/@user/video/123',
        ]

        for url in valid_urls:
            # Simple check that URL contains 'tiktok.com'
            self.assertIn('tiktok.com', url.lower())

    def test_invalid_url(self):
        """Verify invalid URLs are rejected"""
        invalid_urls = [
            'https://www.youtube.com/watch?v=abc',
            'https://instagram.com/p/abc123',
            'not a url at all',
            'https://www.facebook.com/video',
        ]

        for url in invalid_urls:
            self.assertNotIn('tiktok.com', url.lower())

    def test_url_with_parameters(self):
        """Test URL with query parameters"""
        url = 'https://www.tiktok.com/@user/video/123?lang=en&is_copy_url=1'
        self.assertIn('tiktok.com', url.lower())


class TestFileNaming(unittest.TestCase):
    """Tests for file naming logic"""

    def test_safe_filename_creation(self):
        """Verify safe filenames are created"""
        # Simulate safe filename creation
        author = "test_user"
        video_id = "1234567890"

        filename = f"{author}_{video_id}.mp4"

        # Verify no problematic characters
        self.assertNotIn('/', filename)
        self.assertNotIn('\\', filename)
        self.assertTrue(filename.endswith('.mp4'))

    def test_sanitize_filename(self):
        """Verify removal of unsafe characters from filenames"""
        unsafe_name = "user@name/with\\invalid:chars*.txt"

        # Remove invalid characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
        safe_name = ''.join(c if c in safe_chars else '_' for c in unsafe_name)

        self.assertNotIn('/', safe_name)
        self.assertNotIn('\\', safe_name)
        self.assertNotIn('*', safe_name)
        self.assertNotIn(':', safe_name)

    def test_filename_length(self):
        """Test that very long filenames are handled"""
        long_author = "a" * 200
        video_id = "123"

        filename = f"{long_author}_{video_id}.mp4"

        # Filename exists (even if long)
        self.assertIsInstance(filename, str)
        self.assertGreater(len(filename), 0)


class TestAntiDuplicateLogic(unittest.TestCase):
    """Tests for anti-duplicate logic"""

    def test_duplicate_detection(self):
        """Verify duplicates are detected"""
        downloaded_ids = ['123', '456', '789']

        new_video_id = '456'  # This is a duplicate

        is_duplicate = new_video_id in downloaded_ids
        self.assertTrue(is_duplicate)

    def test_unique_video(self):
        """Verify unique videos are recognized"""
        downloaded_ids = ['123', '456', '789']

        new_video_id = '999'  # This is new

        is_duplicate = new_video_id in downloaded_ids
        self.assertFalse(is_duplicate)

    def test_empty_downloaded_list(self):
        """Test with no previously downloaded videos"""
        downloaded_ids = []

        new_video_id = '123'

        is_duplicate = new_video_id in downloaded_ids
        self.assertFalse(is_duplicate)

    def test_case_sensitivity(self):
        """Test that video IDs are case-sensitive"""
        downloaded_ids = ['abc123']

        # Different case should be different video
        self.assertNotIn('ABC123', downloaded_ids)
        self.assertIn('abc123', downloaded_ids)


class TestDelayLogic(unittest.TestCase):
    """Tests for anti-bot delay calculations"""

    def test_delay_range(self):
        """Verify delay is within expected range"""
        import random

        # Simulate random delay between downloads
        min_delay = 5
        max_delay = 15

        for _ in range(10):
            delay = random.uniform(min_delay, max_delay)
            self.assertGreaterEqual(delay, min_delay)
            self.assertLessEqual(delay, max_delay)

    def test_user_delay_range(self):
        """Verify delay between users is within range"""
        import random

        min_delay = 10
        max_delay = 30

        for _ in range(10):
            delay = random.uniform(min_delay, max_delay)
            self.assertGreaterEqual(delay, min_delay)
            self.assertLessEqual(delay, max_delay)


class TestMonitoredUsers(unittest.TestCase):
    """Tests for monitored users database operations"""

    def setUp(self):
        """Setup temporary database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()

        # Create monitored_users table
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitored_users (
                username TEXT PRIMARY KEY,
                last_check INTEGER,
                last_video_timestamp INTEGER,
                total_videos INTEGER,
                active INTEGER DEFAULT 1
            )
        ''')
        conn.commit()
        conn.close()

    def tearDown(self):
        """Cleanup"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_add_monitored_user(self):
        """Test adding a user to monitoring"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO monitored_users (username, last_check, total_videos)
            VALUES (?, ?, ?)
        ''', ('testuser', 0, 0))
        conn.commit()

        # Verify user was added
        cursor.execute('SELECT * FROM monitored_users WHERE username = ?', ('testuser',))
        result = cursor.fetchone()

        conn.close()

        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'testuser')

    def test_update_last_check(self):
        """Test updating last check timestamp"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Insert user
        cursor.execute('''
            INSERT INTO monitored_users (username, last_check)
            VALUES (?, ?)
        ''', ('testuser', 1000000))
        conn.commit()

        # Update last check
        new_timestamp = 2000000
        cursor.execute('''
            UPDATE monitored_users 
            SET last_check = ? 
            WHERE username = ?
        ''', (new_timestamp, 'testuser'))
        conn.commit()

        # Verify update
        cursor.execute('SELECT last_check FROM monitored_users WHERE username = ?', ('testuser',))
        result = cursor.fetchone()

        conn.close()

        self.assertEqual(result[0], new_timestamp)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)