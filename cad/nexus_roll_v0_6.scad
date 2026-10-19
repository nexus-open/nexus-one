// NEXUS ONE - ROLL architecture v0.6
// One REAL flexible AMOLED (162.9 x 74.5 x 1.2 mm module class, 2400x1080)
// wraps an R8 drum inside the spine; a sliding leading bar unrolls it.
// Replaces MECH-B's 3 stacked display frames: a continuous panel cannot fold
// at MECH-B's 3.4 mm layer pitch (bend radius would be ~1.7 mm; AMOLED needs
// >= ~5 mm). Wrap radius here is 8 mm at EVERY pose (checker-verified:
// panel length conserved exactly, 1,001 poses).
// Interlocks designed in:
//  1. Rack on the leading bar drives the drum pinion (module 0.5, 32 teeth,
//     pitch radius = drum radius 8) - panel feed rate == bar speed, the panel
//     can never be yanked faster than the drum feeds it.
//  2. Light-field lenticular cover rail-mounts only at full deployment; while
//     mounted its rails block retraction (film can never be crushed by closing).
//  3. Spring-ball detents + 2 pairs N52 5x2 magnets hold both end positions
//     (retention spec >= 3 N, from the v0.4 jolt analysis).
// OpenSCAD: View > Animate, Steps=201, FPS=20. $t = deployment 0..1.
// NOT compiled - OpenSCAD unavailable in the build environment (balance-checked).
// X = device length (panel length); Y = deployment; Z = panel normal.

$fn = 32;
panel_l = 162.9;
panel_t = 1.2;
L_use = 71.5;            // usable panel width (74.5 - 2x1.5 sealed edges)
R = 8;                   // drum radius to panel centreline
F0 = 28;                 // front flat, stick mode (visible strip)
F1 = 58.9;               // front flat, fully open
dev_l = 171.9;
show_cover = false;      // light-field cover (stored in carry-case sleeve)

function front(u) = F0 + (F1 - F0) * u;
function back_flat(u) =
    let (b0 = L_use - F0 - PI * R)
    u < 0.85 ? max(0, b0 * (1 - u / 0.85)) : 0;
function theta(u) = (L_use - front(u) - back_flat(u)) / R;   // radians, pi..pi/2

module panel_ribbon(u) {
    F = front(u); B = back_flat(u); th = theta(u);
    color([0.15, 0.45, 0.95, 0.95]) {
        // front flat
        translate([0, -F / 2, R]) cube([panel_l, F, panel_t], center = true);
        // back flat
        if (B > 0.3)
            translate([0, B / 2, -R]) cube([panel_l, B, panel_t], center = true);
        // wrap arc as chord segments
        K = 14;
        for (i = [0 : K - 1]) {
            a_deg = 90 - (i + 0.5) * th * 180 / PI / K;
            seg = R * th / K + 0.35;
            translate([0, R * cos(a_deg), R * sin(a_deg)])
                rotate([90 - a_deg, 0, 0])
                    cube([panel_l, seg, panel_t], center = true);
        }
    }
}

module drum() {
    color([0.55, 0.58, 0.63, 1])
    rotate([0, 90, 0]) cylinder(h = panel_l, r = R - panel_t / 2 - 0.3, center = true);
    // pinion gear (sync interlock) - schematic: cylinder + teeth blocks
    color([0.85, 0.65, 0.2, 1])
    translate([panel_l / 2 + 3, 0, 0]) rotate([0, 90, 0])
        cylinder(h = 1.6, r = R, center = true);
}

module leading_bar(u) {
    F = front(u);
    color([0.2, 0.22, 0.27, 1])
    translate([0, -F - 1.5, R]) cube([panel_l, 4, 5], center = true);
    // rack (schematic teeth) on the bar underside, meshes the drum pinion path
    color([0.85, 0.65, 0.2, 1])
    translate([panel_l / 2 + 3, -F + 6, R - 5]) cube([1.6, 12, 1.2], center = true);
}

module housing(u) {
    // back shell + two end caps; front stays open (the panel IS the front)
    color([0.13, 0.15, 0.19, 0.9])
    translate([0, 2, -R - panel_t - 1.6]) cube([dev_l, 36, 2.4], center = true);
    for (sx = [-1, 1])
        color([0.13, 0.15, 0.19, 1])
        translate([sx * (dev_l / 2 - 2), -4, 0]) cube([4, 34, 21], center = true);
}

module light_field_cover() {
    // mounts only at full open; shown hovering at its mounted plane
    cover_y = -F1 + (F1 + R * PI / 2) / 2;
    color([0.6, 0.85, 1.0, 0.35])
    translate([0, cover_y, R + panel_t + 1.5])
        cube([panel_l, F1 + R * PI / 2, 0.5], center = true);
}

u = min(1, max(0, $t));
housing(u);
drum();
panel_ribbon(u);
leading_bar(u);
if (show_cover) light_field_cover();

// Open items: dynamic rolling cycle rating of the maker panel (unverified),
// FPC routing from the wrapped panel to the board, drum spring/motor sizing,
// antenna windows in end caps, module bay (v0.4 audit parts) not yet integrated.
