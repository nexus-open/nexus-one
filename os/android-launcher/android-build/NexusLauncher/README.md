# Nexus Launcher (Android skeleton, v0.1)

Hosts Nexus OS (the v0.8 HTML prototype, in `app/src/main/assets/`) as an
Android launcher activity, with a native bridge seam for the frozen BLE
protocol (`../../protocol/BLE_PROTOCOL.md`).

**Status: NOT COMPILED.** The design environment has no Android SDK. To build:
open this folder in Android Studio, let it sync (AGP 8.5.2, compileSdk 34),
Run on any Android 8+ phone. WebView part works immediately; BLE calls are
marked `TODO(BLE)` in `MainActivity.kt` — the GATT client is the next task.

The manifest registers HOME category so it *can* be set as default launcher;
remove that category if you only want a normal app during development.
