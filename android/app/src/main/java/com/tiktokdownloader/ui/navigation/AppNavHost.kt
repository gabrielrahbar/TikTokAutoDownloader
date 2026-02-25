package com.tiktokdownloader.ui.navigation

import androidx.compose.runtime.Composable
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.tiktokdownloader.ui.screens.disclaimer.DisclaimerScreen
import com.tiktokdownloader.ui.screens.gallery.GalleryScreen
import com.tiktokdownloader.ui.screens.settings.SettingsScreen
import com.tiktokdownloader.ui.screens.users.UsersScreen
import com.tiktokdownloader.ui.viewmodel.GalleryViewModel
import com.tiktokdownloader.ui.viewmodel.SettingsViewModel
import com.tiktokdownloader.ui.viewmodel.UsersViewModel

@Composable
fun AppNavHost(
    navController: NavHostController,
    startDestination: String,
    usersViewModel: UsersViewModel,
    galleryViewModel: GalleryViewModel,
    settingsViewModel: SettingsViewModel,
    onDisclaimerAccepted: () -> Unit
) {
    NavHost(navController = navController, startDestination = startDestination) {
        composable(Screen.Disclaimer.route) {
            DisclaimerScreen(
                onAccepted = {
                    onDisclaimerAccepted()
                    navController.navigate(Screen.Users.route) {
                        popUpTo(Screen.Disclaimer.route) { inclusive = true }
                    }
                },
                onDeclined = { /* Close app handled in Activity */ }
            )
        }

        composable(Screen.Users.route) {
            UsersScreen(viewModel = usersViewModel)
        }

        composable(Screen.Gallery.route) {
            GalleryScreen(viewModel = galleryViewModel)
        }

        composable(Screen.Settings.route) {
            SettingsScreen(viewModel = settingsViewModel)
        }
    }
}
