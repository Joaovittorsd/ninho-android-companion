package com.ninho.companion

import android.app.admin.DevicePolicyManager
import android.content.Context
import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

/**
 * Just enough UI to confirm, by eye, that QR provisioning made this app
 * Device Owner on a real device. Nothing else lives here yet.
 */
class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val dpm = getSystemService(Context.DEVICE_POLICY_SERVICE) as DevicePolicyManager
        val isOwner = dpm.isDeviceOwnerApp(packageName)

        findViewById<TextView>(R.id.statusText).text =
            if (isOwner) getString(R.string.status_is_device_owner)
            else getString(R.string.status_not_device_owner)
    }
}
