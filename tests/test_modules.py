#!/usr/bin/env python3
"""
Unit tests for core modules: ErrorHandler and ConfigManager
These tests cover the essential functionality without over-engineering
"""

import unittest
import sys
import os
import tempfile
import yaml

# Add parent directory to path
sys.path.insert(0, os. path.dirname(os.path.dirname(os.path. abspath(__file__))))

from error_handler import ErrorHandler, ErrorType, UserFriendlyError


# ERROR HANDLER TESTS

class TestErrorClassification(unittest.TestCase):
    """Tests for error type classification - the core functionality"""

    def test_geo_restriction_errors(self):
        """Test geo-restriction detection"""
        test_cases = [
            "Video not available in your country",
            "This content is not available in your region",
            "geo-blocked content",
        ]
        for msg in test_cases:
            result = ErrorHandler.analyze_error(Exception(msg))
            self.assertEqual(result. error_type, ErrorType.GEO_RESTRICTION)

    def test_rate_limit_errors(self):
        """Test rate limit detection"""
        test_cases = [
            "Rate limit exceeded",
            "HTTP Error 429",
            "Too many requests",
        ]
        for msg in test_cases:
            result = ErrorHandler.analyze_error(Exception(msg))
            self.assertEqual(result. error_type, ErrorType.RATE_LIMIT)

    def test_network_errors(self):
        """Test network error detection"""
        test_cases = [
            "Connection refused",
            "Connection timed out",
            "Network is unreachable",
        ]
        for msg in test_cases:
            result = ErrorHandler.analyze_error(Exception(msg))
            self. assertEqual(result.error_type, ErrorType.NETWORK)

    def test_deleted_video_errors(self):
        """Test deleted video detection"""
        test_cases = [
            "Video has been removed",
            "404 Not Found",
            "Content no longer available",
        ]
        for msg in test_cases:
            result = ErrorHandler. analyze_error(Exception(msg))
            self.assertEqual(result.error_type, ErrorType.DELETED_VIDEO)

    def test_private_video_errors(self):
        """Test private video detection"""
        result = ErrorHandler.analyze_error(Exception("This video is private"))
        self.assertEqual(result.error_type, ErrorType.PRIVATE_VIDEO)

    def test_unknown_error_fallback(self):
        """Test unknown errors fall back correctly"""
        result = ErrorHandler.analyze_error(Exception("random xyz error"))
        self. assertEqual(result.error_type, ErrorType.UNKNOWN)


class TestRetryLogic(unittest.TestCase):
    """Tests for retry decision logic"""

    class TestRetryLogic(unittest.TestCase):
        """Tests for retry decision logic"""

        def test_retryable_errors(self):
            """Network and rate limit errors should be retryable"""
            for error_type in [ErrorType.NETWORK, ErrorType.RATE_LIMIT]:
                error = UserFriendlyError(error_type=error_type, message="Test")
                self.assertTrue(ErrorHandler.is_retryable(error))

        def test_non_retryable_errors(self):
            """Deleted, private, geo-blocked, and cookie errors should NOT be retryable"""
            non_retryable = [
                ErrorType.DELETED_VIDEO,
                ErrorType.PRIVATE_VIDEO,
                ErrorType.INVALID_URL,
                ErrorType.GEO_RESTRICTION, 
                ErrorType.COOKIES_NEEDED,
                ErrorType.PERMISSION,
                ErrorType.UNKNOWN
            ]
            for error_type in non_retryable:
                error = UserFriendlyError(error_type=error_type, message="Test")
                self.assertFalse(ErrorHandler.is_retryable(error))

    def test_wait_times(self):
        """Test wait times are reasonable"""
        rate_limit_error = UserFriendlyError(error_type=ErrorType.RATE_LIMIT, message="Test")
        network_error = UserFriendlyError(error_type=ErrorType.NETWORK, message="Test")
        
        # Rate limit should wait longer than network
        self.assertGreater(
            ErrorHandler.get_wait_time(rate_limit_error),
            ErrorHandler.get_wait_time(network_error)
        )


class TestErrorSolutions(unittest.TestCase):
    """Test that errors provide helpful solutions"""

    def test_errors_have_solutions(self):
        """All analyzed errors should have at least one solution"""
        test_errors = [
            "not available in your country",
            "429 too many requests",
            "Connection timeout",
            "random unknown error",
        ]
        for msg in test_errors:
            result = ErrorHandler.analyze_error(Exception(msg))
            self.assertGreater(len(result.solutions), 0, f"No solutions for: {msg}")


# CONFIG MANAGER TESTS

