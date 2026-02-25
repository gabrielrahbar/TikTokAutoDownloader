package com.tiktokdownloader.data.repository

import android.content.Context
import com.tiktokdownloader.data.local.dao.MonitoredUserDao
import com.tiktokdownloader.data.local.dao.SettingDao
import com.tiktokdownloader.data.local.dao.VideoDao
import com.tiktokdownloader.data.local.entity.MonitoredUserEntity
import com.tiktokdownloader.data.local.entity.SettingEntity
import com.tiktokdownloader.data.local.entity.VideoEntity
import com.tiktokdownloader.data.remote.RetryHelper
import com.tiktokdownloader.data.remote.TikTokApiService
import com.tiktokdownloader.data.remote.VideoData
import com.tiktokdownloader.data.remote.VideoDownloadManager
import kotlinx.coroutines.flow.Flow

class TikTokRepository(
    private val videoDao: VideoDao,
    private val userDao: MonitoredUserDao,
    private val settingDao: SettingDao,
    private val apiService: TikTokApiService
) {
    // ── Videos ──────────────────────────────────────────────

    fun getAllVideos(): Flow<List<VideoEntity>> = videoDao.getAllVideos()

    fun getVideosByAuthor(author: String): Flow<List<VideoEntity>> =
        videoDao.getVideosByAuthor(author)

    fun getVideoCount(): Flow<Int> = videoDao.getVideoCount()

    suspend fun getVideoById(id: String): VideoEntity? = videoDao.getVideoById(id)

    suspend fun insertVideo(video: VideoEntity) = videoDao.insertVideo(video)

    suspend fun deleteVideo(video: VideoEntity) = videoDao.deleteVideo(video)

    suspend fun deleteVideoById(id: String) = videoDao.deleteVideoById(id)

    suspend fun deleteAllVideos() = videoDao.deleteAllVideos()

    suspend fun getLatestVideoByAuthor(author: String): VideoEntity? =
        videoDao.getLatestVideoByAuthor(author)

    // ── Monitored Users ─────────────────────────────────────

    fun getAllUsers(): Flow<List<MonitoredUserEntity>> = userDao.getAllUsers()

    fun getUserCount(): Flow<Int> = userDao.getUserCount()

    suspend fun getEnabledUsers(): List<MonitoredUserEntity> = userDao.getEnabledUsers()

    suspend fun getUserByUsername(username: String): MonitoredUserEntity? =
        userDao.getUserByUsername(username)

    suspend fun insertUser(user: MonitoredUserEntity) = userDao.insertUser(user)

    suspend fun updateUser(user: MonitoredUserEntity) = userDao.updateUser(user)

    suspend fun deleteUserByUsername(username: String) = userDao.deleteUserByUsername(username)

    suspend fun setUserEnabled(username: String, enabled: Boolean) =
        userDao.setUserEnabled(username, enabled)

    suspend fun updateUserCheckInfo(username: String, lastCheck: String, totalVideos: Int) =
        userDao.updateUserCheckInfo(username, lastCheck, totalVideos)

    suspend fun deleteAllUsers() = userDao.deleteAllUsers()

    // ── Settings ────────────────────────────────────────────

    suspend fun getSettingValue(key: String): String? = settingDao.getSettingValue(key)

    suspend fun setSetting(key: String, value: String) =
        settingDao.insertSetting(SettingEntity(key, value))

    suspend fun deleteAllSettings() = settingDao.deleteAllSettings()

    // ── Remote API with Retry ───────────────────────────────

    /**
     * Fetches user videos with automatic retry and error classification.
     * Mirrors Python's get_user_videos() with retry_on_network_error.
     */
    suspend fun fetchUserVideos(username: String, count: Int = 10): Result<List<VideoData>> {
        return RetryHelper.withRetry(config = RetryHelper.DEFAULT_API) {
            val response = apiService.getUserVideos(username, count)
            if (response.isSuccessful) {
                response.body()?.videos ?: emptyList()
            } else {
                throw Exception("API error: ${response.code()} ${response.message()}")
            }
        }
    }

    /**
     * Fetches single video info with retry logic.
     */
    suspend fun fetchVideoInfo(videoId: String): Result<VideoData> {
        return RetryHelper.withRetry(config = RetryHelper.DEFAULT_API) {
            val response = apiService.getVideoInfo(videoId)
            if (response.isSuccessful && response.body()?.video != null) {
                response.body()!!.video!!
            } else {
                throw Exception("Video not found: ${response.code()}")
            }
        }
    }

    /**
     * Downloads a video file to device storage.
     * Mirrors Python's download_video() with retry and error handling.
     *
     * @return Updated VideoEntity with file path, or null on failure
     */
    suspend fun downloadVideoFile(
        context: Context,
        video: VideoEntity,
        onProgress: ((Float) -> Unit)? = null
    ): VideoEntity? {
        val downloadManager = VideoDownloadManager(context)
        val downloadUrl = video.url.ifBlank { return null }

        val result = downloadManager.downloadVideo(
            downloadUrl = downloadUrl,
            videoId = video.id,
            author = video.author,
            onProgress = onProgress
        )

        return if (result.success) {
            val updated = video.copy(
                filePath = result.filePath,
                status = "downloaded"
            )
            videoDao.insertVideo(updated)
            updated
        } else {
            val failed = video.copy(status = "failed")
            videoDao.insertVideo(failed)
            null
        }
    }
}
