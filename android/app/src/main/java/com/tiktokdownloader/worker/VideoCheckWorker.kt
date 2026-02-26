package com.tiktokdownloader.worker

import android.content.Context
import android.util.Log
import androidx.work.*
import com.tiktokdownloader.data.local.database.AppDatabase
import com.tiktokdownloader.data.remote.ErrorClassifier
import com.tiktokdownloader.data.remote.RetrofitClient
import com.tiktokdownloader.data.repository.TikTokRepository
import com.tiktokdownloader.notification.NotificationHelper
import java.text.SimpleDateFormat
import java.util.*
import java.util.concurrent.TimeUnit

class VideoCheckWorker(
    context: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(context, workerParams) {

    companion object {
        private const val TAG = "VideoCheckWorker"
        private const val WORK_NAME = "tiktok_video_check"

        fun schedule(context: Context, intervalMinutes: Long = 30) {
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .setRequiresBatteryNotLow(true)
                .build()

            val workRequest = PeriodicWorkRequestBuilder<VideoCheckWorker>(
                intervalMinutes, TimeUnit.MINUTES,
                5, TimeUnit.MINUTES // flex interval
            )
                .setConstraints(constraints)
                .setBackoffCriteria(
                    BackoffPolicy.EXPONENTIAL,
                    WorkRequest.MIN_BACKOFF_MILLIS,
                    TimeUnit.MILLISECONDS
                )
                .addTag("tiktok_monitoring")
                .build()

            WorkManager.getInstance(context)
                .enqueueUniquePeriodicWork(
                    WORK_NAME,
                    ExistingPeriodicWorkPolicy.UPDATE,
                    workRequest
                )

            Log.i(TAG, "Scheduled video check every $intervalMinutes minutes")
        }

        fun cancel(context: Context) {
            WorkManager.getInstance(context).cancelUniqueWork(WORK_NAME)
            Log.i(TAG, "Cancelled video check worker")
        }

        /**
         * Triggers an immediate one-time check.
         */
        fun runOnce(context: Context) {
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()

            val workRequest = OneTimeWorkRequestBuilder<VideoCheckWorker>()
                .setConstraints(constraints)
                .setBackoffCriteria(
                    BackoffPolicy.EXPONENTIAL,
                    WorkRequest.MIN_BACKOFF_MILLIS,
                    TimeUnit.MILLISECONDS
                )
                .addTag("tiktok_manual_check")
                .build()

            WorkManager.getInstance(context).enqueue(workRequest)
            Log.i(TAG, "Triggered one-time video check")
        }
    }

    override suspend fun doWork(): Result {
        Log.i(TAG, "Starting video check...")

        val db = AppDatabase.getInstance(applicationContext)
        val repository = TikTokRepository(
            db.videoDao(), db.monitoredUserDao(), db.settingDao(), RetrofitClient.apiService
        )

        return try {
            val enabledUsers = repository.getEnabledUsers()
            if (enabledUsers.isEmpty()) {
                Log.i(TAG, "No enabled users to check")
                return Result.success()
            }

            val maxVideos = repository.getSettingValue("max_videos_per_check")?.toIntOrNull() ?: 5
            val notificationsEnabled = repository.getSettingValue("notifications_enabled") != "false"
            var notificationId = System.currentTimeMillis().toInt()
            var consecutiveFailures = 0

            for (user in enabledUsers) {
                try {
                    Log.i(TAG, "Checking user: @${user.username}")

                    val result = repository.fetchUserVideos(user.username, maxVideos)
                    result.onSuccess { videos ->
                        var newCount = 0
                        for (video in videos) {
                            val existing = repository.getVideoById(video.id)
                            if (existing == null) {
                                val dateFormat = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
                                val videoEntity = com.tiktokdownloader.data.local.entity.VideoEntity(
                                    id = video.id,
                                    url = video.downloadUrl.ifBlank { video.url },
                                    title = video.title,
                                    author = video.author,
                                    uploadDate = video.uploadDate,
                                    uploadTimestamp = video.uploadTimestamp,
                                    downloadDate = dateFormat.format(Date()),
                                    filePath = "",
                                    likes = video.likes,
                                    views = video.views,
                                    status = "pending"
                                )
                                repository.insertVideo(videoEntity)

                                // Attempt actual file download
                                val downloaded = repository.downloadVideoFile(
                                    context = applicationContext,
                                    video = videoEntity
                                )

                                if (downloaded != null) {
                                    newCount++
                                    if (notificationsEnabled) {
                                        NotificationHelper.showNewVideoNotification(
                                            applicationContext,
                                            user.username,
                                            video.title,
                                            notificationId++
                                        )
                                    }
                                } else {
                                    Log.w(TAG, "Download failed for video ${video.id}")
                                    if (notificationsEnabled) {
                                        NotificationHelper.showErrorNotification(
                                            applicationContext,
                                            "Download failed for @${user.username}",
                                            "Video ${video.id} could not be downloaded",
                                            notificationId++
                                        )
                                    }
                                }

                                // Anti-bot delay between downloads (5-15s like Python)
                                val downloadDelay = (5_000L..15_000L).random()
                                kotlinx.coroutines.delay(downloadDelay)
                            }
                        }

                        val dateFormat = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
                        repository.updateUserCheckInfo(
                            user.username,
                            dateFormat.format(Date()),
                            user.totalVideos + newCount
                        )

                        Log.i(TAG, "Found $newCount new videos for @${user.username}")
                        consecutiveFailures = 0 // Reset on success
                    }

                    result.onFailure { error ->
                        val classified = ErrorClassifier.classify(error)
                        Log.e(TAG, "Error fetching @${user.username}: ${classified.message}")

                        if (!classified.isRetryable) {
                            consecutiveFailures++
                        }

                        if (notificationsEnabled) {
                            NotificationHelper.showErrorNotification(
                                applicationContext,
                                "Check failed for @${user.username}",
                                classified.solution,
                                notificationId++
                            )
                        }
                    }

                    // Anti-bot delay between users (10-30s like Python)
                    val delay = (10_000L..30_000L).random()
                    kotlinx.coroutines.delay(delay)

                } catch (e: Exception) {
                    Log.e(TAG, "Error checking user @${user.username}: ${e.message}")
                    consecutiveFailures++
                }
            }

            // Auto-stop if ALL users had non-retryable failures (like Python)
            if (consecutiveFailures >= enabledUsers.size) {
                Log.w(TAG, "All users failed with non-retryable errors. " +
                        "Worker will retry with backoff.")
                return Result.retry()
            }

            Result.success()
        } catch (e: Exception) {
            Log.e(TAG, "Worker failed: ${e.message}", e)
            Result.retry()
        }
    }
}
