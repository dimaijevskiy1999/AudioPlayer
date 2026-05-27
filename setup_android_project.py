#!/usr/bin/env python3
"""
Запусти этот скрипт в любой папке:
    python setup_android_project.py

Будет создан готовый Android-проект AudioPlayer.
Затем залей папку на GitHub — Actions сам соберёт APK.
"""

import os

# ── helpers ──────────────────────────────────────────────────────────────────

def write(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.lstrip("\n"))
    print(f"  ✓  {path}")

ROOT = "AudioPlayer"

# ── Gradle / project config ───────────────────────────────────────────────────

write(f"{ROOT}/settings.gradle.kts", """
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "AudioPlayer"
include(":app")
""")

write(f"{ROOT}/build.gradle.kts", """
plugins {
    id("com.android.application")     version "8.7.3" apply false
    id("org.jetbrains.kotlin.android") version "2.0.21" apply false
    id("org.jetbrains.kotlin.plugin.compose") version "2.0.21" apply false
}
""")

write(f"{ROOT}/gradle.properties", """
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
kotlin.code.style=official
android.nonTransitiveRClass=true
""")

write(f"{ROOT}/app/build.gradle.kts", """
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace  = "com.player"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.player"
        minSdk        = 24
        targetSdk     = 35
        versionCode   = 1
        versionName   = "1.0"
    }

    buildFeatures { compose = true }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    kotlinOptions { jvmTarget = "11" }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.12.01")
    implementation(composeBom)
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.activity:activity-compose:1.9.3")

    // Media3
    implementation("androidx.media3:media3-exoplayer:1.5.0")
    implementation("androidx.media3:media3-session:1.5.0")

    // ViewModel
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.7")

    // Guava (ListenableFuture)
    implementation("com.google.guava:guava:33.3.1-android")
}
""")

# ── Manifest ──────────────────────────────────────────────────────────────────

write(f"{ROOT}/app/src/main/AndroidManifest.xml", """
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.READ_MEDIA_AUDIO" />
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
""")

# ── Kotlin source files ───────────────────────────────────────────────────────

SRC = f"{ROOT}/app/src/main/java/com/player"

write(f"{SRC}/service/AudioPlayerService.kt", """
package com.player.service

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

    override fun onGetSession(controllerInfo: MediaSession.ControllerInfo): MediaSession? =
        mediaSession

    override fun onDestroy() {
        mediaSession?.run {
            player.release()
            release()
            mediaSession = null
        }
        super.onDestroy()
    }
}
""")

write(f"{SRC}/data/AudioRepository.kt", """
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
            val idColumn    = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media._ID)
            val titleColumn = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media.TITLE)
            while (cursor.moveToNext()) {
                val id  = cursor.getLong(idColumn)
                val uri = ContentUris.withAppendedId(
                    MediaStore.Audio.Media.EXTERNAL_CONTENT_URI, id
                )
                tracks.add(MediaItem.fromUri(uri))
            }
        }
        return tracks
    }
}
""")

write(f"{SRC}/ui/PlayerScreen.kt", """
package com.player.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

val BluePrimary     = Color(0xFF0056B3)
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
""")

write(f"{SRC}/viewmodel/PlayerViewModel.kt", """
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
            if (it.isPlaying) { it.pause(); _isPlaying.value = false }
            else               { it.play();  _isPlaying.value = true  }
        }
    }

    override fun onCleared() {
        super.onCleared()
        controller?.release()
    }
}
""")

write(f"{SRC}/MainActivity.kt", """
package com.player

import android.content.ComponentName
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.media3.session.MediaController
import androidx.media3.session.SessionToken
import com.google.common.util.concurrent.ListenableFuture
import com.player.service.AudioPlayerService
import com.player.ui.PlayerScreen
import com.player.viewmodel.PlayerViewModel

class MainActivity : ComponentActivity() {
    private var controllerFuture: ListenableFuture<MediaController>? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val sessionToken = SessionToken(
            this, ComponentName(this, AudioPlayerService::class.java)
        )
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
""")

# ── GitHub Actions workflow ────────────────────────────────────────────────────

write(f"{ROOT}/.github/workflows/build.yml", """
name: Build APK

on:
  push:
    branches: [ main ]
  workflow_dispatch:       # кнопка "Run workflow" в браузере

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Java 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'

      - name: Set up Gradle 8.10.2
        uses: gradle/actions/setup-gradle@v4
        with:
          gradle-version: "8.10.2"

      - name: Build debug APK
        run: gradle assembleDebug
        working-directory: .

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: AudioPlayer-debug
          path: app/build/outputs/apk/debug/app-debug.apk
          retention-days: 7
""")

# ── .gitignore ────────────────────────────────────────────────────────────────

write(f"{ROOT}/.gitignore", """
*.iml
.gradle
/local.properties
/.idea
.DS_Store
/build
/captures
.externalNativeBuild
.cxx
local.properties
""")

# ── Done ──────────────────────────────────────────────────────────────────────

print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Проект создан в папке: ./{ROOT}/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Следующие шаги (всё через браузер / Git):

  1. Зайди на github.com → New repository → AudioPlayer
     (Public, без README)

  2. В терминале / командной строке:
       cd {ROOT}
       git init
       git add .
       git commit -m "init"
       git branch -M main
       git remote add origin https://github.com/ТВО_ИМЯ/AudioPlayer.git
       git push -u origin main

  3. GitHub Actions сам запустит сборку (~5-7 мин).
     Следи: вкладка Actions в репозитории.

  4. Когда статус ✓ — открой тот же Actions-запуск,
     внизу найди раздел Artifacts → AudioPlayer-debug
     → Download ZIP → внутри app-debug.apk

  5. Перекинь APK на телефон (Telegram себе /
     Google Drive) и установи.
""")
