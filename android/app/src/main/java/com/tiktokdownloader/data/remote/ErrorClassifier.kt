package com.tiktokdownloader.data.remote

/**
 * Error classification mirroring Python error_handler.py.
 * Categorizes download/network errors and provides actionable solutions.
 */
object ErrorClassifier {

    enum class ErrorType {
        NETWORK,
        GEO_RESTRICTION,
        PRIVATE_VIDEO,
        DELETED_VIDEO,
        RATE_LIMIT,
        COOKIES_NEEDED,
        AGE_RESTRICTED,
        UNKNOWN
    }

    data class ClassifiedError(
        val type: ErrorType,
        val message: String,
        val solution: String,
        val isRetryable: Boolean,
        val recommendedWaitMs: Long
    )

    /**
     * Analyzes an exception and classifies it into a known error type.
     * Mirrors Python's ErrorHandler.analyze_error().
     */
    fun classify(error: Throwable): ClassifiedError {
        val msg = (error.message ?: "").lowercase()

        return when {
            // Network errors - retryable
            msg.contains("timeout") || msg.contains("timed out") ||
            msg.contains("unable to resolve host") || msg.contains("no address associated") ||
            msg.contains("failed to connect") || msg.contains("connection reset") ||
            msg.contains("connection refused") || msg.contains("network is unreachable") ||
            msg.contains("broken pipe") || msg.contains("eof") ||
            error is java.net.SocketTimeoutException ||
            error is java.net.UnknownHostException ||
            error is java.net.ConnectException ||
            error is java.io.IOException -> {
                ClassifiedError(
                    type = ErrorType.NETWORK,
                    message = "Network error: ${error.message}",
                    solution = "Check your internet connection and try again",
                    isRetryable = true,
                    recommendedWaitMs = 5_000L
                )
            }

            // Geo-restriction - NOT retryable (unless VPN changes)
            msg.contains("geo") || msg.contains("not available in your") ||
            msg.contains("blocked") || msg.contains("restricted") ||
            msg.contains("country") || msg.contains("region") -> {
                ClassifiedError(
                    type = ErrorType.GEO_RESTRICTION,
                    message = "Video is geo-restricted in your region",
                    solution = "Try using a VPN or enable geo-bypass in settings",
                    isRetryable = false,
                    recommendedWaitMs = 0L
                )
            }

            // Private video - NOT retryable
            msg.contains("private") || msg.contains("not publicly available") ||
            msg.contains("login required") || msg.contains("authentication") -> {
                ClassifiedError(
                    type = ErrorType.PRIVATE_VIDEO,
                    message = "Video is private or requires authentication",
                    solution = "This video is not publicly available",
                    isRetryable = false,
                    recommendedWaitMs = 0L
                )
            }

            // Deleted video - NOT retryable
            msg.contains("deleted") || msg.contains("removed") ||
            msg.contains("not found") || msg.contains("404") ||
            msg.contains("does not exist") -> {
                ClassifiedError(
                    type = ErrorType.DELETED_VIDEO,
                    message = "Video has been deleted or removed",
                    solution = "This video no longer exists on TikTok",
                    isRetryable = false,
                    recommendedWaitMs = 0L
                )
            }

            // Rate limit - retryable with long wait
            msg.contains("rate limit") || msg.contains("429") ||
            msg.contains("too many requests") || msg.contains("throttl") -> {
                ClassifiedError(
                    type = ErrorType.RATE_LIMIT,
                    message = "Rate limited by TikTok",
                    solution = "Too many requests. Waiting before retry...",
                    isRetryable = true,
                    recommendedWaitMs = 300_000L // 5 minutes like Python
                )
            }

            // Cookies needed - NOT retryable without user action
            msg.contains("cookie") || msg.contains("captcha") ||
            msg.contains("verification") -> {
                ClassifiedError(
                    type = ErrorType.COOKIES_NEEDED,
                    message = "TikTok requires verification",
                    solution = "Anti-bot protection triggered. Try again later",
                    isRetryable = true,
                    recommendedWaitMs = 60_000L
                )
            }

            // Age restricted
            msg.contains("age") || msg.contains("mature") ||
            msg.contains("nsfw") -> {
                ClassifiedError(
                    type = ErrorType.AGE_RESTRICTED,
                    message = "Age-restricted content",
                    solution = "This content requires age verification",
                    isRetryable = false,
                    recommendedWaitMs = 0L
                )
            }

            // Unknown - retryable once
            else -> {
                ClassifiedError(
                    type = ErrorType.UNKNOWN,
                    message = "Download failed: ${error.message}",
                    solution = "An unexpected error occurred. Will retry once",
                    isRetryable = true,
                    recommendedWaitMs = 10_000L
                )
            }
        }
    }

    /**
     * Classifies HTTP response codes.
     */
    fun classifyHttpCode(code: Int, message: String = ""): ClassifiedError {
        return when (code) {
            429 -> ClassifiedError(
                ErrorType.RATE_LIMIT,
                "Rate limited (HTTP 429)",
                "Too many requests. Waiting 5 minutes...",
                isRetryable = true,
                recommendedWaitMs = 300_000L
            )
            403 -> ClassifiedError(
                ErrorType.GEO_RESTRICTION,
                "Access forbidden (HTTP 403): $message",
                "Content may be geo-restricted or require authentication",
                isRetryable = false,
                recommendedWaitMs = 0L
            )
            404 -> ClassifiedError(
                ErrorType.DELETED_VIDEO,
                "Not found (HTTP 404): $message",
                "Video may have been deleted",
                isRetryable = false,
                recommendedWaitMs = 0L
            )
            in 500..599 -> ClassifiedError(
                ErrorType.NETWORK,
                "Server error (HTTP $code): $message",
                "TikTok server error. Will retry...",
                isRetryable = true,
                recommendedWaitMs = 30_000L
            )
            else -> ClassifiedError(
                ErrorType.UNKNOWN,
                "HTTP $code: $message",
                "Unexpected response",
                isRetryable = code in 500..599,
                recommendedWaitMs = 10_000L
            )
        }
    }
}
