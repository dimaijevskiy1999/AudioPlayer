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
