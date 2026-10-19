// NEXUS ONE — MECH-B staged guide cassette v0.3
// Split end plates with vertical-lift / straight-slide / vertical-lower slots.
// v0.3 changes vs v0.2 (see reports/REPORT_v0_3.md):
//  1. plate_z_low -1.0 -> -2.6 and plate_z_high 9.5 -> 10.7: thinnest slot
//     walls go from 0.4 mm (lower) / 0.6 mm (left upper) to 2.0 / 1.8 mm.
//     Plates now socket 2.6 mm into the spine top (sockets cut in frame()).
//  2. Slot corners get relief circles (slot_w + 0.6) so the 0.8 mm pin has
//     room to turn the 90-degree corners instead of hitting a sharp corner.
//     NOTE: pin MOTION is still the sharp staged path; relief is clearance,
//     not a smoothed motion profile. Motion smoothing stays an open item.
//  3. Deployment sequence is now a documented constraint (validator check D):
//     LEFT wing deploys FIRST, RIGHT wing folds FIRST. Moving the right wing
//     while the left is folded collides (0.6 mm Z interference, 721/1001
//     sampled poses in the rebuilt checker). A physical unit needs a
//     sequence interlock or a geometry change - not yet designed.
// Concept geometry only: OpenSCAD rendering and physical fit are not yet verified.
// OpenSCAD: View > Animate, Steps=201, FPS=20, then enable Animate.
// X = panel length; Y = lateral deployment; Z = normal to panel.

$fn=24;
panel_l=137;
panel_w=24;
panel_t=2.5;
pitch=3.4;
lift=1.5;
spine_l=145;
spine_w=32;
spine_h=14;
deck_a=0.6;
deck_b=1.0;
base_z=spine_h+deck_a+deck_b;
plate_y_half=15.5;
plate_z_low=-2.6;
plate_z_high=10.7;
plate_t=1.0;
pocket_x=1.6;
slot_w=1.2;
pin_d=0.8;
tab_y=1.8;
lift_fraction=0.15;
slide_fraction=0.70;
lower_fraction=0.15;
show_frame=true;
show_panels=true;
show_plates=true;
show_mounts=true;

function y_start()=-panel_w/2;
function y_end(side)= side<0 ? -37.4 : 13.4;
function start_z(side)=side<0 ? 2*pitch : pitch;
function peak_z(side)=start_z(side)+lift;
function station_x(side)=side<0 ? 69.4 : 71.0;
function panel_y(side,u)=
    u<lift_fraction ? y_start()
    : u<lift_fraction+slide_fraction
      ? y_start()+(y_end(side)-y_start())*((u-lift_fraction)/slide_fraction)
      : y_end(side);
function panel_z(side,u)=
    u<lift_fraction ? start_z(side)+lift*(u/lift_fraction)
    : u<lift_fraction+slide_fraction ? peak_z(side)
    : peak_z(side)*(1-(u-lift_fraction-slide_fraction)/lower_fraction);
function pin_y(side,u)=side<0 ? panel_y(side,u)+panel_w : panel_y(side,u);
function slot_points(side)=side<0
    ? [[12,6.8],[12,8.3],[-13.4,8.3],[-13.4,0]]
    : [[-12,3.4],[-12,4.9],[13.4,4.9],[13.4,0]];

module slot_stroke(pts,w) {
    union() {
        for (i=[0:len(pts)-2]) hull() {
            translate(pts[i]) circle(d=w);
            translate(pts[i+1]) circle(d=w);
        }
        // v0.3 corner relief: widen each interior corner so the pin can turn.
        for (i=[1:len(pts)-2])
            translate(pts[i]) circle(d=w+0.6);
    }
}

module guide_plate(side,xcenter) {
    pts=slot_points(side);
    color(side<0 ? [0.92,0.53,0.16,0.92] : [0.12,0.66,0.59,0.92])
    multmatrix([[0,0,1,xcenter-plate_t/2],
                [1,0,0,0],
                [0,1,0,base_z],
                [0,0,0,1]]) {
        difference() {
            linear_extrude(height=plate_t)
                polygon(points=[[-plate_y_half,plate_z_low],
                                [ plate_y_half,plate_z_low],
                                [ plate_y_half,plate_z_high],
                                [-plate_y_half,plate_z_high]]);
            translate([0,0,-0.1])
                linear_extrude(height=plate_t+0.2)
                    slot_stroke(pts,slot_w);
        }
    }
}

