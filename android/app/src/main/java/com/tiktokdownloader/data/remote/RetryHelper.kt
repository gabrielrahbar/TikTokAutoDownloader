package com.tiktokdownloader.data.remote

import android.util.Log
import kotlinx.coroutines.delay

/**
 * Retry logic mirroring Python retry_utils.py.
 * Implements exponential backoff with configurable parameters.
 */
object RetryHelper {

    private const val TAG = "RetryHelper"

    data class RetryConfig(
        val maxRetries: Int = 3,
        val initialDelayMs: Long = 5_000L,
        val maxDelayMs: Long = 60_000L,
        val backoffMultiplier: Double = 2.0
    )

    val DEFAULT_NETWORK = RetryConfig(
        maxRetries = 3,
        initialDelayMs = 5_000L,
        maxDelayMs = 60_000L,
        backoffMultiplier = 2.0
    )

    val DEFAULT_API = RetryConfig(
        maxRetries = 2,
        initialDelayMs = 10_000L,
        maxDelayMs = 120_000L,
        backoffMultiplier = 3.0
    )

    /**
     * Execute an operation with automatic retry and exponential backoff.
     * Mirrors Python's @retry_on_network_error decorator.
     *
     * @param config Retry configuration
     * @param onRetry Callback invoked before each retry with (attempt, delayMs, error)
     * @param shouldRetry Optional predicate to determine if retry should happen
     * @param operation The suspending operation to execute
     * @return Result of the operation
     */
    suspend fun <T> withRetry(
        config: RetryConfig = DEFAULT_NETWORK,
        onRetry: ((attempt: Int, delayMs: Long, error: Throwable) -> Unit)? = null,
        shouldRetry: ((Throwable) -> Boolean)? = null,
        operation: suspend (attempt: Int) -> T
    ): Result<T> {
        var lastError: Throwable? = null
        var currentDelay = config.initialDelayMs

        for (attempt in 1..config.maxRetries) {
            try {
                val result = operation(attempt)
                if (attempt > 1) {
                    Log.i(TAG, "Operation succeeded on attempt $attempt")
                }
                return Result.success(result)
            } catch (e: Throwable) {
                lastError = e

                // Check if we should retry this error type
                val classifiedError = ErrorClassifier.classify(e)
                val canRetry = shouldRetry?.invoke(e) ?: classifiedError.isRetryable

                if (!canRetry) {
                    Log.w(TAG, "Non-retryable error on attempt $attempt: ${classifiedError.message}")
                    return Result.failure(e)
                }

                if (attempt < config.maxRetries) {
                    // Use the classified error's recommended wait if it's longer
                    val waitMs = maxOf(currentDelay, classifiedError.recommendedWaitMs)
                        .coerceAtMost(config.maxDelayMs)

                    // Add jitter (±20%) to prevent thundering herd
                    val jitter = (waitMs * 0.2 * (Math.random() * 2 - 1)).toLong()
                    val actualDelay = (waitMs + jitter).coerceAtLeast(1000L)

                    Log.w(TAG, "Attempt $attempt failed: ${e.message}. " +
                            "Retrying in ${actualDelay / 1000}s...")

                    onRetry?.invoke(attempt, actualDelay, e)
                    delay(actualDelay)

                    // Exponential backoff
                    currentDelay = (currentDelay * config.backoffMultiplier).toLong()
                        .coerceAtMost(config.maxDelayMs)
                } else {
                    Log.e(TAG, "All $attempt attempts failed: ${e.message}")
                }
            }
        }

        return Result.failure(lastError ?: Exception("All retry attempts exhausted"))
    }

    /**
     * Execute a simple operation with default retry config, returning null on failure.
     * Mirrors Python's safe_execute().
     */
    suspend fun <T> safeExecute(
        config: RetryConfig = DEFAULT_NETWORK,
        defaultValue: T? = null,
        operation: suspend () -> T
    ): T? {
        return try {
            withRetry(config = config) { operation() }.getOrNull() ?: defaultValue
        } catch (e: Exception) {
            Log.e(TAG, "safeExecute failed: ${e.message}")
            defaultValue
        }
    }
}
