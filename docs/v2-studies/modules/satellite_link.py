#!/usr/bin/env python3
"""
NEXUS ONE v2.0 — satellite module link-budget SANITY (class level).
Not a full link budget: per-network satellite G/T, EIRP density limits and
regulatory margins are operator-specific (NOT-VERIFIED). What this checks:
free-space path loss for the two constellation classes the MT6825-class
modem targets, device EIRP, and why 3GPP R17 IoT-NTN closes the link.
"""
import math

def fspl_db(d_km, f_mhz):
    return 32.44 + 20*math.log10(d_km) + 20*math.log10(f_mhz)

# n255 L-band uplink 1626.5-1660.5 MHz (Inmarsat/Ligado-class GEO)
F_MHZ = 1640.0
D_GEO = 35786.0    # km
D_LEO = 550.0      # km, LEO-class (Lynk/AST-class altitude)

TX_DBM   = 23.0    # 3GPP power class 3 handheld
ANT_GAIN = 3.0     # dBi, ASSUMPTION: L-band patch in end-cap window
EIRP = TX_DBM + ANT_GAIN

print("=== NEXUS ONE v2.0 satellite link-budget sanity (class level) ===")
print(f"Band: n255 L-band UL ~{F_MHZ:.0f} MHz | device TX {TX_DBM:.0f} dBm + {ANT_GAIN:.0f} dBi -> EIRP {EIRP:.0f} dBm")
for name, d in (("GEO", D_GEO), ("LEO", D_LEO)):
    L = fspl_db(d, F_MHZ)
    pr = EIRP - L          # dBm at an isotropic satellite antenna
    print(f"\n{name} (d={d:.0f} km): FSPL = {L:.1f} dB")
    print(f"  Pr_iso = {pr:.1f} dBm")
    if name == "GEO":
        print(f"  Sanity: 3GPP R17 IoT-NTN (NB-IoT NTN, 180 kHz, up to 128x")
        print(f"  repetitions, ~-13 dB SNR operating point) is DESIGNED for")
        print(f"  exactly this ~188 dB path — commercial proof: Motorola Defy 2")
        print(f"  / CAT S75 / Defy Satellite Link ship MT6825 on GEO networks.")
    else:
        print(f"  Sanity: {fspl_db(D_GEO,F_MHZ)-L:.0f} dB easier than GEO — closes with wide margin;")
        print(f"  same modem class, same antenna.")

print("\nDownlink (satellite -> phone, 1525-1559 MHz DL):")
print("  Satellite EIRP density is network-controlled; phone RX needs only")
print("  ~-3 dBi patch gain + modem sensitivity (~-130 dBm class, ASSUMPTION).")
print("  Paging/messaging DL on GEO is the proven commercial configuration.")
print("\nNOT-VERIFIED: per-operator G/T, EIRP-density regulatory mask,")
print("  in-situ antenna efficiency with the real end-cap + hand/body loading,")
print("  3GPP R17 certification of the module as built.")
