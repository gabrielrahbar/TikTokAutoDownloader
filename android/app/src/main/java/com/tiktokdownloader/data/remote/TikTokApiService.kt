package com.tiktokdownloader.data.remote

import retrofit2.Response
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.Query
import retrofit2.http.Url

/**
 * Retrofit service for accessing TikTok public data.
 * Uses publicly available endpoints only.
 */
interface TikTokApiService {

    @GET("api/user/posts")
    suspend fun getUserVideos(
        @Query("username") username: String,
        @Query("count") count: Int = 10,
        @Query("cursor") cursor: String = "0"
    ): Response<UserVideosResponse>

    @GET("api/video/info")
    suspend fun getVideoInfo(
        @Query("video_id") videoId: String
    ): Response<VideoInfoResponse>

    /**
     * Fetches a TikTok page to extract video metadata.
     * Used as fallback when API endpoints are unavailable.
     */
    @GET
    suspend fun fetchPage(
        @Url url: String,
        @Header("User-Agent") userAgent: String =
            "Mozilla/5.0 (Linux; Android 14; Pixel 8) " +
            "AppleWebKit/537.36 (KHTML, like Gecko) " +
            "Chrome/120.0.0.0 Mobile Safari/537.36"
    ): Response<okhttp3.ResponseBody>
}

data class UserVideosResponse(
    val videos: List<VideoData> = emptyList(),
    val hasMore: Boolean = false,
    val cursor: String = "0"
)

data class VideoInfoResponse(
    val video: VideoData? = null
)

data class VideoData(
    val id: String = "",
    val url: String = "",
    val title: String = "",
    val author: String = "",
    val uploadDate: String = "",
    val uploadTimestamp: Long = 0L,
    val likes: Long = 0L,
    val views: Long = 0L,
    val downloadUrl: String = ""
)
