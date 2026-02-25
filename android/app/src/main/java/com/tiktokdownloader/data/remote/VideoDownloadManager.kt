package com.tiktokdownloader.data.remote

import android.content.ContentValues
import android.content.Context
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import android.util.Log
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.io.FileOutputStream
import java.io.IOException
import java.util.concurrent.TimeUnit

/**
 * Handles actual video file downloads to device storage.
 * Mirrors the download logic from Python's tiktok_downloader_advanced.py.
 *
 * Supports:
 * - Direct HTTP download with anti-bot headers
 * - Scoped Storage (Android 11+)
 * - Legacy storage (Android 10-)
 * - Retry with exponential backoff
 * - Download progress tracking
 */
class VideoDownloadManager(private val context: Context) {

    companion object {
        private const val TAG = "VideoDownloadManager"
        private const val DOWNLOAD_DIR = "TikTokDownloader"
    }

    data class DownloadResult(
        val success: Boolean,
        val filePath: String = "",
        val error: ErrorClassifier.ClassifiedError? = null
    )

    // OkHttp client configured for video downloads with anti-bot headers
    private val downloadClient = OkHttpClient.Builder()
        .connectTimeout(60, TimeUnit.SECONDS)
        .readTimeout(120, TimeUnit.SECONDS)
        .writeTimeout(60, TimeUnit.SECONDS)
        .followRedirects(true)
        .followSslRedirects(true)
        .addInterceptor { chain ->
            val request = chain.request().newBuilder()
                .addHeader("User-Agent",
                    "Mozilla/5.0 (Linux; Android 14; Pixel 8) " +
                    "AppleWebKit/537.36 (KHTML, like Gecko) " +
                    "Chrome/120.0.0.0 Mobile Safari/537.36")
                .addHeader("Accept", "*/*")
                .addHeader("Accept-Language", "en-US,en;q=0.9")
                .addHeader("Referer", "https://www.tiktok.com/")
                .addHeader("Origin", "https://www.tiktok.com")
                .build()
            chain.proceed(request)
        }
        .build()

    /**
     * Downloads a video file from the given URL.
     * Uses retry logic with exponential backoff.
     *
     * @param downloadUrl Direct URL to the video file
     * @param videoId Unique video identifier
     * @param author Video author username
     * @param onProgress Optional progress callback (0.0 to 1.0)
     * @return DownloadResult with file path or error details
     */
    suspend fun downloadVideo(
        downloadUrl: String,
        videoId: String,
        author: String,
        onProgress: ((Float) -> Unit)? = null
    ): DownloadResult {
        if (downloadUrl.isBlank()) {
            return DownloadResult(
                success = false,
                error = ErrorClassifier.ClassifiedError(
                    type = ErrorClassifier.ErrorType.UNKNOWN,
                    message = "No download URL available",
                    solution = "Video URL could not be resolved",
                    isRetryable = false,
                    recommendedWaitMs = 0L
                )
            )
        }

        val result = RetryHelper.withRetry(
            config = RetryHelper.DEFAULT_NETWORK,
            onRetry = { attempt, delayMs, error ->
                Log.w(TAG, "Download retry $attempt for video $videoId, " +
                        "waiting ${delayMs / 1000}s: ${error.message}")
            }
        ) {
            performDownload(downloadUrl, videoId, author, onProgress)
        }

        return result.getOrElse { error ->
            val classified = ErrorClassifier.classify(error)
            Log.e(TAG, "Download failed for $videoId: ${classified.message}")
            DownloadResult(success = false, error = classified)
        }
    }

    /**
     * Performs the actual HTTP download operation.
     */
    private fun performDownload(
        url: String,
        videoId: String,
        author: String,
        onProgress: ((Float) -> Unit)?
    ): DownloadResult {
        val sanitizedAuthor = author.replace(Regex("[^a-zA-Z0-9._-]"), "_")
        val fileName = "${sanitizedAuthor}_${videoId}.mp4"

        val request = Request.Builder()
            .url(url)
            .build()

        val response = downloadClient.newCall(request).execute()

        if (!response.isSuccessful) {
            val classified = ErrorClassifier.classifyHttpCode(response.code, response.message)
            if (classified.isRetryable) {
                throw IOException("HTTP ${response.code}: ${response.message}")
            }
            return DownloadResult(success = false, error = classified)
        }

        val body = response.body ?: throw IOException("Empty response body")
        val contentLength = body.contentLength()

        val filePath = saveToStorage(fileName, body.byteStream(), contentLength, onProgress)
            ?: throw IOException("Failed to save video to storage")

        Log.i(TAG, "Downloaded video $videoId to $filePath")
        return DownloadResult(success = true, filePath = filePath)
    }

    /**
     * Saves video bytes to device storage.
     * Uses Scoped Storage for Android 10+ and legacy storage for older versions.
     */
    private fun saveToStorage(
        fileName: String,
        inputStream: java.io.InputStream,
        contentLength: Long,
        onProgress: ((Float) -> Unit)?
    ): String? {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            saveToScopedStorage(fileName, inputStream, contentLength, onProgress)
        } else {
            saveToLegacyStorage(fileName, inputStream, contentLength, onProgress)
        }
    }

    /**
     * Scoped Storage (Android 10+) - saves to Movies/TikTokDownloader via MediaStore.
     */
    private fun saveToScopedStorage(
        fileName: String,
        inputStream: java.io.InputStream,
        contentLength: Long,
        onProgress: ((Float) -> Unit)?
    ): String? {
        val contentValues = ContentValues().apply {
            put(MediaStore.MediaColumns.DISPLAY_NAME, fileName)
            put(MediaStore.MediaColumns.MIME_TYPE, "video/mp4")
            put(MediaStore.MediaColumns.RELATIVE_PATH,
                "${Environment.DIRECTORY_MOVIES}/$DOWNLOAD_DIR")
        }

        val resolver = context.contentResolver
        val uri = resolver.insert(MediaStore.Video.Media.EXTERNAL_CONTENT_URI, contentValues)
            ?: return null

        return try {
            resolver.openOutputStream(uri)?.use { outputStream ->
                copyWithProgress(inputStream, outputStream, contentLength, onProgress)
            }
            uri.toString()
        } catch (e: Exception) {
            resolver.delete(uri, null, null)
            throw e
        }
    }

    /**
     * Legacy storage (pre-Android 10) - saves to external storage directory.
     */
    @Suppress("DEPRECATION")
    private fun saveToLegacyStorage(
        fileName: String,
        inputStream: java.io.InputStream,
        contentLength: Long,
        onProgress: ((Float) -> Unit)?
    ): String? {
        val downloadDir = File(
            Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_MOVIES),
            DOWNLOAD_DIR
        )
        if (!downloadDir.exists()) downloadDir.mkdirs()

        val file = File(downloadDir, fileName)
        FileOutputStream(file).use { outputStream ->
            copyWithProgress(inputStream, outputStream, contentLength, onProgress)
        }
        return file.absolutePath
    }

    /**
     * Copies input to output stream with progress tracking.
     */
    private fun copyWithProgress(
        input: java.io.InputStream,
        output: java.io.OutputStream,
        contentLength: Long,
        onProgress: ((Float) -> Unit)?
    ) {
        val buffer = ByteArray(8192)
        var bytesRead: Int
        var totalBytesRead = 0L

        while (input.read(buffer).also { bytesRead = it } != -1) {
            output.write(buffer, 0, bytesRead)
            totalBytesRead += bytesRead

            if (contentLength > 0 && onProgress != null) {
                onProgress(totalBytesRead.toFloat() / contentLength.toFloat())
            }
        }
        output.flush()
    }
}
