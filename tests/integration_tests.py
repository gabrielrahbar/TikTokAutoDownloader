"""
Integration tests for TikTokAutoDownloader
These tests verify that the tool can still download from TikTok
and that yt-dlp is working correctly with TikTok's API
"""

import unittest
import os
import tempfile
import shutil
import subprocess
import json
from datetime import datetime


class TestTikTokIntegration(unittest.TestCase):
    """
    Integration tests that make real calls to TikTok
    These tests verify the tool still works with current TikTok API
    """

    @classmethod
    def setUpClass(cls):
        """Setup before all tests"""
        cls.temp_dir = tempfile.mkdtemp()
        
        # Public test video URL that should remain available
        # Using a verified account's popular video
        cls.test_video_url = "https://www.tiktok.com/@tiktok/video/6620802621319957765"
        
        print(f"\n{'='*60}")
        print("🧪 Starting TikTok Integration Tests")
        print(f"Test directory: {cls.temp_dir}")
        print(f"Test video: {cls.test_video_url}")
        print(f"{'='*60}\n")

    @classmethod
    def tearDownClass(cls):
        """Cleanup after all tests"""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
        print(f"\n{'='*60}")
        print("✅ Integration Tests Completed")
        print(f"{'='*60}\n")

    def test_01_yt_dlp_installed(self):
        """Verify yt-dlp is installed and accessible"""
        try:
            result = subprocess.run(
                ['yt-dlp', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            self.assertEqual(result.returncode, 0)
            version = result.stdout.strip()
            print(f"✓ yt-dlp version: {version}")
        except FileNotFoundError:
            self.fail("yt-dlp is not installed or not in PATH")
        except subprocess.TimeoutExpired:
            self.fail("yt-dlp command timed out")

    def test_02_tiktok_video_info(self):
        """Test that yt-dlp can extract TikTok video information"""
        try:
            result = subprocess.run(
                [
                    'yt-dlp',
                    '--dump-json',
                    '--no-download',
                    '--quiet',
                    self.test_video_url
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            self.assertEqual(result.returncode, 0, 
                           f"yt-dlp failed to extract info. Error: {result.stderr}")
            
            # Parse JSON response
            video_info = json.loads(result.stdout)
            
            # Verify essential fields are present
            self.assertIn('id', video_info)
            self.assertIn('title', video_info)
            self.assertIn('uploader', video_info)
            
            print(f"✓ Successfully extracted video info")
            print(f"  - Video ID: {video_info.get('id')}")
            print(f"  - Title: {video_info.get('title', '')[:50]}...")
            print(f"  - Uploader: {video_info.get('uploader')}")
            
        except subprocess.TimeoutExpired:
            self.fail("Video info extraction timed out - TikTok may be blocking requests")
        except json.JSONDecodeError:
            self.fail(f"Failed to parse yt-dlp JSON output: {result.stdout}")
        except Exception as e:
            self.fail(f"Unexpected error during video info extraction: {str(e)}")

    def test_03_tiktok_video_download(self):
        """Test actual video download from TikTok"""
        output_path = os.path.join(self.temp_dir, 'test_video.mp4')
        
        try:
            result = subprocess.run(
                [
                    'yt-dlp',
                    '-o', output_path,
                    '--quiet',
                    '--no-warnings',
                    self.test_video_url
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Check if download succeeded
            self.assertEqual(result.returncode, 0, 
                           f"Video download failed. Error: {result.stderr}")
            
            # Verify file was created
            self.assertTrue(os.path.exists(output_path), 
                          "Video file was not created")
            
            # Verify file has content
            file_size = os.path.getsize(output_path)
            self.assertGreater(file_size, 1000, 
                             f"Downloaded file is too small ({file_size} bytes)")
            
            print(f"✓ Successfully downloaded video")
            print(f"  - File size: {file_size / 1024:.2f} KB")
            print(f"  - Location: {output_path}")
            
        except subprocess.TimeoutExpired:
            self.fail("Video download timed out - TikTok may be rate limiting")
        except Exception as e:
            self.fail(f"Unexpected error during video download: {str(e)}")

    def test_04_tiktok_api_accessibility(self):
        """Test if TikTok API is accessible (no geo-blocking)"""
        try:
            # Quick check to see if we can reach TikTok
            result = subprocess.run(
                [
                    'yt-dlp',
                    '--dump-json',
                    '--no-download',
                    '--quiet',
                    '--socket-timeout', '15',
                    self.test_video_url
                ],
                capture_output=True,
                text=True,
                timeout=20
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.lower()
                
                # Check for common errors
                if 'not available' in error_msg or 'geo' in error_msg:
                    self.fail("⚠️ TikTok video not available (possible geo-restriction)")
                elif 'private' in error_msg:
                    self.fail("⚠️ Test video has been made private")
                elif 'removed' in error_msg or 'deleted' in error_msg:
                    self.fail("⚠️ Test video has been removed - update test URL")
                elif 'unable to extract' in error_msg:
                    self.fail("⚠️ yt-dlp cannot extract TikTok data - API may have changed")
                else:
                    self.fail(f"⚠️ Unknown error: {result.stderr}")
            
            print("✓ TikTok API is accessible")
            
        except subprocess.TimeoutExpired:
            self.fail("⚠️ Connection to TikTok timed out - network issues or rate limiting")
        except Exception as e:
            self.fail(f"⚠️ Unexpected error checking TikTok accessibility: {str(e)}")

    def test_05_rate_limiting_check(self):
        """Test if we're being rate limited by TikTok"""
        print("\n⏱️  Testing for rate limiting...")
        
        # Try to extract info twice in quick succession
        for i in range(2):
            try:
                result = subprocess.run(
                    [
                        'yt-dlp',
                        '--dump-json',
                        '--no-download',
                        '--quiet',
                        self.test_video_url
                    ],
                    capture_output=True,
                    text=True,
                    timeout=20
                )
                
                if result.returncode != 0:
                    error_msg = result.stderr.lower()
                    if 'too many requests' in error_msg or '429' in error_msg:
                        self.fail("⚠️ TikTok is rate limiting requests")
                    
                print(f"  Request {i+1}/2: OK")
                
            except subprocess.TimeoutExpired:
                self.fail("⚠️ Request timed out - possible rate limiting")
        
        print("✓ No rate limiting detected")


class TestYtDlpVersion(unittest.TestCase):
    """Test yt-dlp version and suggest updates if needed"""
    
    def test_yt_dlp_version_check(self):
        """Check if yt-dlp is reasonably up to date"""
        try:
            result = subprocess.run(
                ['yt-dlp', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            version = result.stdout.strip()
            print(f"\n📦 Current yt-dlp version: {version}")
            
            # Extract year and month from version (format: YYYY.MM.DD)
            try:
                year = int(version.split('.')[0])
                month = int(version.split('.')[1])
                
                current_year = datetime.now().year
                current_month = datetime.now().month
                
                # Warn if yt-dlp is older than 3 months
                version_age_months = (current_year - year) * 12 + (current_month - month)
                
                if version_age_months > 3:
                    print(f"⚠️  WARNING: yt-dlp is {version_age_months} months old")
                    print("   Consider updating: pip install --upgrade yt-dlp")
                elif version_age_months > 1:
                    print(f"ℹ️  yt-dlp is {version_age_months} month(s) old")
                else:
                    print("✓ yt-dlp is up to date")
                    
            except (ValueError, IndexError):
                print("ℹ️  Could not parse version date")
                
        except Exception as e:
            self.fail(f"Failed to check yt-dlp version: {str(e)}")


def run_integration_tests():
    """
    Helper function to run integration tests with detailed output
    Can be called from CI/CD or manually
    """
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes in order
    suite.addTests(loader.loadTestsFromTestCase(TestYtDlpVersion))
    suite.addTests(loader.loadTestsFromTestCase(TestTikTokIntegration))
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit_code = run_integration_tests()
    exit(exit_code)
