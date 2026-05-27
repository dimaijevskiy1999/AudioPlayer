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
