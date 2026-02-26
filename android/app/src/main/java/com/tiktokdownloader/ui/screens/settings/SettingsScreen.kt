package com.tiktokdownloader.ui.screens.settings

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.tiktokdownloader.R
import com.tiktokdownloader.ui.viewmodel.SettingsViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(viewModel: SettingsViewModel) {
    val settings by viewModel.settings.collectAsState()
    val videoCount by viewModel.videoCount.collectAsState()
    val userCount by viewModel.userCount.collectAsState()

    var showClearConfirm by remember { mutableStateOf(false) }
    var showDisclaimerDialog by remember { mutableStateOf(false) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.nav_settings)) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer,
                    titleContentColor = MaterialTheme.colorScheme.onPrimaryContainer
                )
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
        ) {
            // Stats Card
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                )
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            text = userCount.toString(),
                            style = MaterialTheme.typography.headlineMedium,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onPrimaryContainer
                        )
                        Text(
                            text = "Users",
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onPrimaryContainer
                        )
                    }
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            text = videoCount.toString(),
                            style = MaterialTheme.typography.headlineMedium,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onPrimaryContainer
                        )
                        Text(
                            text = "Videos",
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onPrimaryContainer
                        )
                    }
                }
            }

            // Monitoring Section
            SettingsSectionHeader(
                icon = Icons.Filled.Schedule,
                title = stringResource(R.string.settings_monitoring)
            )

            SettingsSliderItem(
                title = stringResource(R.string.settings_check_interval),
                value = settings.checkIntervalMinutes.toFloat(),
                valueRange = 5f..120f,
                steps = 22,
                valueLabel = "${settings.checkIntervalMinutes} min",
                onValueChange = { viewModel.updateCheckInterval(it.toInt()) }
            )

            SettingsSliderItem(
                title = stringResource(R.string.settings_max_videos),
                value = settings.maxVideosPerCheck.toFloat(),
                valueRange = 1f..20f,
                steps = 18,
                valueLabel = settings.maxVideosPerCheck.toString(),
                onValueChange = { viewModel.updateMaxVideos(it.toInt()) }
            )

            HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp))

            // Notifications Section
            SettingsSectionHeader(
                icon = Icons.Filled.Notifications,
                title = stringResource(R.string.settings_notifications)
            )

            SettingsSwitchItem(
                title = stringResource(R.string.settings_enable_notifications),
                checked = settings.notificationsEnabled,
                onCheckedChange = { viewModel.updateNotifications(it) }
            )

            HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp))

            // Download Section
            SettingsSectionHeader(
                icon = Icons.Filled.Download,
                title = stringResource(R.string.settings_download)
            )

            SettingsSwitchItem(
                title = stringResource(R.string.settings_with_audio),
                checked = settings.withAudio,
                onCheckedChange = { viewModel.updateWithAudio(it) }
            )

            SettingsSwitchItem(
                title = stringResource(R.string.settings_geo_bypass),
                checked = settings.geoBypass,
                onCheckedChange = { viewModel.updateGeoBypass(it) }
            )

            HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp))

            // Storage Section
            SettingsSectionHeader(
                icon = Icons.Filled.Storage,
                title = stringResource(R.string.settings_storage)
            )

            SettingsClickItem(
                title = stringResource(R.string.settings_clear_database),
                subtitle = "$videoCount videos, $userCount users",
                onClick = { showClearConfirm = true }
            )

            HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp))

            // About Section
            SettingsSectionHeader(
                icon = Icons.Filled.Info,
                title = stringResource(R.string.settings_about)
            )

            SettingsClickItem(
                title = stringResource(R.string.settings_version, "1.0.0"),
                subtitle = "TikTok Auto Downloader"
            )

            SettingsClickItem(
                title = stringResource(R.string.settings_disclaimer),
                subtitle = "Copyright & regional restrictions",
                onClick = { showDisclaimerDialog = true }
            )

            // Public content warning
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.tertiaryContainer
                )
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        Icons.Filled.Public,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.onTertiaryContainer
                    )
                    Spacer(modifier = Modifier.width(12.dp))
                    Text(
                        text = stringResource(R.string.public_content_warning),
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onTertiaryContainer
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))
        }
    }

    if (showClearConfirm) {
        AlertDialog(
            onDismissRequest = { showClearConfirm = false },
            icon = { Icon(Icons.Filled.Warning, contentDescription = null) },
            title = { Text("Clear Database") },
            text = { Text("This will delete all monitored users and video records. Downloaded files will not be deleted. Continue?") },
            confirmButton = {
                TextButton(onClick = {
                    showClearConfirm = false
                    viewModel.clearDatabase()
                }) {
                    Text("Clear", color = MaterialTheme.colorScheme.error)
                }
            },
            dismissButton = {
                TextButton(onClick = { showClearConfirm = false }) {
                    Text(stringResource(R.string.cancel))
                }
            }
        )
    }

    if (showDisclaimerDialog) {
        AlertDialog(
            onDismissRequest = { showDisclaimerDialog = false },
            icon = { Icon(Icons.Filled.Warning, contentDescription = null) },
            title = { Text(stringResource(R.string.disclaimer_title)) },
            text = { Text(stringResource(R.string.disclaimer_message)) },
            confirmButton = {
                TextButton(onClick = { showDisclaimerDialog = false }) {
                    Text(stringResource(R.string.ok))
                }
            }
        )
    }
}

@Composable
private fun SettingsSectionHeader(icon: ImageVector, title: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.primary,
            modifier = Modifier.size(20.dp)
        )
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = title,
            style = MaterialTheme.typography.titleSmall,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.primary
        )
    }
}

@Composable
private fun SettingsSwitchItem(
    title: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = title,
            style = MaterialTheme.typography.bodyLarge,
            modifier = Modifier.weight(1f)
        )
        Switch(checked = checked, onCheckedChange = onCheckedChange)
    }
}

@Composable
private fun SettingsSliderItem(
    title: String,
    value: Float,
    valueRange: ClosedFloatingPointRange<Float>,
    steps: Int,
    valueLabel: String,
    onValueChange: (Float) -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(text = title, style = MaterialTheme.typography.bodyLarge)
            Text(
                text = valueLabel,
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.primary
            )
        }
        Slider(
            value = value,
            onValueChange = onValueChange,
            valueRange = valueRange,
            steps = steps
        )
    }
}

@Composable
private fun SettingsClickItem(
    title: String,
    subtitle: String? = null,
    onClick: (() -> Unit)? = null
) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        onClick = onClick ?: {}
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 12.dp)
        ) {
            Text(text = title, style = MaterialTheme.typography.bodyLarge)
            subtitle?.let {
                Text(
                    text = it,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}
