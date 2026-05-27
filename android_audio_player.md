# Android Audio Player — Полный код проекта

## Структура проекта

```
app/
├── src/main/
│   ├── java/com/player/
│   │   ├── MainActivity.kt
│   │   ├── service/
│   │   │   └── AudioPlayerService.kt
│   │   ├── data/
│   │   │   └── AudioRepository.kt
│   │   ├── ui/
│   │   │   └── PlayerScreen.kt
│   │   └── viewmodel/
│   │       └── PlayerViewModel.kt
│   └── AndroidManifest.xml
└── build.gradle.kts (app)
build.gradle.kts (project)
```

---

## 1. `app/build.gradle.kts`

```kotlin
plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
}

android {
    namespace = "com.player"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.player"
        minSdk = 24
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"
    }

    buildFeatures {
        compose = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }

    kotlinOptions {
        jvmTarget = "11"
    }
}

dependencies {
    // Compose BOM
    val composeBom = platform("androidx.compose:compose-bom:2024.12.01")
    implementation(composeBom)
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.activity:activity-compose:1.9.3")

    // Media3
    implementation("androidx.media3:media3-exoplayer:1.5.0")
    implementation("androidx.media3:media3-session:1.5.0")

    // Lifecycle / ViewModel
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.7")

    // Guava (для ListenableFuture)
    implementation("com.google.guava:guava:33.3.1-android")
}
```

---

## 2. `app/src/main/AndroidManifest.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <!-- Разрешения -->
    <uses-permission android:name="android.permission.READ_MEDIA_AUDIO" />
    <!-- Для Android 9 и ниже: -->
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"
        android:maxSdkVersion="32" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK" />

    <application
        android:allowBackup="true"
        android:label="AudioPlayer"
        android:theme="@style/Theme.AppCompat.Light.NoActionBar">

        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <!-- AudioPlayerService -->
        <service
            android:name=".service.AudioPlayerService"
            android:foregroundServiceType="mediaPlayback"
            android:exported="true">
            <intent-filter>
                <action android:name="androidx.media3.session.MediaSessionService" />
            </intent-filter>
        </service>

    </application>
</manifest>
```

---

## 3. `AudioPlayerService.kt`

```kotlin
// File: app/src/main/java/com/player/service/AudioPlayerService.kt
package com.player.service

import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.session.MediaSession
import androidx.media3.session.MediaSessionService

class AudioPlayerService : MediaSessionService() {
    private var player: ExoPlayer? = null
    private var mediaSession: MediaSession? = null

    override fun onCreate() {
        super.onCreate()
        player = ExoPlayer.Builder(this).build()
        mediaSession = MediaSession.Builder(this, player!!).build()
    }

    override fun onGetSession(controllerInfo: MediaSession.ControllerInfo): MediaSession? = mediaSession

    override fun onDestroy() {
        mediaSession?.run {
            player.release()
            release()
            mediaSession = null
        }
        super.onDestroy()
    }
}
```

---

## 4. `AudioRepository.kt`

```kotlin
// File: app/src/main/java/com/player/data/AudioRepository.kt
package com.player.data

import android.content.ContentUris
import android.content.Context
import android.provider.MediaStore
import androidx.media3.common.MediaItem

data class AudioTrack(val id: Long, val title: String, val uri: String)

class AudioRepository(private val context: Context) {
    fun fetchAudioTracks(): List<MediaItem> {
        val tracks = mutableListOf<MediaItem>()
        val projection = arrayOf(
            MediaStore.Audio.Media._ID,
            MediaStore.Audio.Media.TITLE
        )

        context.contentResolver.query(
            MediaStore.Audio.Media.EXTERNAL_CONTENT_URI,
            projection, null, null, null
        )?.use { cursor ->
            val idColumn = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media._ID)
            val titleColumn = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media.TITLE)
            while (cursor.moveToNext()) {
                val id = cursor.getLong(idColumn)
                val title = cursor.getString(titleColumn)
                val uri = ContentUris.withAppendedId(
                    MediaStore.Audio.Media.EXTERNAL_CONTENT_URI, id
                )
                tracks.add(MediaItem.fromUri(uri))
            }
        }
        return tracks
    }
}
```

---

## 5. `PlayerScreen.kt`

```kotlin
// File: app/src/main/java/com/player/ui/PlayerScreen.kt
package com.player.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

