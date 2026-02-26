package com.tiktokdownloader.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "videos")
data class VideoEntity(
    @PrimaryKey
    val id: String,
    val url: String = "",
    val title: String = "",
    val author: String = "",
    @ColumnInfo(name = "upload_date")
    val uploadDate: String = "",
    @ColumnInfo(name = "upload_timestamp")
    val uploadTimestamp: Long = 0L,
    @ColumnInfo(name = "download_date")
    val downloadDate: String = "",
    @ColumnInfo(name = "file_path")
    val filePath: String = "",
    val likes: Long = 0L,
    val views: Long = 0L,
    val status: String = "downloaded"
)
