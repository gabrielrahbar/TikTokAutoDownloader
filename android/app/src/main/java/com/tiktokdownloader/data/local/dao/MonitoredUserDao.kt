package com.tiktokdownloader.data.local.dao

import androidx.room.*
import com.tiktokdownloader.data.local.entity.MonitoredUserEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface MonitoredUserDao {
    @Query("SELECT * FROM monitored_users ORDER BY username ASC")
    fun getAllUsers(): Flow<List<MonitoredUserEntity>>

    @Query("SELECT * FROM monitored_users WHERE enabled = 1 ORDER BY username ASC")
    suspend fun getEnabledUsers(): List<MonitoredUserEntity>

    @Query("SELECT * FROM monitored_users WHERE username = :username")
    suspend fun getUserByUsername(username: String): MonitoredUserEntity?

    @Query("SELECT COUNT(*) FROM monitored_users")
    fun getUserCount(): Flow<Int>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertUser(user: MonitoredUserEntity)

    @Update
    suspend fun updateUser(user: MonitoredUserEntity)

    @Delete
    suspend fun deleteUser(user: MonitoredUserEntity)

    @Query("DELETE FROM monitored_users WHERE username = :username")
    suspend fun deleteUserByUsername(username: String)

    @Query("UPDATE monitored_users SET enabled = :enabled WHERE username = :username")
    suspend fun setUserEnabled(username: String, enabled: Boolean)

    @Query("UPDATE monitored_users SET last_check = :lastCheck, total_videos = :totalVideos WHERE username = :username")
    suspend fun updateUserCheckInfo(username: String, lastCheck: String, totalVideos: Int)

    @Query("DELETE FROM monitored_users")
    suspend fun deleteAllUsers()
}
