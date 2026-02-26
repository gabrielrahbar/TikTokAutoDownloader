package com.tiktokdownloader

import com.tiktokdownloader.data.remote.ErrorClassifier
import com.tiktokdownloader.data.remote.ErrorClassifier.ErrorType
import com.tiktokdownloader.data.remote.RetryHelper
import com.tiktokdownloader.data.remote.VideoData
import org.junit.Assert.*
import org.junit.Test
import java.io.IOException
import java.net.ConnectException
import java.net.SocketTimeoutException
import java.net.UnknownHostException

/**
 * Tests for ErrorClassifier - mirrors Python error_handler.py test coverage.
 */
class ErrorClassifierTest {

    // ── Network Errors ──────────────────────────────────────

    @Test
    fun classify_socketTimeout_isNetworkError() {
        val error = SocketTimeoutException("Connection timed out")
        val result = ErrorClassifier.classify(error)
        assertEquals(ErrorType.NETWORK, result.type)
        assertTrue(result.isRetryable)
        assertTrue(result.recommendedWaitMs > 0)
    }

    @Test
    fun classify_unknownHost_isNetworkError() {
        val error = UnknownHostException("Unable to resolve host")
        val result = ErrorClassifier.classify(error)
        assertEquals(ErrorType.NETWORK, result.type)
        assertTrue(result.isRetryable)
    }

    @Test
    fun classify_connectionRefused_isNetworkError() {
        val error = ConnectException("Connection refused")
        val result = ErrorClassifier.classify(error)
        assertEquals(ErrorType.NETWORK, result.type)
        assertTrue(result.isRetryable)
    }

    @Test
    fun classify_ioException_isNetworkError() {
        val error = IOException("Broken pipe")
        val result = ErrorClassifier.classify(error)
        assertEquals(ErrorType.NETWORK, result.type)
        assertTrue(result.isRetryable)
    }

    // ── Geo Restriction ─────────────────────────────────────

    @Test
    fun classify_geoRestricted_isGeoRestriction() {
        val error = Exception("This video is not available in your country")
        val result = ErrorClassifier.classify(error)
        assertEquals(ErrorType.GEO_RESTRICTION, result.type)
        assertFalse(result.isRetryable)
    }

    @Test
    fun classify_blocked_isGeoRestriction() {
        val error = Exception("Content blocked in this region")
        val result = ErrorClassifier.classify(error)
        assertEquals(ErrorType.GEO_RESTRICTION, result.type)
        assertFalse(result.isRetryable)
    }

    // ── Private Video ───────────────────────────────────────

    @Test
    fun classify_privateVideo_isPrivateVideo() {
        val error = Exception("This video is private")
        val result = ErrorClassifier.classify(error)
        assertEquals(ErrorType.PRIVATE_VIDEO, result.type)
        assertFalse(result.isRetryable)
    }

    @Test
    fun classify_loginRequired_isPrivateVideo() {
        val error = Exception("Login required to view this content")
        val result = ErrorClassifier.classify(error)
        assertEquals(ErrorType.PRIVATE_VIDEO, result.type)
        assertFalse(result.isRetryable)
    }

    // ── Deleted Video ───────────────────────────────────────

    @Test
    fun classify_deleted_isDeletedVideo() {
        val error = Exception("Video has been deleted")
        val result = ErrorClassifier.classify(error)
        assertEquals(ErrorType.DELETED_VIDEO, result.type)
        assertFalse(result.isRetryable)
    }

    @Test
    fun classify_notFound_isDeletedVideo() {
        val error = Exception("404 Not Found")
        val result = ErrorClassifier.classify(error)
        assertEquals(ErrorType.DELETED_VIDEO, result.type)
        assertFalse(result.isRetryable)
    }

    // ── Rate Limit ──────────────────────────────────────────

    @Test
    fun classify_rateLimit_isRateLimit() {
        val error = Exception("Rate limit exceeded, 429")
        val result = ErrorClassifier.classify(error)
        assertEquals(ErrorType.RATE_LIMIT, result.type)
        assertTrue(result.isRetryable)
        assertEquals(300_000L, result.recommendedWaitMs) // 5 minutes
    }

    @Test
    fun classify_tooManyRequests_isRateLimit() {
        val error = Exception("Too many requests")
        val result = ErrorClassifier.classify(error)
        assertEquals(ErrorType.RATE_LIMIT, result.type)
        assertTrue(result.isRetryable)
    }

    // ── Cookies Needed ──────────────────────────────────────

    @Test
    fun classify_captcha_isCookiesNeeded() {
        val error = Exception("Captcha verification required")
        val result = ErrorClassifier.classify(error)
        assertEquals(ErrorType.COOKIES_NEEDED, result.type)
        assertTrue(result.isRetryable)
    }

    // ── Unknown ─────────────────────────────────────────────

