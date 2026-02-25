package com.tiktokdownloader.notification

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import com.tiktokdownloader.R

object NotificationHelper {

    private const val CHANNEL_ID = "tiktok_downloads"
    private const val CHANNEL_NAME = "Download Notifications"
    private const val MONITORING_CHANNEL_ID = "tiktok_monitoring"

    fun createNotificationChannels(context: Context) {
        val downloadChannel = NotificationChannel(
            CHANNEL_ID,
            CHANNEL_NAME,
            NotificationManager.IMPORTANCE_DEFAULT
        ).apply {
            description = context.getString(R.string.notification_channel_description)
        }

        val monitoringChannel = NotificationChannel(
            MONITORING_CHANNEL_ID,
            "Monitoring Service",
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = "Background monitoring notifications"
        }

        val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.createNotificationChannel(downloadChannel)
        manager.createNotificationChannel(monitoringChannel)
    }

    fun showNewVideoNotification(context: Context, username: String, videoTitle: String, notificationId: Int) {
        if (!hasNotificationPermission(context)) return

        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentTitle(context.getString(R.string.notification_new_video, username))
            .setContentText(videoTitle.ifBlank { "New video available" })
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setAutoCancel(true)
            .build()

        NotificationManagerCompat.from(context).notify(notificationId, notification)
    }

    fun showMonitoringNotification(context: Context, userCount: Int): NotificationCompat.Builder {
        return NotificationCompat.Builder(context, MONITORING_CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentTitle("TikTok Monitor")
            .setContentText(context.getString(R.string.notification_monitoring, userCount))
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
    }

    private fun hasNotificationPermission(context: Context): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.POST_NOTIFICATIONS
            ) == PackageManager.PERMISSION_GRANTED
        } else {
            true
        }
    }
}
