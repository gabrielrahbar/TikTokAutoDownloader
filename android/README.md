# TikTok Auto Downloader - Android App

Android version of the TikTok Auto Downloader, built with modern Android development practices.

## Features

- **User Monitoring**: Add, remove, pause/resume TikTok users to monitor
- **Background Downloads**: Automatic video checking via WorkManager
- **Video Gallery**: Browse downloaded videos with thumbnails, likes, and views
- **Video Sharing**: Share downloaded videos with other apps
- **Settings**: Configure check intervals, notifications, quality, geo-bypass
- **Notifications**: Get notified when new videos are downloaded
- **Legal Compliance**: Copyright disclaimer on first launch
- **Material Design 3**: Modern UI with dynamic color support

## Tech Stack

| Technology | Purpose |
|-----------|---------|
| **Kotlin** | Primary language |
| **Jetpack Compose** | Declarative UI framework |
| **Material Design 3** | UI components and theming |
| **Room** | Local SQLite database |
| **WorkManager** | Background periodic tasks |
| **Retrofit + OkHttp** | Network requests |
| **Coil** | Image/thumbnail loading |
| **ExoPlayer (Media3)** | Video playback |
| **DataStore** | Preferences storage |
| **Navigation Compose** | Screen navigation |

## Architecture

The app follows **MVVM (Model-View-ViewModel)** architecture with clean separation:

```
com.tiktokdownloader/
├── data/                    # Data layer
│   ├── local/              # Room database
│   │   ├── dao/            # Data Access Objects
│   │   ├── database/       # Database configuration
│   │   └── entity/         # Database entities
│   ├── remote/             # Retrofit API service
│   └── repository/         # Repository pattern
├── domain/                  # Domain layer
│   └── model/              # Domain models
├── notification/            # Notification management
├── ui/                      # Presentation layer
│   ├── components/         # Reusable composables
│   ├── navigation/         # Navigation graph
│   ├── screens/            # Feature screens
│   │   ├── disclaimer/     # Legal disclaimer
│   │   ├── gallery/        # Video gallery
│   │   ├── settings/       # App settings
│   │   └── users/          # User management
│   ├── theme/              # Material 3 theme
│   └── viewmodel/          # ViewModels
└── worker/                  # WorkManager workers
```

## Database Schema

Mirrors the Python application's SQLite schema:

| Table | Description |
|-------|-------------|
| `videos` | Downloaded video metadata (id, url, title, author, likes, views, file_path) |
| `monitored_users` | Tracked TikTok users (username, last_check, total_videos, enabled) |
| `settings` | Key-value app settings |

## Build Instructions

### Prerequisites

- **Android Studio** Hedgehog (2023.1.1) or newer
- **JDK 17** or newer
- **Android SDK** with API level 34

### Steps

1. Open Android Studio
2. Select **File → Open** and navigate to the `android/` directory
3. Wait for Gradle sync to complete
4. Connect an Android device or start an emulator (API 26+)
5. Click **Run** (▶️) or use `Shift+F10`

### Command Line Build

```bash
cd android/
./gradlew assembleDebug      # Debug APK
./gradlew assembleRelease    # Release APK (requires signing config)
./gradlew test               # Run unit tests
./gradlew connectedCheck     # Run instrumented tests
```

The debug APK will be at: `app/build/outputs/apk/debug/app-debug.apk`

## Permissions

| Permission | Reason |
|-----------|--------|
| `INTERNET` | Download videos from TikTok |
| `POST_NOTIFICATIONS` | Notify about new downloads |
| `READ_MEDIA_VIDEO` | Access downloaded videos (Android 13+) |
| `FOREGROUND_SERVICE` | Background download service |

## Play Store Compliance

- ✅ Minimal permissions
- ✅ Scoped Storage support (Android 11+)
- ✅ Copyright disclaimer on first launch
- ✅ "Public content only" warnings
- ✅ Regional restrictions disclaimer
- ✅ Privacy-first design (no data collection)
- ✅ ProGuard/R8 obfuscation enabled for release builds

## Legal Notice

This app downloads **publicly available** TikTok content only. All downloaded content remains the intellectual property of the original creators. Users are responsible for compliance with local laws and TikTok's Terms of Service.
