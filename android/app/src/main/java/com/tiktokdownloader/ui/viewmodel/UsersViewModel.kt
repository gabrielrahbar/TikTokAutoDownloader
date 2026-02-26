package com.tiktokdownloader.ui.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.tiktokdownloader.data.local.database.AppDatabase
import com.tiktokdownloader.data.local.entity.MonitoredUserEntity
import com.tiktokdownloader.data.remote.RetrofitClient
import com.tiktokdownloader.data.repository.TikTokRepository
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

data class UsersUiState(
    val users: List<MonitoredUserEntity> = emptyList(),
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    val showAddDialog: Boolean = false
)

class UsersViewModel(application: Application) : AndroidViewModel(application) {

    private val db = AppDatabase.getInstance(application)
    private val repository = TikTokRepository(
        db.videoDao(), db.monitoredUserDao(), db.settingDao(), RetrofitClient.apiService
    )

    private val _uiState = MutableStateFlow(UsersUiState())
    val uiState: StateFlow<UsersUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            repository.getAllUsers().collect { users ->
                _uiState.update { it.copy(users = users, isLoading = false) }
            }
        }
    }

    fun showAddDialog() {
        _uiState.update { it.copy(showAddDialog = true) }
    }

    fun hideAddDialog() {
        _uiState.update { it.copy(showAddDialog = false) }
    }

    fun addUser(username: String) {
        val cleanUsername = username.trim().removePrefix("@")
        if (cleanUsername.isBlank()) {
            _uiState.update { it.copy(errorMessage = "Username cannot be empty") }
            return
        }
        viewModelScope.launch {
            val existing = repository.getUserByUsername(cleanUsername)
            if (existing != null) {
                _uiState.update { it.copy(errorMessage = "User @$cleanUsername is already monitored") }
                return@launch
            }
            repository.insertUser(MonitoredUserEntity(username = cleanUsername))
            _uiState.update { it.copy(showAddDialog = false, errorMessage = null) }
        }
    }

    fun removeUser(username: String) {
        viewModelScope.launch {
            repository.deleteUserByUsername(username)
        }
    }

    fun toggleUserEnabled(username: String, enabled: Boolean) {
        viewModelScope.launch {
            repository.setUserEnabled(username, enabled)
        }
    }

    fun clearError() {
        _uiState.update { it.copy(errorMessage = null) }
    }
}
