package com.tiktokdownloader.domain.model

data class Video(
    val id: String,
    val url: String = "",
    val title: String = "",
    val author: String = "",
    val uploadDate: String = "",
    val uploadTimestamp: Long = 0L,
    val downloadDate: String = "",
    val filePath: String = "",
    val likes: Long = 0L,
    val views: Long = 0L,
    val status: String = "downloaded"
)

data class MonitoredUser(
    val username: String,
    val lastCheck: String = "",
    val lastVideoId: String = "",
    val lastVideoTimestamp: Long = 0L,
    val totalVideos: Int = 0,
    val enabled: Boolean = true
)

data class AppSettings(
    val checkIntervalMinutes: Int = 30,
    val maxVideosPerCheck: Int = 5,
    val notificationsEnabled: Boolean = true,
    val videoQuality: String = "best",
    val withAudio: Boolean = true,
    val geoBypass: Boolean = true,
    val disclaimerAccepted: Boolean = false
)
