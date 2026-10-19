package com.nexus.launcher

import android.annotation.SuppressLint
import android.app.Activity
import android.os.Bundle
import android.webkit.JavascriptInterface
import android.webkit.WebView

/**
 * Nexus Launcher v0.1 — hosts the Nexus OS prototype (assets/nexus_os.html,
 * the v0.8 build) in a WebView and exposes a native bridge:
 *  - JS -> native: NexusBridge (module toggles, heartbeat) per BLE_PROTOCOL.md
 *  - native -> JS: onDrumAngle(deg) pushes AS5600 telemetry into the OS UI
 * BLE GATT client: NexusBleClient.kt (v1.3) — scanner, GATT, protocol parsing,
 * 10 s heartbeat. Bridge calls below route into it.
 * NOT COMPILED in the design environment (no Android SDK) — builds in
 * Android Studio; see ../README.md.
 */
class MainActivity : Activity() {

    private lateinit var web: WebView

    private lateinit var ble: NexusBleClient

    inner class NexusBridge {
        @JavascriptInterface
        fun setModulePower(moduleId: Int, on: Boolean) = ble.setModulePower(moduleId, on)
        @JavascriptInterface
        fun setBrightnessCap(pct: Int) = ble.setBrightnessCap(pct)
        @JavascriptInterface
        fun setDisplayPower(on: Boolean) = ble.setDisplayPower(on)
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        web = WebView(this)
        web.settings.javaScriptEnabled = true
        web.addJavascriptInterface(NexusBridge(), "NexusBridge")
        web.loadUrl("file:///android_asset/nexus_os.html")
        setContentView(web)
        ble = NexusBleClient(this, onDrumAngle = { deg -> pushDrumAngle(deg) }, onState = { })
        // Runtime permissions for BLUETOOTH_SCAN/CONNECT are requested by the
        // launcher's permission flow before this call in the production build.
        ble.connect()
    }

    /** Push a drum-angle reading (degrees, 0–220) into the OS UI. */
    fun pushDrumAngle(deg: Float) {
        val u = (deg / 220f * 100).toInt().coerceIn(0, 100)
        web.evaluateJavascript(
            "(()=>{const s=document.getElementById('u');if(s){s.value=$u;s.dispatchEvent(new Event('input'));}})()", null
        )
    }
}
