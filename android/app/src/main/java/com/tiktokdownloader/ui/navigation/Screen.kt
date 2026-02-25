package com.tiktokdownloader.ui.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.People
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.VideoLibrary
import androidx.compose.ui.graphics.vector.ImageVector

sealed class Screen(val route: String, val title: String, val icon: ImageVector) {
    data object Users : Screen("users", "Users", Icons.Filled.People)
    data object Gallery : Screen("gallery", "Gallery", Icons.Filled.VideoLibrary)
    data object Settings : Screen("settings", "Settings", Icons.Filled.Settings)
    data object Disclaimer : Screen("disclaimer", "Disclaimer", Icons.Filled.Settings)

    companion object {
        val bottomNavItems = listOf(Users, Gallery, Settings)
    }
}
