package com.tiktokdownloader.ui.viewmodel

import android.app.Application
import android.content.Intent
import androidx.core.content.FileProvider
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.tiktokdownloader.data.local.database.AppDatabase
import com.tiktokdownloader.data.local.entity.VideoEntity
import com.tiktokdownloader.data.remote.RetrofitClient
import com.tiktokdownloader.data.repository.TikTokRepository
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.io.File

data class GalleryUiState(
    val videos: List<VideoEntity> = emptyList(),
    val isLoading: Boolean = true,
    val selectedVideo: VideoEntity? = null
)

class GalleryViewModel(application: Application) : AndroidViewModel(application) {

    private val db = AppDatabase.getInstance(application)
    private val repository = TikTokRepository(
        db.videoDao(), db.monitoredUserDao(), db.settingDao(), RetrofitClient.apiService
    )

    private val _uiState = MutableStateFlow(GalleryUiState())
    val uiState: StateFlow<GalleryUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            repository.getAllVideos().collect { videos ->
                _uiState.update { it.copy(videos = videos, isLoading = false) }
            }
        }
    }

    fun selectVideo(video: VideoEntity?) {
        _uiState.update { it.copy(selectedVideo = video) }
    }

    fun deleteVideo(video: VideoEntity) {
        viewModelScope.launch {
            // Delete local file
            val file = File(video.filePath)
            if (file.exists()) file.delete()
            repository.deleteVideo(video)
            _uiState.update { it.copy(selectedVideo = null) }
        }
    }

    fun shareVideo(video: VideoEntity) {
        val context = getApplication<Application>()
        val file = File(video.filePath)
        if (!file.exists()) return

        val uri = FileProvider.getUriForFile(
            context,
            "${context.packageName}.fileprovider",
            file
        )
        val shareIntent = Intent(Intent.ACTION_SEND).apply {
            type = "video/mp4"
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        context.startActivity(Intent.createChooser(shareIntent, "Share video").apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        })
    }
}
