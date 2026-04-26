package com.pala.app.service

import android.app.Service
import android.content.Intent
import android.os.IBinder

class StepTrackingService : Service() {
    override fun onBind(intent: Intent?): IBinder? = null
}
