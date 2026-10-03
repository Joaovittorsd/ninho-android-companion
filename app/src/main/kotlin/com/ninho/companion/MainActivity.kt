package com.ninho.companion

import android.app.admin.DevicePolicyManager
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.ninho.companion.deviceadmin.NinhoDeviceAdminReceiver

/**
 * Spike-level status/onboarding screen for BOTH modes:
 *  - Modo A (Device Owner): just shows status, nothing to request — it's
 *    already fully active by the time this screen is reachable post-provisioning.
 *  - Modo B (Device Admin + Accessibility, manual install): shows one button
 *    per special permission the parent has to grant manually, since Android
 *    doesn't allow any of these to be requested in a single flow.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var dpm: DevicePolicyManager
    private lateinit var adminComponent: ComponentName
    private lateinit var statusText: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        dpm = getSystemService(Context.DEVICE_POLICY_SERVICE) as DevicePolicyManager
        adminComponent = ComponentName(this, NinhoDeviceAdminReceiver::class.java)
        statusText = findViewById(R.id.statusText)

        findViewById<android.view.View>(R.id.btnRequestDeviceAdmin).setOnClickListener {
            requestDeviceAdmin()
        }
        findViewById<android.view.View>(R.id.btnRequestAccessibility).setOnClickListener {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }
        findViewById<android.view.View>(R.id.btnRequestOverlay).setOnClickListener {
            requestOverlayPermission()
        }
    }

    override fun onResume() {
        super.onResume()
        refreshStatus()
    }

    private fun requestDeviceAdmin() {
        val intent = Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN).apply {
            putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, adminComponent)
            putExtra(
                DevicePolicyManager.EXTRA_ADD_EXPLANATION,
                getString(R.string.device_admin_explanation),
            )
        }
        startActivity(intent)
    }

    private fun requestOverlayPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && !Settings.canDrawOverlays(this)) {
            startActivity(
                Intent(
                    Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:$packageName"),
                )
            )
        }
    }

    private fun refreshStatus() {
        val isDeviceOwner = dpm.isDeviceOwnerApp(packageName)
        val isAdminActive = dpm.isAdminActive(adminComponent)
        val overlayGranted = Build.VERSION.SDK_INT < Build.VERSION_CODES.M || Settings.canDrawOverlays(this)

        val mode = if (isDeviceOwner) "Modo A (Device Owner)" else "Modo B (Device Admin + Accessibility)"

        statusText.text = getString(
            R.string.status_summary,
            mode,
            boolLabel(isDeviceOwner || isAdminActive),
            boolLabel(overlayGranted),
        )
    }

    private fun boolLabel(value: Boolean): String =
        getString(if (value) R.string.status_yes else R.string.status_no)
}
