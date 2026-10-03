package com.ninho.companion.blocking

import android.content.Context
import android.graphics.Color
import android.graphics.PixelFormat
import android.os.Build
import android.view.Gravity
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.TextView
import com.ninho.companion.R

/**
 * Draws (or removes) a full-screen block overlay. Requires SYSTEM_ALERT_WINDOW,
 * granted manually by the parent via ACTION_MANAGE_OVERLAY_PERMISSION during
 * Modo B onboarding — see MainActivity.
 *
 * Spike-level only: no per-app configuration from the backend yet, just
 * proves the mechanism (detect foreground app via NinhoAccessibilityService,
 * show/hide this overlay) works before wiring it to a real block-list.
 */
object BlockOverlayController {
    private var overlayView: FrameLayout? = null

    fun show(context: Context, blockedPackageLabel: String) {
        if (overlayView != null) return
        if (!canDrawOverlays(context)) return

        val windowManager = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager

        val view = FrameLayout(context).apply {
            setBackgroundColor(Color.BLACK)
            addView(
                TextView(context).apply {
                    text = context.getString(R.string.block_overlay_message, blockedPackageLabel)
                    setTextColor(Color.WHITE)
                    textSize = 20f
                    gravity = Gravity.CENTER
                },
                FrameLayout.LayoutParams(
                    FrameLayout.LayoutParams.WRAP_CONTENT,
                    FrameLayout.LayoutParams.WRAP_CONTENT,
                    Gravity.CENTER,
                )
            )
        }

        val overlayType = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        } else {
            @Suppress("DEPRECATION")
            WindowManager.LayoutParams.TYPE_SYSTEM_ALERT
        }

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            overlayType,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.OPAQUE,
        )

        windowManager.addView(view, params)
        overlayView = view
    }

    fun hide(context: Context) {
        val view = overlayView ?: return
        val windowManager = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
        windowManager.removeView(view)
        overlayView = null
    }

    private fun canDrawOverlays(context: Context): Boolean =
        Build.VERSION.SDK_INT < Build.VERSION_CODES.M ||
            android.provider.Settings.canDrawOverlays(context)
}
