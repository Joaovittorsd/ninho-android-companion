package com.ninho.companion.accessibility

import android.accessibilityservice.AccessibilityService
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import com.ninho.companion.blocking.BlockOverlayController

/**
 * Modo B only (see docs/android/DESIGN-ninho-android-companion.md). Detects
 * which app is in the foreground — nothing else. canRetrieveWindowContent is
 * off in accessibility_service_config.xml, so this cannot read screen text or
 * keystrokes; it only sees package-name window-state-changed events.
 *
 * Spike-level: BLOCKED_PACKAGES is hardcoded. Wiring this to a real,
 * backend-driven block-list (the `app_restrictions` table from the design
 * doc) is follow-up work, not covered by this file yet.
 */
class NinhoAccessibilityService : AccessibilityService() {

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        val packageName = event?.packageName?.toString() ?: return
        if (packageName == lastForegroundPackage) return
        lastForegroundPackage = packageName

        Log.i(TAG, "Foreground app changed: $packageName")

        if (packageName in BLOCKED_PACKAGES) {
            BlockOverlayController.show(this, packageName)
        } else {
            BlockOverlayController.hide(this)
        }
    }

    override fun onInterrupt() {
        Log.i(TAG, "Accessibility service interrupted")
    }

    companion object {
        private const val TAG = "NinhoAccessibility"
        private var lastForegroundPackage: String? = null

        // Spike placeholder — replace with the backend-driven block-list.
        private val BLOCKED_PACKAGES = setOf(
            "com.example.placeholder.blocked.app",
        )
    }
}
