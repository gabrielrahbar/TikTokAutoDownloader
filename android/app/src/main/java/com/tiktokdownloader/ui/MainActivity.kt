package com.tiktokdownloader.ui

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.core.content.ContextCompat
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.tiktokdownloader.data.local.database.AppDatabase
import com.tiktokdownloader.data.remote.RetrofitClient
import com.tiktokdownloader.data.repository.TikTokRepository
import com.tiktokdownloader.ui.navigation.AppNavHost
import com.tiktokdownloader.ui.navigation.Screen
import com.tiktokdownloader.ui.theme.TikTokDownloaderTheme
import com.tiktokdownloader.ui.viewmodel.GalleryViewModel
import com.tiktokdownloader.ui.viewmodel.SettingsViewModel
import com.tiktokdownloader.ui.viewmodel.UsersViewModel
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

class MainActivity : ComponentActivity() {

    // Runtime permission launcher for POST_NOTIFICATIONS (Android 13+)
    private val notificationPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { /* Permission result handled - notifications will work if granted */ }

    // Runtime permission launcher for storage (Android 13+)
    private val storagePermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { /* Storage permission result handled */ }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        // Request runtime permissions
        requestRequiredPermissions()

        // Check if disclaimer was accepted
        val db = AppDatabase.getInstance(this)
        val repository = TikTokRepository(
            db.videoDao(), db.monitoredUserDao(), db.settingDao(), RetrofitClient.apiService
        )

        val disclaimerAccepted = runBlocking {
            repository.getSettingValue("disclaimer_accepted") == "true"
        }

        setContent {
            TikTokDownloaderTheme {
                MainApp(disclaimerAccepted = disclaimerAccepted)
            }
        }
    }

    /**
     * Requests runtime permissions required by the app.
     * Android 13+ requires POST_NOTIFICATIONS at runtime.
     * Android 13+ requires READ_MEDIA_VIDEO for video access.
     */
    private fun requestRequiredPermissions() {
        // Notification permission (Android 13+/TIRAMISU)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(
                    this, Manifest.permission.POST_NOTIFICATIONS
                ) != PackageManager.PERMISSION_GRANTED
            ) {
                notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }

        // Storage permission (Android 13+)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(
                    this, Manifest.permission.READ_MEDIA_VIDEO
                ) != PackageManager.PERMISSION_GRANTED
            ) {
                storagePermissionLauncher.launch(Manifest.permission.READ_MEDIA_VIDEO)
            }
        }
    }
}

@Composable
fun MainApp(disclaimerAccepted: Boolean) {
    val navController = rememberNavController()
    val usersViewModel: UsersViewModel = viewModel()
    val galleryViewModel: GalleryViewModel = viewModel()
    val settingsViewModel: SettingsViewModel = viewModel()

    val startDestination = if (disclaimerAccepted) Screen.Users.route else Screen.Disclaimer.route
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route

    val showBottomBar = currentRoute in Screen.bottomNavItems.map { it.route }

    Scaffold(
        bottomBar = {
            if (showBottomBar) {
                NavigationBar {
                    Screen.bottomNavItems.forEach { screen ->
                        NavigationBarItem(
                            icon = { Icon(screen.icon, contentDescription = screen.title) },
                            label = { Text(screen.title) },
                            selected = currentRoute == screen.route,
                            onClick = {
                                if (currentRoute != screen.route) {
                                    navController.navigate(screen.route) {
                                        popUpTo(Screen.Users.route) { saveState = true }
                                        launchSingleTop = true
                                        restoreState = true
                                    }
                                }
                            }
                        )
                    }
                }
            }
        }
    ) { innerPadding ->
        AppNavHost(
            navController = navController,
            startDestination = startDestination,
            usersViewModel = usersViewModel,
            galleryViewModel = galleryViewModel,
            settingsViewModel = settingsViewModel,
            onDisclaimerAccepted = {
                kotlinx.coroutines.MainScope().launch {
                    val db = AppDatabase.getInstance(navController.context)
                    val repo = TikTokRepository(
                        db.videoDao(), db.monitoredUserDao(), db.settingDao(), RetrofitClient.apiService
                    )
                    repo.setSetting("disclaimer_accepted", "true")
                }
            },
            modifier = Modifier.padding(innerPadding)
        )
    }
}
