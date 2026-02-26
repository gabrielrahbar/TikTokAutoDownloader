package com.tiktokdownloader.ui.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.tiktokdownloader.data.local.database.AppDatabase
import com.tiktokdownloader.data.remote.RetrofitClient
import com.tiktokdownloader.data.repository.TikTokRepository
import com.tiktokdownloader.domain.model.AppSettings
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

class SettingsViewModel(application: Application) : AndroidViewModel(application) {

    private val db = AppDatabase.getInstance(application)
    private val repository = TikTokRepository(
        db.videoDao(), db.monitoredUserDao(), db.settingDao(), RetrofitClient.apiService
    )

    private val _settings = MutableStateFlow(AppSettings())
    val settings: StateFlow<AppSettings> = _settings.asStateFlow()

    private val _videoCount = MutableStateFlow(0)
    val videoCount: StateFlow<Int> = _videoCount.asStateFlow()

    private val _userCount = MutableStateFlow(0)
    val userCount: StateFlow<Int> = _userCount.asStateFlow()

    init {
        loadSettings()
        viewModelScope.launch {
            repository.getVideoCount().collect { count ->
                _videoCount.value = count
            }
        }
        viewModelScope.launch {
            repository.getUserCount().collect { count ->
                _userCount.value = count
            }
        }
    }

    private fun loadSettings() {
        viewModelScope.launch {
            val interval = repository.getSettingValue("check_interval")?.toIntOrNull() ?: 30
            val maxVideos = repository.getSettingValue("max_videos_per_check")?.toIntOrNull() ?: 5
            val notifications = repository.getSettingValue("notifications_enabled") != "false"
            val quality = repository.getSettingValue("video_quality") ?: "best"
            val withAudio = repository.getSettingValue("with_audio") != "false"
            val geoBypass = repository.getSettingValue("geo_bypass") != "false"
            val disclaimer = repository.getSettingValue("disclaimer_accepted") == "true"

            _settings.value = AppSettings(
                checkIntervalMinutes = interval,
                maxVideosPerCheck = maxVideos,
                notificationsEnabled = notifications,
                videoQuality = quality,
                withAudio = withAudio,
                geoBypass = geoBypass,
                disclaimerAccepted = disclaimer
            )
        }
    }

    fun updateCheckInterval(minutes: Int) {
        viewModelScope.launch {
            repository.setSetting("check_interval", minutes.toString())
            _settings.update { it.copy(checkIntervalMinutes = minutes) }
        }
    }

    fun updateMaxVideos(max: Int) {
        viewModelScope.launch {
            repository.setSetting("max_videos_per_check", max.toString())
            _settings.update { it.copy(maxVideosPerCheck = max) }
        }
    }

    fun updateNotifications(enabled: Boolean) {
        viewModelScope.launch {
            repository.setSetting("notifications_enabled", enabled.toString())
            _settings.update { it.copy(notificationsEnabled = enabled) }
        }
    }

    fun updateVideoQuality(quality: String) {
        viewModelScope.launch {
            repository.setSetting("video_quality", quality)
            _settings.update { it.copy(videoQuality = quality) }
        }
    }

    fun updateWithAudio(withAudio: Boolean) {
        viewModelScope.launch {
            repository.setSetting("with_audio", withAudio.toString())
            _settings.update { it.copy(withAudio = withAudio) }
        }
    }

    fun updateGeoBypass(enabled: Boolean) {
        viewModelScope.launch {
            repository.setSetting("geo_bypass", enabled.toString())
            _settings.update { it.copy(geoBypass = enabled) }
        }
    }

    fun clearDatabase() {
        viewModelScope.launch {
            repository.deleteAllVideos()
            repository.deleteAllUsers()
        }
    }
}