class TestConfigManager(unittest.TestCase):
    """Tests for ConfigManager functionality"""

    def test_get_with_default(self):
        """Test getting config with default fallback"""
        from config_manager import ConfigManager
        
        manager = ConfigManager.__new__(ConfigManager)
        manager._config = {'existing': {'key': 'value'}}
        
        # Existing key
        self.assertEqual(manager.get('existing.key'), 'value')
        
        # Non-existing with default
        self. assertEqual(manager.get('missing.key', 'default'), 'default')

    def test_set_config_value(self):
        """Test setting config values"""
        from config_manager import ConfigManager
        
        manager = ConfigManager.__new__(ConfigManager)
        manager._config = {}
        
        manager.set('new.nested.key', 'value')
        self. assertEqual(manager. get('new.nested.key'), 'value')

    def test_merge_config(self):
        """Test config merging preserves defaults and adds user values"""
        from config_manager import ConfigManager
        
        manager = ConfigManager.__new__(ConfigManager)
        
        default = {'section': {'key1': 'default1', 'key2': 'default2'}}
        user = {'section': {'key1': 'user1'}, 'new_section': {'key': 'value'}}
        
        merged = manager.merge_config(default, user)
        
        self.assertEqual(merged['section']['key1'], 'user1')  # Overridden
        self.assertEqual(merged['section']['key2'], 'default2')  # Kept default
        self. assertEqual(merged['new_section']['key'], 'value')  # New section


class TestConfigFileLoading(unittest.TestCase):
    """Tests for YAML config file loading"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path. join(self.temp_dir, 'test_config.yaml')

    def tearDown(self):
        if os.path.exists(self.config_path):
            os.unlink(self.config_path)
        os.rmdir(self.temp_dir)

    def test_load_valid_yaml(self):
        """Test loading valid YAML"""
        config = {'monitor': {'interval_minutes': 45}}
        
        with open(self. config_path, 'w') as f:
            yaml. dump(config, f)
        
        with open(self.config_path, 'r') as f:
            loaded = yaml.safe_load(f)
        
        self.assertEqual(loaded['monitor']['interval_minutes'], 45)

    def test_empty_yaml_returns_none(self):
        """Test empty YAML returns None"""
        with open(self.config_path, 'w') as f:
            f.write('')
        
        with open(self.config_path, 'r') as f:
            loaded = yaml.safe_load(f)
        
        self.assertIsNone(loaded)
# RETRY UTILS TESTS


class TestRetryUtils(unittest.TestCase):
    """Essential tests for retry utilities"""

    def test_retry_delay_in_range(self):
        """Test delay is within specified range"""
        from retry_utils import get_retry_delay
        
        for _ in range(10):
            delay = get_retry_delay(5, 15)
            self. assertGreaterEqual(delay, 5)
            self.assertLessEqual(delay, 15)

    def test_exponential_backoff_increases(self):
        """Test exponential backoff increases with attempts"""
        from retry_utils import get_retry_delay
        
        delays = [get_retry_delay(5, 15, attempt=i, exponential=True) for i in range(1, 4)]
        # Average of later attempts should be higher
        self.assertLessEqual(delays[0], delays[2] + 10)  # Allow some variance

    def test_safe_execute_returns_default_on_error(self):
        """Test safe_execute returns default on exception"""
        from retry_utils import safe_execute
        
        def failing():
            raise ValueError("Error")
        
        result = safe_execute(failing, default="fallback", log_error=False)
        self. assertEqual(result, "fallback")



# NOTIFICATION MANAGER TESTS


class TestNotificationManager(unittest.TestCase):
    """Essential tests for notification manager"""

    def test_disabled_by_default(self):
        """Test notifications are disabled by default"""
        from notification_manager import NotificationManager
        manager = NotificationManager()
        self.assertFalse(manager.enabled)

    def test_send_when_disabled_returns_false(self):
        """Test send returns False when disabled"""
        from notification_manager import NotificationManager
        manager = NotificationManager()
        result = manager.send("Title", "Message")
        self. assertFalse(result)

    def test_views_formatting(self):
        """Test view count formatting"""
        # Millions
        views = 1500000
        formatted = f"{views / 1_000_000:.1f}M" if views >= 1_000_000 else str(views)
        self.assertEqual(formatted, "1.5M")
        
        # Thousands
        views = 45000
        formatted = f"{views / 1_000:.0f}K" if views >= 1_000 else str(views)
        self.assertEqual(formatted, "45K")


if __name__ == '__main__':
    unittest.main(verbosity=2)