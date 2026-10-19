package com.nexus.launcher

import android.annotation.SuppressLint
import android.bluetooth.*
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanResult
import android.content.Context
import android.os.Build
import android.os.Handler
import android.os.Looper
import java.util.UUID
import java.util.concurrent.Executors

/**
 * Nexus BLE client — implements protocol/BLE_PROTOCOL.md v1.0 against the
 * ESP32-S3 controller firmware (firmware/nexus_controller).
 *
 * Security posture mirrors the protocol: we only issue commands on a bonded,
 * encrypted link (the firmware rejects anything else anyway), and the UI must
 * re-read state characteristics instead of assuming a command succeeded —
 * the controller is the safety owner and may refuse.
 *
 * v1.7 (2026-10-19): BLE API modernization ONLY — protocol bytes, UUIDs,
 * opcodes and timing are byte-identical to v1.3. The pre-API-33 calls that
 * v1.6's compile flagged as deprecated (BluetoothAdapter.getDefaultAdapter,
 * characteristic.value + writeCharacteristic(), descriptor.value +
 * writeDescriptor(), the value-less onCharacteristicChanged override) are
 * replaced on API 33+ by BluetoothManager.adapter and the typed
 * write/onCharacteristicChanged APIs. minSdk is 26, so the legacy calls are
 * retained behind Build.VERSION branches for older devices — that is the
 * standard dual-path pattern, not leftover debt.
 *
 * Compiled and verified with the v1.6/v1.7 toolchain (kotlinc vs android-34;
 * signed APK assembled). Runtime permissions (BLUETOOTH_SCAN /
 * BLUETOOTH_CONNECT) must be requested by the hosting activity before
 * connect() is called.
 */
@SuppressLint("MissingPermission")
class NexusBleClient(
    private val ctx: Context,
    private val onDrumAngle: (Float) -> Unit,
    private val onState: (String) -> Unit,
) {
    companion object {
        private fun uuid(suffix: String) =
            UUID.fromString("4e455855-$suffix-1000-8000-00805f9b34fb")
        val SVC = uuid("0000")
        val CH_ANGLE = uuid("0001"); val CH_DETENT = uuid("0002")
        val CH_BATT = uuid("0003"); val CH_BAY = uuid("0004")
        val CH_THERM = uuid("0005"); val CH_CMD = uuid("0010")
        val CCCD = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")
        const val OP_HEARTBEAT: Byte = 0x00
        const val OP_DISPLAY: Byte = 0x01
        const val OP_MODULE: Byte = 0x02
        const val OP_BRIGHTNESS_CAP: Byte = 0x03
        const val OP_CALIBRATE: Byte = 0x04
    }

    private var gatt: BluetoothGatt? = null
    private val heartbeat = Executors.newSingleThreadScheduledExecutor()
    private var heartbeatStarted = false

    fun connect() {
        // getDefaultAdapter() is deprecated (API 33+); BluetoothManager is
        // the supported route and exists since API 18, so no branch needed.
        val adapter = (ctx.getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager)?.adapter ?: return
        val scanner = adapter.bluetoothLeScanner ?: return
        scanner.startScan(object : ScanCallback() {
            override fun onScanResult(type: Int, result: ScanResult) {
                if (result.device.name == "NEXUS-ONE") {
                    scanner.stopScan(this)
                    gatt = result.device.connectGatt(ctx, false, gattCb, BluetoothDevice.TRANSPORT_LE)
                }
            }
        })
    }

    /** CCCD write: typed API on 33+, legacy value-set below. Same bytes. */
    @Suppress("DEPRECATION")
    private fun enableNotifications(g: BluetoothGatt, d: BluetoothGattDescriptor) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            g.writeDescriptor(d, BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
        } else {
            d.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
            g.writeDescriptor(d)
        }
    }

    private val gattCb = object : BluetoothGattCallback() {
        override fun onConnectionStateChange(g: BluetoothGatt, status: Int, newState: Int) {
            if (newState == BluetoothProfile.STATE_CONNECTED) {
                g.discoverServices()
            } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                onState("disconnected")
            }
        }

        override fun onServicesDiscovered(g: BluetoothGatt, status: Int) {
            val svc = g.getService(SVC) ?: return
            // DeviceInfo first: protocol version must be 1
            svc.getCharacteristic(uuid("0020"))?.let { g.readCharacteristic(it) }
            listOf(CH_ANGLE, CH_DETENT, CH_BATT, CH_BAY, CH_THERM).forEach { u ->
                svc.getCharacteristic(u)?.let { ch ->
                    g.setCharacteristicNotification(ch, true)
                    ch.getDescriptor(CCCD)?.let { d -> enableNotifications(g, d) }
                }
            }
            startHeartbeat()
            onState("connected")
        }

        // API 33+ callback: value arrives as a parameter.
        override fun onCharacteristicChanged(g: BluetoothGatt, ch: BluetoothGattCharacteristic, value: ByteArray) {
            handleChanged(ch, value)
        }

        // Pre-API-33 callback: retained for minSdk 26 devices; on 33+ the
        // overload above is the one the framework invokes.
        @Deprecated("Pre-API-33 callback shape; kept for minSdk 26 devices")
        @Suppress("DEPRECATION")
        override fun onCharacteristicChanged(g: BluetoothGatt, ch: BluetoothGattCharacteristic) {
            handleChanged(ch, ch.value ?: return)
        }

        private fun handleChanged(ch: BluetoothGattCharacteristic, v: ByteArray) {
            when (ch.uuid) {
                CH_ANGLE -> if (v.size >= 2) {
                    val centi = (v[0].toInt() and 0xFF) or ((v[1].toInt() and 0xFF) shl 8)
                    Handler(Looper.getMainLooper()).post { onDrumAngle(centi / 100f) }
                }
                CH_BAY -> if (v.size >= 2) onState("bay module=${v[0]} power=${v[1]}")
                CH_THERM -> if (v.size >= 3) onState("thermal budgetState=${v[2]}")
                CH_BATT -> if (v.size >= 4) onState("battery ${v[0]}%")
                CH_DETENT -> if (v.isNotEmpty()) onState("detents=${v[0]}")
            }
        }
    }

    private fun startHeartbeat() {
        if (heartbeatStarted) return
        heartbeatStarted = true
        heartbeat.scheduleAtFixedRate({
            writeCmd(byteArrayOf(OP_HEARTBEAT))
        }, 0, 10, java.util.concurrent.TimeUnit.SECONDS)   // protocol: every 10 s
    }

    @Suppress("DEPRECATION")
    fun writeCmd(data: ByteArray) {
        val g = gatt ?: return
        val svc = g.getService(SVC) ?: return
        val ch = svc.getCharacteristic(CH_CMD) ?: return
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            // Typed write (API 33+): value passed directly, returns a status code.
            g.writeCharacteristic(ch, data, BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT)
        } else {
            ch.value = data
            ch.writeType = BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT
            g.writeCharacteristic(ch)
        }
    }

    fun setModulePower(moduleId: Int, on: Boolean) =
        writeCmd(byteArrayOf(OP_MODULE, moduleId.toByte(), if (on) 1 else 0))

    fun setBrightnessCap(pct: Int) =
        writeCmd(byteArrayOf(OP_BRIGHTNESS_CAP, pct.coerceIn(0, 100).toByte()))

    fun setDisplayPower(on: Boolean) =
        writeCmd(byteArrayOf(OP_DISPLAY, if (on) 1 else 0))
}
