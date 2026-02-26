package com.tiktokdownloader

import com.tiktokdownloader.data.local.entity.MonitoredUserEntity
import com.tiktokdownloader.data.local.entity.SettingEntity
import com.tiktokdownloader.data.local.entity.VideoEntity
import com.tiktokdownloader.domain.model.AppSettings
import com.tiktokdownloader.domain.model.MonitoredUser
import com.tiktokdownloader.domain.model.Video
import org.junit.Assert.*
import org.junit.Test

class EntityTest {

    @Test
    fun videoEntity_defaultValues() {
        val video = VideoEntity(id = "test123")
        assertEquals("test123", video.id)
        assertEquals("", video.url)
        assertEquals("", video.title)
        assertEquals("", video.author)
        assertEquals("downloaded", video.status)
        assertEquals(0L, video.likes)
        assertEquals(0L, video.views)
    }

    @Test
    fun monitoredUserEntity_defaultValues() {
        val user = MonitoredUserEntity(username = "testuser")
        assertEquals("testuser", user.username)
        assertTrue(user.enabled)
        assertEquals(0, user.totalVideos)
        assertEquals("", user.lastCheck)
    }

    @Test
    fun settingEntity_creation() {
        val setting = SettingEntity(key = "interval", value = "30")
        assertEquals("interval", setting.key)
        assertEquals("30", setting.value)
    }

    @Test
    fun domainModel_video() {
        val video = Video(
            id = "v1",
            title = "Test",
            author = "user1",
            likes = 1000,
            views = 5000
        )
        assertEquals("v1", video.id)
        assertEquals("Test", video.title)
        assertEquals("user1", video.author)
        assertEquals(1000L, video.likes)
        assertEquals(5000L, video.views)
    }

    @Test
    fun domainModel_monitoredUser() {
        val user = MonitoredUser(username = "tiktokuser", enabled = false)
        assertEquals("tiktokuser", user.username)
        assertFalse(user.enabled)
    }

    @Test
    fun domainModel_appSettings_defaults() {
        val settings = AppSettings()
        assertEquals(30, settings.checkIntervalMinutes)
        assertEquals(5, settings.maxVideosPerCheck)
        assertTrue(settings.notificationsEnabled)
        assertEquals("best", settings.videoQuality)
        assertTrue(settings.withAudio)
        assertTrue(settings.geoBypass)
        assertFalse(settings.disclaimerAccepted)
    }

    @Test
    fun videoEntity_withAllFields() {
        val video = VideoEntity(
            id = "abc123",
            url = "https://tiktok.com/video/abc123",
            title = "Cool Video",
            author = "creator",
            uploadDate = "2024-01-01",
            uploadTimestamp = 1704067200L,
            downloadDate = "2024-01-02 10:00:00",
            filePath = "/storage/tiktok/video.mp4",
            likes = 50000,
            views = 1000000,
            status = "downloaded"
        )
        assertEquals("abc123", video.id)
        assertEquals("https://tiktok.com/video/abc123", video.url)
        assertEquals("Cool Video", video.title)
        assertEquals("creator", video.author)
        assertEquals(1704067200L, video.uploadTimestamp)
        assertEquals("/storage/tiktok/video.mp4", video.filePath)
        assertEquals(50000L, video.likes)
        assertEquals(1000000L, video.views)
    }

    @Test
    fun monitoredUserEntity_toggleEnabled() {
        val user = MonitoredUserEntity(username = "user1", enabled = true)
        val disabled = user.copy(enabled = false)
        assertTrue(user.enabled)
        assertFalse(disabled.enabled)
        assertEquals(user.username, disabled.username)
    }
}
