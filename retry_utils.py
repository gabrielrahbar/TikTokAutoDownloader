#!/usr/bin/env python3
"""
Retry utilities for handling network errors and TikTok API issues
"""

import time
import random
from functools import wraps
from logger_manager import logger


class RetryConfig:
    """Configuration for retry behavior"""
    
    # Network retry settings
    MAX_NETWORK_RETRIES = 3
    NETWORK_RETRY_DELAY = (10, 30)  # (min, max) seconds
    
    # TikTok API retry settings
    MAX_API_RETRIES = 5
    API_RETRY_DELAY = (5, 15)  # (min, max) seconds
    
    # Download retry settings
    MAX_DOWNLOAD_RETRIES = 3
    DOWNLOAD_RETRY_DELAY = (15, 45)  # (min, max) seconds
    
    # Rate limit handling
    RATE_LIMIT_WAIT = 300  # 5 minutes
    
    # Exponential backoff
    USE_EXPONENTIAL_BACKOFF = True
    BACKOFF_MULTIPLIER = 2


def get_retry_delay(min_delay, max_delay, attempt=1, exponential=False):
    """
    Calculate retry delay with optional exponential backoff
    
    Args:
        min_delay: Minimum delay in seconds
        max_delay: Maximum delay in seconds
        attempt: Current retry attempt number
        exponential: Whether to use exponential backoff
    
    Returns:
        int: Delay in seconds
    """
    if exponential and RetryConfig.USE_EXPONENTIAL_BACKOFF:
        # Exponential backoff: delay increases with each attempt
        base_delay = random.uniform(min_delay, max_delay)
        multiplier = RetryConfig.BACKOFF_MULTIPLIER ** (attempt - 1)
        delay = min(base_delay * multiplier, max_delay * 3)  # Cap at 3x max
    else:
        # Random delay within range
        delay = random.uniform(min_delay, max_delay)
    
    return int(delay)


def retry_on_network_error(max_retries=None, delay_range=None):
    """
    Decorator for retrying functions on network errors
    
    Usage:
        @retry_on_network_error(max_retries=3)
        def download_something():
            ...
    """
    if max_retries is None:
        max_retries = RetryConfig.MAX_NETWORK_RETRIES
    if delay_range is None:
        delay_range = RetryConfig.NETWORK_RETRY_DELAY
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except (ConnectionError, TimeoutError, OSError) as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        wait_time = get_retry_delay(
                            delay_range[0], 
                            delay_range[1], 
                            attempt,
                            exponential=True
                        )
                        
                        logger.warning(
                            f"Network error in {func.__name__}: {str(e)}"
                        )
                        logger.retry_attempt(attempt, max_retries, wait_time)
                        
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            f"Max retries ({max_retries}) reached for {func.__name__}"
                        )
                        raise last_exception
                        
            return None
            
        return wrapper
    return decorator


def retry_on_api_error(max_retries=None, delay_range=None, rate_limit_wait=None):
    """
    Decorator for retrying functions on TikTok API errors
    Handles rate limiting specially
    """
    if max_retries is None:
        max_retries = RetryConfig.MAX_API_RETRIES
    if delay_range is None:
        delay_range = RetryConfig.API_RETRY_DELAY
    if rate_limit_wait is None:
        rate_limit_wait = RetryConfig.RATE_LIMIT_WAIT
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    error_msg = str(e).lower()
                    
                    # Check for rate limiting
                    if 'rate limit' in error_msg or '429' in error_msg or 'too many' in error_msg:
                        logger.rate_limit_detected(rate_limit_wait)
                        time.sleep(rate_limit_wait)
                        continue
                    
                    # Check for temporary errors
                    temporary_errors = [
                        'timeout', 'timed out', 'connection', 'temporary',
                        'unavailable', 'try again', '503', '502', '504'
                    ]
                    
                    is_temporary = any(err in error_msg for err in temporary_errors)
                    
                    if is_temporary and attempt < max_retries:
                        wait_time = get_retry_delay(
                            delay_range[0],
                            delay_range[1],
                            attempt,
                            exponential=True
                        )
                        
                        logger.warning(
                            f"API error in {func.__name__}: {str(e)}"
                        )
                        logger.retry_attempt(attempt, max_retries, wait_time)
                        
                        time.sleep(wait_time)
                    else:
                        # Non-retryable error or max retries reached
                        if attempt >= max_retries:
                            logger.error(
                                f"Max retries ({max_retries}) reached for {func.__name__}"
                            )
                        raise last_exception
                        
            return None
            
        return wrapper
    return decorator


def safe_execute(func, *args, default=None, log_error=True, **kwargs):
    """
    Safely execute a function and return default on error
    
    Args:
        func: Function to execute
        *args: Function arguments
        default: Default value to return on error
        log_error: Whether to log errors
        **kwargs: Function keyword arguments
    
    Returns:
        Function result or default value
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_error:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
        return default


class RetryContext:
    """
    Context manager for retry logic
    
    Usage:
        with RetryContext(max_retries=3) as retry:
            while retry.should_retry():
                try:
                    # Your code here
                    result = do_something()
                    retry.success()  # Mark as successful
                    break
                except Exception as e:
                    retry.failed(e)
    """
    
    def __init__(self, max_retries=3, delay_range=(5, 15), exponential=True):
        self.max_retries = max_retries
        self.delay_range = delay_range
        self.exponential = exponential
        self.attempt = 0
        self.last_error = None
        self._success = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and not self._success:
            logger.error(f"Retry context failed after {self.attempt} attempts")
        return False
    
    def should_retry(self):
        """Check if should attempt/retry"""
        self.attempt += 1
        return self.attempt <= self.max_retries
    
    def failed(self, error):
        """Mark attempt as failed"""
        self.last_error = error
        
        if self.attempt < self.max_retries:
            wait_time = get_retry_delay(
                self.delay_range[0],
                self.delay_range[1],
                self.attempt,
                exponential=self.exponential
            )
            
            logger.warning(f"Attempt {self.attempt} failed: {str(error)}")
            logger.retry_attempt(self.attempt, self.max_retries, wait_time)
            
            time.sleep(wait_time)
        else:
            logger.error(f"All {self.max_retries} attempts failed")
            if self.last_error:
                raise self.last_error
    
    def success(self):
        """Mark as successful"""
        self._success = True


def wait_with_jitter(base_seconds, jitter_percent=0.1):
    """
    Wait for specified seconds with random jitter
    
    Args:
        base_seconds: Base wait time in seconds
        jitter_percent: Percentage of jitter to add (0.1 = ±10%)
    """
    jitter = base_seconds * jitter_percent
    wait_time = base_seconds + random.uniform(-jitter, jitter)
    time.sleep(max(0, wait_time))
