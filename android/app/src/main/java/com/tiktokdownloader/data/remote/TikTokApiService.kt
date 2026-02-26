package com.tiktokdownloader.data.remote

import retrofit2.Response
import retrofit2.http.GET
import retrofit2.http.Path
import retrofit2.http.Query

/**
 * Retrofit service matching the FastAPI backend endpoints defined in api_server.py.
 *
 * All responses follow the standard envelope:
 * ```json
 * { "success": true, "data": { ... }, "error": null }
 * ```
 */
interface TikTokApiService {

    /** Health check – GET /health */
    @GET("health")
    suspend fun healthCheck(): Response<ApiResponse>

    /** Get recent videos for a user – GET /api/user/{username}/videos?count=N */
    @GET("api/user/{username}/videos")
    suspend fun getUserVideos(
        @Path("username") username: String,
        @Query("count") count: Int = 5
    ): Response<ApiResponse>

    /** Get single video info – GET /api/video/{video_id}/info */
    @GET("api/video/{video_id}/info")
    suspend fun getVideoInfo(
        @Path("video_id") videoId: String
    ): Response<ApiResponse>
}

// ---------------------------------------------------------------------------
// Standard envelope returned by every backend endpoint
// ---------------------------------------------------------------------------

/**
 * Standard API response envelope from the FastAPI backend.
 * Maps to: `{ "success": bool, "data": { ... }, "error": str|null }`
 */
data class ApiResponse(
    val success: Boolean = false,
    val data: Map<String, Any?>? = null,
    val error: String? = null
)

// ---------------------------------------------------------------------------
// Domain-level data classes parsed from ApiResponse.data
// ---------------------------------------------------------------------------

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
