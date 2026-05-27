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
