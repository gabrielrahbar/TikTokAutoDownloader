#!/usr/bin/env python3
"""
Notification Manager for TikTok Auto Downloader
Sends desktop notifications when videos are downloaded
Supports Windows, macOS, and Linux
"""

from logger_manager import logger

# Try to import plyer, fallback gracefully if not available
try:
    from plyer import notification
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    logger.warning("plyer not installed. Desktop notifications disabled.")
    logger.info("Install with: pip install plyer")


class NotificationManager:
    """
    Manages desktop notifications for video downloads
    
    Features:
    - Cross-platform support (Windows, macOS, Linux)
    - Disabled by default (user must enable)
    - Graceful fallback if plyer not installed
    - Status persisted in database
    """
    
    def __init__(self):
        """Initialize notification manager with notifications disabled by default"""
        self.enabled = False  # Default: disabled
        
        if not NOTIFICATIONS_AVAILABLE:
            logger.debug("Notifications not available (plyer not installed)")
    
    def is_available(self):
        """
        Check if notifications are available on this system
        
        Returns:
            bool: True if plyer is installed and notifications can be sent
        """
        return NOTIFICATIONS_AVAILABLE
    
    def enable(self):
        """
        Enable desktop notifications
        
        Returns:
            bool: True if successfully enabled, False if plyer not available
        """
        if not NOTIFICATIONS_AVAILABLE:
            logger.error("Cannot enable notifications: plyer not installed")
            logger.info("Install with: pip install plyer")
            return False
        
        self.enabled = True
        logger.info("Desktop notifications enabled")
        return True
    
    def disable(self):
        """Disable desktop notifications"""
        self.enabled = False
        logger.info("Desktop notifications disabled")
    
    def toggle(self):
        """
        Toggle notifications on/off
        
        Returns:
            bool: New state (True = enabled, False = disabled)
        """
        if self.enabled:
            self.disable()
        else:
            self.enable()
        return self.enabled
    
    def send(self, title, message, timeout=5):
        """
        Send a desktop notification
        
        Args:
            title (str): Notification title
            message (str): Notification message
            timeout (int): How long to show notification in seconds
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug(f"Notification not sent (disabled): {title}")
            return False
        
        if not NOTIFICATIONS_AVAILABLE:
            logger.debug(f"Notification not sent (plyer unavailable): {title}")
            return False
        
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="TikTok Monitor",
                timeout=timeout
            )
            logger.debug(f"Notification sent: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    def notify_video_downloaded(self, username, title, views=None, likes=None):
        """
        Send notification when a video is downloaded
        
        Args:
            username (str): TikTok username
            title (str): Video title
            views (int, optional): View count
            likes (int, optional): Like count
        """
        # Truncate title if too long for notification
        short_title = title[:50] + "..." if len(title) > 50 else title
        
        # Build message with optional stats
        message_parts = [f"@{username} - {short_title}"]
        
        if views is not None:
            # Format views nicely (1.2M, 450K, etc.)
            if views >= 1_000_000:
                views_str = f"{views / 1_000_000:.1f}M"
            elif views >= 1_000:
                views_str = f"{views / 1_000:.0f}K"
            else:
                views_str = str(views)
            message_parts.append(f"👁️ {views_str} views")
        
        if likes is not None:
            # Format likes nicely
            if likes >= 1_000_000:
                likes_str = f"{likes / 1_000_000:.1f}M"
            elif likes >= 1_000:
                likes_str = f"{likes / 1_000:.0f}K"
            else:
                likes_str = str(likes)
            message_parts.append(f"❤️ {likes_str} likes")
        
        message = "\n".join(message_parts)
        
        self.send(
            title="🎬 New Video Downloaded!",
            message=message,
            timeout=8  # Show for 8 seconds
        )
    
    def notify_error(self, error_message):
        """
        Send error notification (use sparingly)
        
        Args:
            error_message (str): Error description
        """
        self.send(
            title="⚠️ TikTok Monitor Error",
            message=error_message,
            timeout=10
        )
    
    def get_status_text(self):
        """
        Get human-readable status text for display
        
        Returns:
            str: Status text (e.g., "Enabled ✅", "Disabled ❌", "Not available")
        """
        if not NOTIFICATIONS_AVAILABLE:
            return "Not available (plyer not installed)"
        elif self.enabled:
            return "Enabled ✅"
        else:
            return "Disabled ❌"


# Global instance - single notification manager for entire application
notifier = NotificationManager()


# Convenience functions for easy import and use
def enable_notifications():
    """
    Enable notifications globally
    
    Returns:
        bool: True if successfully enabled
    """
    return notifier.enable()


def disable_notifications():
    """Disable notifications globally"""
    notifier.disable()


def toggle_notifications():
    """
    Toggle notifications globally
    
    Returns:
        bool: New state (True = enabled)
    """
    return notifier.toggle()


def is_enabled():
    """
    Check if notifications are currently enabled
    
    Returns:
        bool: True if enabled
    """
    return notifier.enabled


def notify_video(username, title, views=None, likes=None):
    """
    Send video downloaded notification (convenience function)
    
    Args:
        username (str): TikTok username
        title (str): Video title
        views (int, optional): View count
        likes (int, optional): Like count
    """
    notifier.notify_video_downloaded(username, title, views, likes)


def get_status():
    """
    Get notification status text (convenience function)
    
    Returns:
        str: Status text for display
    """
    return notifier.get_status_text()
