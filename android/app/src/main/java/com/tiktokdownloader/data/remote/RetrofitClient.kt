package com.tiktokdownloader.data.remote

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object RetrofitClient {

    // TODO: Replace with your Render.com deployment URL
    // Example: "https://tiktok-downloader-api.onrender.com/"
    private const val BASE_URL = "https://tiktok-downloader-api.onrender.com/"

    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BASIC
    }

    /**
     * OkHttp client configured for the FastAPI backend.
     * Longer timeouts to accommodate Render.com free tier cold starts (~30 s).
     */
    private val httpClient = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .addInterceptor { chain ->
            val request = chain.request().newBuilder()
                .addHeader("Accept", "application/json")
                .build()
            chain.proceed(request)
        }
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(90, TimeUnit.SECONDS)   // long read timeout for cold starts
        .writeTimeout(30, TimeUnit.SECONDS)
        .followRedirects(true)
        .followSslRedirects(true)
        .build()

    val instance: Retrofit by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(httpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    val apiService: TikTokApiService by lazy {
        instance.create(TikTokApiService::class.java)
    }

    /** Exposed OkHttp client for direct download operations */
    val okHttpClient: OkHttpClient get() = httpClient
}
