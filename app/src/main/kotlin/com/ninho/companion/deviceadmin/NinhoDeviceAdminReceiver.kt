package com.ninho.companion.deviceadmin

import android.app.admin.DeviceAdminReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import com.ninho.companion.R

/**
 * Shared by both modes (see "Detecção do modo" in the design doc):
 *  - Modo A: activated via QR provisioning -> onProfileProvisioningComplete()
 *    fires, dpm.isDeviceOwnerApp() is true, full Device Owner policy set available.
 *  - Modo B: activated via ACTION_ADD_DEVICE_ADMIN (parent accepts a system
 *    dialog manually) -> only onEnabled() fires, classic Device Admin level
 *    only. onDisableRequested() below is the one Modo B tamper deterrent this
 *    API level provides: the user must dismiss this warning before Android
 *    lets them deactivate the admin (and thus uninstall the app).
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

    override fun onDisableRequested(context: Context, intent: Intent): CharSequence {
        return context.getString(R.string.device_admin_disable_warning)
    }

    override fun onDisabled(context: Context, intent: Intent) {
        super.onDisabled(context, intent)
        Log.i(TAG, "Device admin disabled")
    }

    companion object {
        private const val TAG = "NinhoDeviceAdmin"
    }
}
