#!/usr/bin/env python3
"""
Error Handler - User-Friendly Error Messages
Translates technical errors into clear messages with practical solutions
"""

from logger_manager import logger


class ErrorType:
    """Error categorization"""
    GEO_RESTRICTION = "geo_restriction"
    PRIVATE_VIDEO = "private_video"
    DELETED_VIDEO = "deleted_video"
    RATE_LIMIT = "rate_limit"
    NETWORK = "network"
    INVALID_URL = "invalid_url"
    PERMISSION = "permission"
    DISK_SPACE = "disk_space"
    COOKIES_NEEDED = "cookies_needed"
    UNKNOWN = "unknown"


class UserFriendlyError(Exception):
    """Error with user-friendly message"""
    def __init__(self, error_type, message, solutions=None, technical_details=None):
        self.error_type = error_type
        self.message = message
        self.solutions = solutions or []
        self.technical_details = technical_details
        super().__init__(message)


class ErrorHandler:
    """
    Centralized error handler with user-friendly messages
    """
    
    # Emoji for different error types
    ERROR_EMOJI = {
        ErrorType.GEO_RESTRICTION: "🌍",
        ErrorType.PRIVATE_VIDEO: "🔒",
        ErrorType.DELETED_VIDEO: "🗑️",
        ErrorType.RATE_LIMIT: "⏳",
        ErrorType.NETWORK: "📡",
        ErrorType.INVALID_URL: "🔗",
        ErrorType.PERMISSION: "⛔",
        ErrorType.DISK_SPACE: "💾",
        ErrorType.COOKIES_NEEDED: "🍪",
        ErrorType.UNKNOWN: "❌"
    }
    
    @staticmethod
    def analyze_error(exception):
        """
        Analyze an exception and return a user-friendly error
        
        Args:
            exception: The original exception
            
        Returns:
            UserFriendlyError: Error with clear message and solutions
        """
        error_msg = str(exception).lower()
        
        # Geo-restriction detection
        if any(keyword in error_msg for keyword in ['geo', 'not available in your', 'region', 'country']):
            return UserFriendlyError(
                ErrorType.GEO_RESTRICTION,
                "Video not available in your region",
                solutions=[
                    "Connect to a VPN (recommended: USA, Canada, or Germany)",
                    "Export cookies from TikTok website (run: python tiktok_downloader_advanced.py --help-cookies)",
                    "Try again later (sometimes temporary restriction)"
                ],
                technical_details=str(exception)
            )
        
        # Private video
        if any(keyword in error_msg for keyword in ['private', 'unavailable', 'this video is private']):
            return UserFriendlyError(
                ErrorType.PRIVATE_VIDEO,
                "This video is private or unavailable",
                solutions=[
                    "The video might be set to 'Friends only' or 'Private'",
                    "Check if you need to be logged in to view it",
                    "Export cookies from your TikTok account (run: python tiktok_downloader_advanced.py --help-cookies)"
                ],
                technical_details=str(exception)
            )
        
        # Deleted/removed video
        if any(keyword in error_msg for keyword in ['removed', 'deleted', 'no longer available', 'not found', '404']):
            return UserFriendlyError(
                ErrorType.DELETED_VIDEO,
                "Video has been deleted or removed",
                solutions=[
                    "The author may have deleted the video",
                    "The video might have been removed for violating TikTok guidelines",
                    "Check if the URL is correct"
                ],
                technical_details=str(exception)
            )
        
        # Rate limiting
        if any(keyword in error_msg for keyword in ['rate limit', '429', 'too many requests', 'slow down']):
            return UserFriendlyError(
                ErrorType.RATE_LIMIT,
                "Too many requests - TikTok is limiting downloads",
                solutions=[
                    "Wait 5-10 minutes before trying again",
                    "Use a VPN to change your IP address",
                    "Reduce check frequency in config.yaml (increase interval_minutes)",
                    "The monitor will automatically retry with longer delays"
                ],
                technical_details=str(exception)
            )
        
        # Network errors
        if any(keyword in error_msg for keyword in ['connection', 'timeout', 'timed out', 'network', 'unreachable', 'no internet']):
            return UserFriendlyError(
                ErrorType.NETWORK,
                "Network connection problem",
                solutions=[
                    "Check your internet connection",
                    "Try again in a few moments",
                    "Check if TikTok is accessible in your browser",
                    "The monitor will automatically retry"
                ],
                technical_details=str(exception)
            )
        
        # Invalid URL
        if any(keyword in error_msg for keyword in ['invalid url', 'malformed', 'unsupported url']):
            return UserFriendlyError(
                ErrorType.INVALID_URL,
                "Invalid TikTok URL",
                solutions=[
                    "Make sure the URL starts with: https://www.tiktok.com/@username/video/",
                    "Copy the URL directly from TikTok app or website",
                    "Example: https://www.tiktok.com/@charlidamelio/video/1234567890"
                ],
                technical_details=str(exception)
            )
        
        # Permission errors
        if any(keyword in error_msg for keyword in ['permission', 'access denied', 'forbidden', '403']):
            return UserFriendlyError(
                ErrorType.PERMISSION,
                "Access denied - permission required",
                solutions=[
                    "You might need to be logged in to view this content",
                    "Export cookies from TikTok (run: python tiktok_downloader_advanced.py --help-cookies)",
                    "Check if the video requires special permissions (age restriction, etc.)"
                ],
                technical_details=str(exception)
            )
        
        # Disk space
        if any(keyword in error_msg for keyword in ['disk', 'space', 'no space left', 'storage']):
            return UserFriendlyError(
                ErrorType.DISK_SPACE,
                "Not enough disk space",
                solutions=[
                    "Free up space on your hard drive",
                    "Change output directory to a drive with more space",
                    "Delete old downloaded videos you no longer need"
                ],
                technical_details=str(exception)
            )

        # Cookies needed (generic authentication issue)
        if any(keyword in error_msg for keyword in [
            'sign in', 'login', 'authentication', 'unauthorized',
            'requiring login', 'cookies', 'unable to extract',
            'user id', 'channel_id', '--cookies'
        ]):
            return UserFriendlyError(
                ErrorType.COOKIES_NEEDED,
                "Authentication required",
                solutions=[
                    "This video requires you to be logged in",
                    "Export cookies from your TikTok account",
                    "Run: python tiktok_downloader_advanced.py --help-cookies",
                    "Follow the instructions to export cookies from your browser"
                ],
                technical_details=str(exception)
            )
        
        # Unknown error
        return UserFriendlyError(
            ErrorType.UNKNOWN,
            "An unexpected error occurred",
            solutions=[
                "Try again in a few moments",
                "Check if the video URL is correct",
                "Make sure you have the latest version of yt-dlp: pip install --upgrade yt-dlp",
                "Report this error on GitHub if it persists: https://github.com/gabrielrahbar/TikTokAutoDownloader/issues"
            ],
            technical_details=str(exception)
        )
    
    @staticmethod
    def display_error(error, show_technical=False):
        """
        Display error in a user-friendly format
        
        Args:
            error: UserFriendlyError object
            show_technical: Whether to show technical details
        """
        emoji = ErrorHandler.ERROR_EMOJI.get(error.error_type, "❌")
        
        # Print header
        print("\n" + "="*70)
        print(f"{emoji} ERROR: {error.message}")
        print("="*70)
        
        # Print solutions
        if error.solutions:
            print("\n💡 SOLUTIONS:")
            for i, solution in enumerate(error.solutions, 1):
                print(f"   {i}. {solution}")
        
        # Print technical details (optional)
        if show_technical and error.technical_details:
            print("\n🔧 Technical details:")
            print(f"   {error.technical_details}")
        
        print("="*70 + "\n")
    
    @staticmethod
    def handle_download_error(exception, url, username=None, show_technical=False):
        """
        Handle download error with user-friendly message
        
        Args:
            exception: The exception that occurred
            url: The video URL
            username: TikTok username (optional)
            show_technical: Whether to show technical details
            
        Returns:
            UserFriendlyError: The analyzed error
        """
        user_error = ErrorHandler.analyze_error(exception)
        
        # Log to file with full details
        logger.error(f"Download failed for {'@' + username if username else url}")
        logger.error(f"Error type: {user_error.error_type}")
        logger.error(f"Technical details: {user_error.technical_details}")
        
        # Display to user
        ErrorHandler.display_error(user_error, show_technical=show_technical)
        
        return user_error

    @staticmethod
    def is_retryable(error):
        """
        Check if error is retryable

        Args:
            error: UserFriendlyError object

        Returns:
            bool: True if should retry, False otherwise
        """
        # Retryable errors (temporary issues only)
        retryable_types = [
            ErrorType.NETWORK,
            ErrorType.RATE_LIMIT
            # ← UNKNOWN REMOVED - don't retry unknown errors!
        ]

        # Non-retryable errors (require user action)
        non_retryable_types = [
            ErrorType.DELETED_VIDEO,
            ErrorType.PRIVATE_VIDEO,
            ErrorType.INVALID_URL,
            ErrorType.DISK_SPACE,
            ErrorType.GEO_RESTRICTION,
            ErrorType.COOKIES_NEEDED,
            ErrorType.PERMISSION,
            ErrorType.UNKNOWN
        ]

        if error.error_type in non_retryable_types:
            return False

        if error.error_type in retryable_types:
            return True

        # Default: don't retry
        return False


    
    @staticmethod
    def get_wait_time(error):
        """
        Get recommended wait time before retry based on error type
        
        Args:
            error: UserFriendlyError object
            
        Returns:
            int: Seconds to wait before retry
        """
        wait_times = {
            ErrorType.RATE_LIMIT: 300,  # 5 minutes
            ErrorType.NETWORK: 30,
            ErrorType.GEO_RESTRICTION: 60,
            ErrorType.UNKNOWN: 45
        }
        
        return wait_times.get(error.error_type, 30)


# Convenience functions
def handle_error(exception, url=None, username=None, show_technical=False):
    """
    Convenience function to handle errors
    
    Args:
        exception: The exception to handle
        url: Video URL (optional)
        username: TikTok username (optional)
        show_technical: Show technical details
        
    Returns:
        UserFriendlyError: Analyzed error
    """
    return ErrorHandler.handle_download_error(exception, url, username, show_technical)


def is_retryable_error(error):
    """Check if error should be retried"""
    return ErrorHandler.is_retryable(error)


def get_retry_wait_time(error):
    """Get wait time for retry"""
    return ErrorHandler.get_wait_time(error)
