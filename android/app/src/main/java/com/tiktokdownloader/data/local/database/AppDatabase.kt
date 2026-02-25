package com.tiktokdownloader.data.local.database

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import com.tiktokdownloader.data.local.dao.MonitoredUserDao
import com.tiktokdownloader.data.local.dao.SettingDao
import com.tiktokdownloader.data.local.dao.VideoDao
import com.tiktokdownloader.data.local.entity.MonitoredUserEntity
import com.tiktokdownloader.data.local.entity.SettingEntity
import com.tiktokdownloader.data.local.entity.VideoEntity

@Database(
    entities = [
        VideoEntity::class,
        MonitoredUserEntity::class,
        SettingEntity::class
    ],
    version = 1,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun videoDao(): VideoDao
    abstract fun monitoredUserDao(): MonitoredUserDao
    abstract fun settingDao(): SettingDao

    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getInstance(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "tiktok_monitor.db"
                ).build()
                INSTANCE = instance
                instance
            }
        }
    }
}