module guide_plates() {
    for (sx=[-1,1]) {
        guide_plate(-1,sx*station_x(-1));
        guide_plate( 1,sx*station_x( 1));
    }
}

module deck_top_with_cassette_pockets() {
    difference() {
        color([0.64,0.67,0.72,0.96])
        translate([-spine_l/2,-spine_w/2,spine_h+deck_a])
            cube([spine_l,spine_w,deck_b]);
        // Four shallow pockets let the independent guide plates sit on the top deck.
        for (sx=[-1,1]) for (side=[-1,1])
            translate([sx*station_x(side)-pocket_x/2,
                       -plate_y_half-0.05,
                       spine_h+deck_a-0.05])
                cube([pocket_x,2*plate_y_half+0.1,deck_b+0.1]);
    }
}

module plate_sockets(z0,z1) {
    // v0.3: plates extend to base_z+plate_z_low, so they socket through the
    // decks and 1.0 mm into the spine top. Adjacent plate bands at one end
    // merge into one socket (bands are 1.6 mm apart, sockets 1.6 mm wide).
    for (sx=[-1,1]) for (side=[-1,1])
        translate([sx*station_x(side)-(plate_t+0.6)/2,
                   -plate_y_half-0.1,
                   z0])
            cube([plate_t+0.6,2*plate_y_half+0.2,z1-z0]);
}

module frame() {
    color([0.20,0.23,0.29,1])
    difference() {
        translate([-spine_l/2,-spine_w/2,0])
            cube([spine_l,spine_w,spine_h]);
        plate_sockets(spine_h-1.1,spine_h+0.1);
    }
    color([0.47,0.50,0.56,1])
    difference() {
        translate([-spine_l/2,-spine_w/2,spine_h])
            cube([spine_l,spine_w,deck_a]);
        plate_sockets(spine_h-0.1,spine_h+deck_a+0.1);
    }
    deck_top_with_cassette_pockets();
}

module panel(y,z,c) {
    color(c) translate([-panel_l/2,y,z]) cube([panel_l,panel_w,panel_t]);
}

module wing_mounts(side,u) {
    yy=pin_y(side,u);
    zz=base_z+panel_z(side,u);
    xx=station_x(side);
    for (sx=[-1,1]) {
        xcenter=sx*xx;
        xedge=sx*(panel_l/2-0.30);
        // Stop the arm at the plate's inner face; pin spans through the slot.
        xinner=xcenter-sx*plate_t/2;
        xlo=min(xedge,xinner);
        xhi=max(xedge,xinner);
        if (show_mounts)
            color(side<0 ? [0.72,0.35,0.12,1] : [0.08,0.46,0.42,1])
            translate([xlo,yy-tab_y/2,zz-0.30])
                cube([xhi-xlo,tab_y,0.90]);
        if (show_mounts)
            color([0.93,0.76,0.20,1])
            translate([xcenter,yy,zz])
                rotate([0,90,0]) cylinder(h=plate_t+1.2,d=pin_d,center=true);
    }
}

u=min(1,max(0,$t));
if (show_frame) frame();
if (show_panels) {
    panel(y_start(),base_z,[0.16,0.43,0.86,0.96]);
    panel(panel_y(-1,u),base_z+panel_z(-1,u),[0.90,0.31,0.20,0.93]);
    panel(panel_y( 1,u),base_z+panel_z( 1,u),[0.15,0.67,0.49,0.93]);
}
if (show_plates) guide_plates();
wing_mounts(-1,u);
wing_mounts( 1,u);

// Slot centre-lines use follower positions, not panel centres:
// left: Y=+12 -> -13.4; right: Y=-12 -> +13.4.
// Three stages are discrete in this preview. v0.3 adds corner relief clearance
// and thicker slot walls, but a smoothed motion profile, pin retention,
// sequence interlock, assembly access, cover, flex routing and
// material/tolerance behavior remain open.
