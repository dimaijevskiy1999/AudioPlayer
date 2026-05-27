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
