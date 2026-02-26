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
     * Fetches user videos from the FastAPI backend with automatic retry.
     * The backend wraps Python's get_user_videos() with yt-dlp.
     *
     * Response envelope: { success, data: { videos: [...], count }, error }
     */
    suspend fun fetchUserVideos(username: String, count: Int = 5): Result<List<VideoData>> {
        return RetryHelper.withRetry(config = RetryHelper.DEFAULT_API) {
            val response = apiService.getUserVideos(username, count)
            if (!response.isSuccessful) {
                throw Exception("HTTP ${response.code()}: ${response.message()}")
            }
            val body = response.body()
                ?: throw Exception("Empty response body")
            if (!body.success) {
                throw Exception(body.error ?: "Unknown backend error")
            }

            // Parse videos list from data map
            @Suppress("UNCHECKED_CAST")
            val rawVideos = (body.data?.get("videos") as? List<Map<String, Any?>>) ?: emptyList()
            rawVideos.map { m ->
                VideoData(
                    id = m["id"]?.toString() ?: "",
                    url = m["url"]?.toString() ?: "",
                    title = m["title"]?.toString() ?: "",
                    author = m["author"]?.toString() ?: username,
                    uploadDate = (m["upload_date"] ?: m["uploadDate"])?.toString() ?: "",
                    uploadTimestamp = (m["upload_timestamp"] ?: m["uploadTimestamp"])
                        ?.toString()?.toDoubleOrNull()?.toLong() ?: 0L,
                    likes = (m["likes"])?.toString()?.toDoubleOrNull()?.toLong() ?: 0L,
                    views = (m["views"])?.toString()?.toDoubleOrNull()?.toLong() ?: 0L,
                    downloadUrl = (m["download_url"] ?: m["downloadUrl"])?.toString() ?: "",
                )
            }
        }
    }

    /**
     * Fetches single video info from the FastAPI backend with retry.
     *
     * Response envelope: { success, data: { video: { ... } }, error }
     */
    suspend fun fetchVideoInfo(videoId: String, username: String? = null): Result<VideoData> {
        return RetryHelper.withRetry(config = RetryHelper.DEFAULT_API) {
            val response = apiService.getVideoInfo(videoId, username)
            if (!response.isSuccessful) {
                throw Exception("HTTP ${response.code()}: ${response.message()}")
            }
            val body = response.body()
                ?: throw Exception("Empty response body")
            if (!body.success) {
                throw Exception(body.error ?: "Unknown backend error")
            }

            @Suppress("UNCHECKED_CAST")
            val m = (body.data?.get("video") as? Map<String, Any?>)
                ?: throw Exception("Video not found in response")
            VideoData(
                id = m["id"]?.toString() ?: videoId,
                url = m["url"]?.toString() ?: "",
                title = m["title"]?.toString() ?: "",
                author = m["author"]?.toString() ?: "",
                uploadDate = (m["upload_date"] ?: m["uploadDate"])?.toString() ?: "",
                uploadTimestamp = (m["upload_timestamp"] ?: m["uploadTimestamp"])
                    ?.toString()?.toDoubleOrNull()?.toLong() ?: 0L,
                likes = (m["likes"])?.toString()?.toDoubleOrNull()?.toLong() ?: 0L,
                views = (m["views"])?.toString()?.toDoubleOrNull()?.toLong() ?: 0L,
                downloadUrl = (m["download_url"] ?: m["downloadUrl"])?.toString() ?: "",
            )
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
