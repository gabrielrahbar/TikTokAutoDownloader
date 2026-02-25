package com.tiktokdownloader.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "monitored_users")
data class MonitoredUserEntity(
    @PrimaryKey
    val username: String,
    @ColumnInfo(name = "last_check")
    val lastCheck: String = "",
    @ColumnInfo(name = "last_video_id")
    val lastVideoId: String = "",
    @ColumnInfo(name = "last_video_timestamp")
    val lastVideoTimestamp: Long = 0L,
    @ColumnInfo(name = "total_videos")
    val totalVideos: Int = 0,
    val enabled: Boolean = true
)