val BluePrimary = Color(0xFF0056B3)
val WhiteBackground = Color(0xFFF8F9FA)

@Composable
fun PlayerScreen(onPlayPause: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(WhiteBackground)
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            "Музыкальный плеер",
            color = BluePrimary,
            style = MaterialTheme.typography.headlineMedium
        )

        Spacer(modifier = Modifier.height(48.dp))

        Button(
            onClick = onPlayPause,
            colors = ButtonDefaults.buttonColors(containerColor = BluePrimary)
        ) {
            Text("Играть / Пауза", color = Color.White)
        }
    }
}
```

---

## 6. `PlayerViewModel.kt`

```kotlin
// File: app/src/main/java/com/player/viewmodel/PlayerViewModel.kt
package com.player.viewmodel

import androidx.lifecycle.ViewModel
import androidx.media3.session.MediaController
import com.google.common.util.concurrent.ListenableFuture
import com.google.common.util.concurrent.MoreExecutors
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

class PlayerViewModel(controllerFuture: ListenableFuture<MediaController>) : ViewModel() {
    private var controller: MediaController? = null
    private val _isPlaying = MutableStateFlow(false)
    val isPlaying = _isPlaying.asStateFlow()

    init {
        controllerFuture.addListener({
            controller = controllerFuture.get()
        }, MoreExecutors.directExecutor())
    }

    fun togglePlayback() {
        controller?.let {
            if (it.isPlaying) {
                it.pause()
                _isPlaying.value = false
            } else {
                it.play()
                _isPlaying.value = true
            }
        }
    }

    override fun onCleared() {
        super.onCleared()
        controller?.release()
    }
}
```

---

## 7. `MainActivity.kt`

```kotlin
// File: app/src/main/java/com/player/MainActivity.kt
package com.player

import android.content.ComponentName
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.media3.session.MediaController
import androidx.media3.session.SessionToken
import com.google.common.util.concurrent.ListenableFuture
import com.google.common.util.concurrent.MoreExecutors
import com.player.service.AudioPlayerService
import com.player.ui.PlayerScreen
import com.player.viewmodel.PlayerViewModel

class MainActivity : ComponentActivity() {
    private var controllerFuture: ListenableFuture<MediaController>? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val sessionToken = SessionToken(this, ComponentName(this, AudioPlayerService::class.java))
        controllerFuture = MediaController.Builder(this, sessionToken).buildAsync()

        setContent {
            val viewModel = PlayerViewModel(controllerFuture!!)
            PlayerScreen(onPlayPause = { viewModel.togglePlayback() })
        }
    }

    override fun onStop() {
        super.onStop()
        controllerFuture?.let { MediaController.releaseFuture(it) }
    }
}
```

---

## ⚠️ Найденные баги в оригинальном коде

| Файл | Проблема | Исправление |
|------|----------|-------------|
| `MainActivity.kt` | `ListenableFuture` не был импортирован | Добавлен импорт `com.google.common.util.concurrent.ListenableFuture` |
| `AndroidManifest.xml` | Отсутствовали разрешения `READ_MEDIA_AUDIO` и `FOREGROUND_SERVICE_MEDIA_PLAYBACK` | Добавлены в манифест |
| `PlayerViewModel.kt` | Неиспользуемый импорт `viewModelScope` | Убран лишний импорт |
| Весь проект | Отсутствовал `build.gradle.kts` с зависимостями Media3 | Добавлен полный файл зависимостей |
