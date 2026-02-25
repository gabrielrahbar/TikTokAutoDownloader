package com.tiktokdownloader.worker

import android.content.Context
import android.util.Log
import androidx.work.*
import com.tiktokdownloader.data.local.database.AppDatabase
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
                                repository.insertVideo(
                                    com.tiktokdownloader.data.local.entity.VideoEntity(
                                        id = video.id,
                                        url = video.url,
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
                                )
                                newCount++

                                if (notificationsEnabled) {
                                    NotificationHelper.showNewVideoNotification(
                                        applicationContext,
                                        user.username,
                                        video.title,
                                        notificationId++
                                    )
                                }
                            }
                        }

                        val dateFormat = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
                        repository.updateUserCheckInfo(
                            user.username,
                            dateFormat.format(Date()),
                            user.totalVideos + newCount
                        )

                        Log.i(TAG, "Found $newCount new videos for @${user.username}")
                    }

                    // Anti-bot delay between users (randomized)
                    val delay = (10_000L..30_000L).random()
                    kotlinx.coroutines.delay(delay)

                } catch (e: Exception) {
                    Log.e(TAG, "Error checking user @${user.username}: ${e.message}")
                }
            }

            Result.success()
        } catch (e: Exception) {
            Log.e(TAG, "Worker failed: ${e.message}", e)
            Result.retry()
        }
    }
}