    @Test
    fun classify_unknownError_isUnknown() {
        val error = Exception("Something completely unexpected")
        val result = ErrorClassifier.classify(error)
        assertEquals(ErrorType.UNKNOWN, result.type)
        assertTrue(result.isRetryable)
    }

    // ── HTTP Code Classification ────────────────────────────

    @Test
    fun classifyHttpCode_429_isRateLimit() {
        val result = ErrorClassifier.classifyHttpCode(429)
        assertEquals(ErrorType.RATE_LIMIT, result.type)
        assertTrue(result.isRetryable)
    }

    @Test
    fun classifyHttpCode_403_isGeoRestriction() {
        val result = ErrorClassifier.classifyHttpCode(403)
        assertEquals(ErrorType.GEO_RESTRICTION, result.type)
        assertFalse(result.isRetryable)
    }

    @Test
    fun classifyHttpCode_404_isDeleted() {
        val result = ErrorClassifier.classifyHttpCode(404)
        assertEquals(ErrorType.DELETED_VIDEO, result.type)
        assertFalse(result.isRetryable)
    }

    @Test
    fun classifyHttpCode_500_isNetworkError() {
        val result = ErrorClassifier.classifyHttpCode(500)
        assertEquals(ErrorType.NETWORK, result.type)
        assertTrue(result.isRetryable)
    }

    @Test
    fun classifyHttpCode_503_isNetworkError() {
        val result = ErrorClassifier.classifyHttpCode(503)
        assertEquals(ErrorType.NETWORK, result.type)
        assertTrue(result.isRetryable)
    }
}

/**
 * Tests for RetryHelper configuration.
 */
class RetryHelperTest {

    @Test
    fun defaultNetworkConfig_hasCorrectValues() {
        val config = RetryHelper.DEFAULT_NETWORK
        assertEquals(3, config.maxRetries)
        assertEquals(5_000L, config.initialDelayMs)
        assertEquals(60_000L, config.maxDelayMs)
        assertEquals(2.0, config.backoffMultiplier, 0.01)
    }

    @Test
    fun defaultApiConfig_hasCorrectValues() {
        val config = RetryHelper.DEFAULT_API
        assertEquals(2, config.maxRetries)
        assertEquals(10_000L, config.initialDelayMs)
        assertEquals(120_000L, config.maxDelayMs)
        assertEquals(3.0, config.backoffMultiplier, 0.01)
    }

    @Test
    fun retryConfig_customValues() {
        val config = RetryHelper.RetryConfig(
            maxRetries = 5,
            initialDelayMs = 1_000L,
            maxDelayMs = 30_000L,
            backoffMultiplier = 1.5
        )
        assertEquals(5, config.maxRetries)
        assertEquals(1_000L, config.initialDelayMs)
        assertEquals(30_000L, config.maxDelayMs)
        assertEquals(1.5, config.backoffMultiplier, 0.01)
    }

    @Test
    fun retryConfig_exponentialBackoff_increases() {
        val config = RetryHelper.RetryConfig(
            initialDelayMs = 1_000L,
            backoffMultiplier = 2.0,
            maxDelayMs = 100_000L
        )
        // Verify backoff calculation: 1000 * 2.0 = 2000
        val secondDelay = (config.initialDelayMs * config.backoffMultiplier).toLong()
        assertEquals(2_000L, secondDelay)

        // Third delay: 2000 * 2.0 = 4000
        val thirdDelay = (secondDelay * config.backoffMultiplier).toLong()
        assertEquals(4_000L, thirdDelay)
    }

    @Test
    fun retryConfig_maxDelayRespected() {
        val config = RetryHelper.RetryConfig(
            initialDelayMs = 50_000L,
            backoffMultiplier = 3.0,
            maxDelayMs = 60_000L
        )
        val nextDelay = (config.initialDelayMs * config.backoffMultiplier).toLong()
            .coerceAtMost(config.maxDelayMs)
        assertEquals(60_000L, nextDelay) // Capped at maxDelay
    }
}

/**
 * Tests for VideoData model.
 */
class VideoDataTest {

    @Test
    fun videoData_defaultValues() {
        val data = VideoData()
        assertEquals("", data.id)
        assertEquals("", data.url)
        assertEquals("", data.title)
        assertEquals("", data.author)
        assertEquals(0L, data.likes)
        assertEquals(0L, data.views)
        assertEquals("", data.downloadUrl)
    }

    @Test
    fun videoData_withValues() {
        val data = VideoData(
            id = "v123",
            url = "https://tiktok.com/@user/video/123",
            title = "Test Video",
            author = "testuser",
            uploadTimestamp = 1704067200L,
            likes = 1000,
            views = 50000,
            downloadUrl = "https://cdn.tiktok.com/video.mp4"
        )
        assertEquals("v123", data.id)
        assertEquals("testuser", data.author)
        assertEquals(1704067200L, data.uploadTimestamp)
        assertEquals("https://cdn.tiktok.com/video.mp4", data.downloadUrl)
    }
}
