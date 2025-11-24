#!/usr/bin/env python3
"""
Logger Manager for TikTok Auto Downloader
Provides structured logging with file and console output
"""

import logging
import os
from datetime import datetime
from pathlib import Path


class LoggerManager:
    """
    Centralized logger configuration for the entire application
    """
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, log_dir="logs", log_level=logging.INFO):
        if self._logger is not None:
            return
            
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        self._logger = logging.getLogger("TikTokMonitor")
        self._logger.setLevel(log_level)
        
        # Prevent duplicate handlers
        if self._logger.handlers:
            return
        
        # File handler - daily rotation
        log_filename = f"tiktok_monitor_{datetime.now().strftime('%Y-%m-%d')}.log"
        log_filepath = self.log_dir / log_filename
        
        file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)
        
        self._logger.info("=" * 60)
        self._logger.info("TikTok Monitor Started")
        self._logger.info(f"Log file: {log_filepath}")
        self._logger.info("=" * 60)
    
    @property
    def logger(self):
        return self._logger
    
    def debug(self, message):
        """Log debug message"""
        self._logger.debug(message)
    
    def info(self, message):
        """Log info message"""
        self._logger.info(message)
    
    def warning(self, message):
        """Log warning message"""
        self._logger.warning(message)
    
    def error(self, message, exc_info=False):
        """Log error message"""
        self._logger.error(message, exc_info=exc_info)
    
    def critical(self, message, exc_info=False):
        """Log critical message"""
        self._logger.critical(message, exc_info=exc_info)
    
    def success(self, message):
        """Log success message (as INFO level)"""
        self._logger.info(f"✅ {message}")
    
    def download_start(self, url, user):
        """Log download start"""
        self._logger.info(f"📥 Starting download: @{user}")
        self._logger.debug(f"URL: {url}")
    
    def download_complete(self, filepath, user):
        """Log download completion"""
        self._logger.info(f"✅ Download complete: @{user}")
        self._logger.debug(f"File: {filepath}")
    
    def download_failed(self, url, user, error):
        """Log download failure"""
        self._logger.error(f"❌ Download failed: @{user}")
        self._logger.error(f"Error: {error}")
        self._logger.debug(f"URL: {url}")
    
    def retry_attempt(self, attempt, max_attempts, wait_time):
        """Log retry attempt"""
        self._logger.warning(
            f"🔄 Retry attempt {attempt}/{max_attempts} in {wait_time}s..."
        )
    
    def monitoring_start(self, users, interval):
        """Log monitoring start"""
        self._logger.info("=" * 60)
        self._logger.info("🚀 Starting automatic monitoring")
        self._logger.info(f"👥 Users: {', '.join('@' + u for u in users)}")
        self._logger.info(f"⏱️  Interval: {interval} minutes")
        self._logger.info("=" * 60)
    
    def monitoring_check(self, iteration, user):
        """Log monitoring check"""
        self._logger.info(f"🔍 Check #{iteration}: @{user}")
    
    def new_videos_found(self, count, user):
        """Log new videos found"""
        if count > 0:
            self._logger.info(f"🆕 Found {count} new video(s) for @{user}")
        else:
            self._logger.debug(f"No new videos for @{user}")
    
    def user_added(self, username):
        """Log user added to monitoring"""
        self._logger.info(f"➕ User added to monitoring: @{username}")
    
    def user_removed(self, username):
        """Log user removed from monitoring"""
        self._logger.info(f"❌ User removed from monitoring: @{username}")
    
    def geo_restriction_detected(self):
        """Log geo-restriction detection"""
        self._logger.warning("🌍 Geo-restriction detected")
        self._logger.info("💡 Consider using VPN or cookies")
    
    def rate_limit_detected(self, wait_time):
        """Log rate limiting"""
        self._logger.warning(f"⏳ Rate limit detected. Waiting {wait_time}s...")
    
    def cleanup_old_logs(self, days=7):
        """Remove log files older than specified days"""
        try:
            current_time = datetime.now()
            for log_file in self.log_dir.glob("*.log"):
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if (current_time - file_time).days > days:
                    log_file.unlink()
                    self._logger.debug(f"Deleted old log: {log_file.name}")
        except Exception as e:
            self._logger.error(f"Error cleaning up logs: {e}")


# Global logger instance
logger = LoggerManager()


# Convenience functions for direct import
def debug(message):
    logger.debug(message)


def info(message):
    logger.info(message)


def warning(message):
    logger.warning(message)


def error(message, exc_info=False):
    logger.error(message, exc_info=exc_info)


def critical(message, exc_info=False):
    logger.critical(message, exc_info=exc_info)


def success(message):
    logger.success(message)
