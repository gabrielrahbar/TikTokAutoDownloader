package com.tiktokdownloader.data.local.dao

import androidx.room.*
import com.tiktokdownloader.data.local.entity.VideoEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface VideoDao {
    @Query("SELECT * FROM videos ORDER BY download_date DESC")
    fun getAllVideos(): Flow<List<VideoEntity>>

    @Query("SELECT * FROM videos WHERE author = :author ORDER BY download_date DESC")
    fun getVideosByAuthor(author: String): Flow<List<VideoEntity>>

    @Query("SELECT * FROM videos WHERE id = :id")
    suspend fun getVideoById(id: String): VideoEntity?

    @Query("SELECT COUNT(*) FROM videos")
    fun getVideoCount(): Flow<Int>

    @Query("SELECT COUNT(*) FROM videos WHERE author = :author")
    suspend fun getVideoCountByAuthor(author: String): Int

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertVideo(video: VideoEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertVideos(videos: List<VideoEntity>)

    @Delete
    suspend fun deleteVideo(video: VideoEntity)

    @Query("DELETE FROM videos WHERE id = :id")
    suspend fun deleteVideoById(id: String)

    @Query("DELETE FROM videos")
    suspend fun deleteAllVideos()

    @Query("SELECT * FROM videos WHERE author = :author ORDER BY upload_timestamp DESC LIMIT 1")
    suspend fun getLatestVideoByAuthor(author: String): VideoEntity?
}
