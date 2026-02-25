package com.tiktokdownloader.data.repository

import com.tiktokdownloader.data.local.dao.MonitoredUserDao
import com.tiktokdownloader.data.local.dao.SettingDao
import com.tiktokdownloader.data.local.dao.VideoDao
import com.tiktokdownloader.data.local.entity.MonitoredUserEntity
import com.tiktokdownloader.data.local.entity.SettingEntity
import com.tiktokdownloader.data.local.entity.VideoEntity
import com.tiktokdownloader.data.remote.TikTokApiService
import com.tiktokdownloader.data.remote.VideoData
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

    // ── Remote API ──────────────────────────────────────────

    suspend fun fetchUserVideos(username: String, count: Int = 10): Result<List<VideoData>> {
        return try {
            val response = apiService.getUserVideos(username, count)
            if (response.isSuccessful) {
                Result.success(response.body()?.videos ?: emptyList())
            } else {
                Result.failure(Exception("API error: ${response.code()} ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun fetchVideoInfo(videoId: String): Result<VideoData> {
        return try {
            val response = apiService.getVideoInfo(videoId)
            if (response.isSuccessful && response.body()?.video != null) {
                Result.success(response.body()!!.video!!)
            } else {
                Result.failure(Exception("Video not found"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
