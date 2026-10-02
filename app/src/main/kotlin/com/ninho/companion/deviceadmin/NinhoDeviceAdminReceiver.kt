package com.ninho.companion.deviceadmin

import android.app.admin.DeviceAdminReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

/**
 * Minimal receiver for validating QR-code Device Owner provisioning end-to-end
 * (see "The Assignment" in docs/android/DESIGN-ninho-android-companion.md).
 * No business logic yet — the restriction/consent/revocation flows land here
 * once the provisioning spike is confirmed on a real device.
 */
class NinhoDeviceAdminReceiver : DeviceAdminReceiver() {

    override fun onEnabled(context: Context, intent: Intent) {
        super.onEnabled(context, intent)
        Log.i(TAG, "Device admin enabled")
    }

    override fun onProfileProvisioningComplete(context: Context, intent: Intent) {
        super.onProfileProvisioningComplete(context, intent)
        Log.i(TAG, "Device Owner provisioning complete")
    }

    override fun onDisabled(context: Context, intent: Intent) {
        super.onDisabled(context, intent)
        Log.i(TAG, "Device admin disabled")
    }

    companion object {
        private const val TAG = "NinhoDeviceAdmin"
    }
}
