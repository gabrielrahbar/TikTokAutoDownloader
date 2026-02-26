package com.tiktokdownloader

import android.app.Application
import com.tiktokdownloader.notification.NotificationHelper
import com.tiktokdownloader.worker.VideoCheckWorker

class TikTokDownloaderApp : Application() {

    override fun onCreate() {
        super.onCreate()

        // Create notification channels
        NotificationHelper.createNotificationChannels(this)

        // Schedule background monitoring
        VideoCheckWorker.schedule(this, intervalMinutes = 30)
    }
}
