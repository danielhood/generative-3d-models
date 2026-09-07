use <pole_foot.scad>
$fa = 1; $fs = 0.3;
difference() {
    foot();
    translate([-40, 0, -1]) cube([80, 40, 60]);   // cut away the +Y half
}
