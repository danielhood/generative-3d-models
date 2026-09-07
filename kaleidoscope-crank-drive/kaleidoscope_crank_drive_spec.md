# Design spec: Kaleidoscope Crank Drive

Prompt: `kaleidoscope-crank-drive-cad-prompt.md`
Revision: rev A (initial spec), 2026-09-07
Status: **spec only — no CAD yet.** Several components are blocked on information
not present in the prompt; see section 7.

---

## 1. Function summary

A hand crank at the viewing end of a ~60 in (1524 mm) stationary kaleidoscope
drives, via a long supported shaft and a #40 roller chain, a ~30 in (762 mm)
diameter object chamber at the far end, at an approximate 5:1 reduction
(5 crank turns : 1 chamber turn). The chamber's weight is carried by its own
axle and bearings, never by the chain or crank. The kaleidoscope body and its
support structure are stationary; only the chamber rotates.

## 2. Requirements

| # | Requirement | Value |
|---|---|---|
| R1 | Overall length | ~60 in / 1524 mm |
| R2 | Crank location | viewing end, beside and slightly below the eyepiece |
| R3 | Crank arm throw | ~7 in / 178 mm, shaft centre to handle centre |
| R4 | Hand grip | freely rotating cylinder, ~4-5 in / 102-127 mm long |
| R5 | Drive shaft | steel, nominal 3/4 in (19.05 mm) starting point, parametric |
| R6 | Drive shaft support | bearing blocks at viewing end, near front drive, and ≥1 intermediate point; all coaxial |
| R7 | Reduction | ~5:1, via 12T #40 drive sprocket : 60T #40 driven sprocket |
| R8 | Chain | ANSI #40 roller chain, removable/replaceable |
| R9 | Chain tensioning | adjustable small-sprocket/shaft mounting position (slots or equivalent) |
| R10 | Chain guard clearance | reasonable clearance reserved for a future removable guard |
| R11 | Object chamber | circular, ~30 in / 762 mm diameter |
| R12 | Chamber support | independent axle on 2 mounted bearings; carries all structural load |
| R13 | Chamber drive | 60T sprocket mounted securely to the chamber axle |
| R14 | Preference | standard/off-the-shelf hardware wherever possible; custom parts only for crank, plates/brackets, chamber hub, guards, structural interfaces |
| R15 | Sizing caveat | preliminary shaft/bearing/hub sizes are NOT assumed final; must be re-sized once chamber weight/loading is known |
| R16 | Deliverables | exploded view, assembled view, individual manufacturable components; mounting holes and realistic clearances; make-vs-buy called out per part |

---

## 3. Assumptions made where the brief is open

| # | Assumption | Reasoning |
|---|---|---|
| A1 | Native unit system is imperial; mm figures in the prompt are exact conversions | 1524 mm = 60.000 in, 762 mm = 30.000 in, 178 mm ≈ 7.00 in exactly — the round numbers are all on the inch side. **Modeling implication:** enter purchased-hardware dimensions (chain pitch, shaft, sprockets) as exact inch→mm conversions, not rounded mm, or bore/keyway fits will be quietly wrong (the pole-foot spec's C7 offset-vs-scale defect is the same class of bug: a rounding choice that looks harmless and isn't). |
| A2 | "5:1 reduction" is exact from the stated tooth counts | 60/12 = 5.000. No rounding tolerance needed on the ratio itself; only the physical center distance and chain length are open (G2, G9 below). |
| A3 | Chain drive is low-speed, hand-powered, low-duty-cycle | No RPM or continuous-use requirement is given. Standard #40 chain and greased mounted bearings are more than adequate once the load (G1) is known; no special lubrication or speed analysis is warranted at this stage. |
| A4 | "Mounted bearings" means standard pillow-block (UCP) or flange (UCF) units, not custom-machined housings | Matches R14's preference for off-the-shelf hardware and is the standard commercial answer to "support a shaft at intervals." Exact unit/footprint is still an open sourcing question (G5). |
| A5 | Shaft-to-hub torque transfer method is undecided (key + keyway vs. set-screw/clamp collars only) | The prompt says "attach securely" but not how. This changes the shaft cross-section (a keyway is a stress concentration) and the bore feature on every hub part, so it must be picked once, early (G7). |
| A6 | Hand-grip rotates on a simple bushing, not a ball bearing | "Freely rotating" for a slow, low-load hand grip is normally solved with a plain bushing (or bare PETG-on-steel-pin). Flagged as a decision, not asserted as final (G8). |
| A7 | Component 9 ("adjustable chain-tensioning mount") is the *front* instance of component 4 ("drive-shaft bearing mounts"), not a separate part | R9 says the small-sprocket/shaft mounting position must be adjustable — that mounting is the front drive-shaft bearing block. Reading it as a fifth, independent bracket would duplicate component 4. Treated as one part (slotted base) unless the user says otherwise (G-tension, below). |
| A8 | PETG is the default print material only for parts with no significant sustained mechanical load (hand grip, guard, hub shell) | Consistent with the rest of this repo's material choice. The crank arm carries the full hand-cranking force at a lever arm and repeats every use; whether PETG is adequate there is explicitly flagged, not assumed (G16). |

---

## 4. System layout and derived geometry

**Chain/sprocket geometry** (ANSI #40: pitch p = 0.500 in = 12.700 mm, roller Ø 0.312 in / 7.92 mm):

Pitch diameter `PD = p / sin(180°/N)`; outside diameter `OD ≈ p·(0.6 + cot(180°/N))` (ANSI B29.1 addendum formula — a good concept-stage estimate; the real OD/hub/keyway comes off the vendor drawing, see G6).

| | N | PD | OD (est.) |
|---|---|---|---|
| Drive sprocket | 12 | 1.932 in / 49.1 mm | 2.166 in / 55.0 mm |
| Driven sprocket | 60 | 9.554 in / 242.7 mm | 9.841 in / 250.0 mm |

**Center distance** is listed in the prompt as a parameter but no value or layout is given (G2). Chain length in pitches, once a center distance `C` is chosen:

    L = (N1+N2)/2 + 2C/p + p(N2-N1)^2 / (4*pi^2*C)

`L` should round to a whole (ideally even) number of pitches; adjust `C` slightly to land on one rather than forcing an offset link. This also sets the take-up travel needed at the tensioning mount (R9) — nominally on the order of one pitch (12.7 mm) of adjustment, to be confirmed once `C` is fixed.

**Minimum center distance** to clear the two sprockets and leave chain-guard clearance: roughly `(OD_large + OD_small)/2 + guard clearance` ≈ 152.5 mm + clearance. **Recommended** center distance for good wrap angle on the small sprocket and reasonable chain wear life is on the order of the large sprocket's pitch diameter or more (≥ ~243 mm), which is also well above the interference minimum. A provisional **300 mm** is used as a placeholder default below — it is not derived from the actual front-end layout, which is unknown (G2).

**Drive shaft length** runs the full ~1524 mm kaleidoscope length less end clearances at the viewing-end and front-end bearing mounts; exact end offsets depend on the (unspecified) eyepiece and front-frame geometry (G13, G2).

---

## 5. Component breakdown (make vs. buy)

| # | Component | Make / Buy | Notes |
|---|---|---|---|
| 1 | Hand crank arm | **Make** | Custom lever, shaft-end hub + handle-end pin boss. Material adequacy under repeated hand torque not yet checked — G16. |
| 2 | Rotating hand grip | **Make** (print) | Sleeve over a pin/axle; bushing fit per A6. |
| 2b | Grip pin/axle | **Buy** (raw stock) | Steel rod, cut to length; diameter set by grip bushing choice (G8). |
| 3 | Long drive shaft | **Buy** (raw stock) | Steel shafting, nominal 3/4 in to start (R5), cut to length; not load-verified (G1, R15). |
| 4 | Drive-shaft bearing mounts (viewing end + front) | **Buy** bearing + **Make** bracket | Bearing: standard pillow/flange block, exact unit TBD — G5. Bracket: custom plate to frame — G3. Front instance doubles as the tensioning mount, A7. |
| 5 | Intermediate drive-shaft bearing mount | **Buy** bearing + **Make** bracket | Same as #4; count and spacing depend on shaft span/deflection, not yet calculated (G1, G15). |
| 6 | 12T #40 drive sprocket | **Buy** | Reference geometry in section 4; bore/keyway from vendor drawing — G6. |
| 7 | 60T #40 driven sprocket | **Buy** | Same as #6. |
| 8 | #40 roller chain (path) | **Buy** chain; **Make** reference geometry | Chain itself is commodity stock cut to the length in section 4; the CAD "path" is a non-physical reference curve for clearance/visual checks, not a manufactured part. |
| 9 | Adjustable chain-tensioning mount | **Make** | Per A7, treated as the front instance of #4 with slotted base rather than a fifth bracket — confirm before modeling (G-tension). |
| 10 | Front object-chamber axle | **Buy** (raw stock) | Steel shaft, custom length/diameter; ends likely need machining for retaining features once G1/G7 are resolved. |
| 11 | Two front-axle bearing mounts | **Buy** bearing + **Make** bracket | Same pattern as #4/#5; must carry full chamber weight per R12 — the one component where G1 is most directly load-bearing. |
| 12 | Hub/flange, chamber-to-axle | **Make** | Fully custom per R14. Blocked on chamber attachment geometry — G4. |
| 13 | Structural mounting plates/brackets to wood frame | **Make** | Blocked on frame cross-section/material at each mount point — G3. |
| 14 | Removable chain/sprocket guard | **Make** | Sized from the real sprocket OD and chain path (section 4) and center distance (G2) — model last. |

---

## 6. Parametric design table

Per the prompt's explicit list of parameters to expose. "Status" marks whether the default below is a given spec value, a calculated/derived value, or a placeholder standing in for an unresolved gap.

| Parameter | Proposed default | Status |
|---|---|---|
| Kaleidoscope length | 1524 mm | Given (R1) |
| Object chamber diameter | 762 mm | Given (R11) |
| Drive shaft diameter | 19.05 mm (3/4 in) | Given starting point, **not final** — R15, G15 |
| Front axle diameter | 19.05 mm (3/4 in) | Placeholder, no value given — G1, G15 |
| Crank arm length | 178 mm (7 in) | Given (R3) |
| Bearing spacing | ~508 mm (even 3-way split of 1524 mm) | Placeholder — no span given beyond "viewing end, front, ≥1 intermediate" — G3, G15 |
| Sprocket tooth counts | 12 / 60 | Given (R7) |
| Sprocket centre distance | 300 mm | Placeholder — G2, G9 |
| Mounting plate thickness | 6 mm (steel, TBD material) | Placeholder — depends on G1 load and G3 frame material |
| Chain clearance | 18 mm radial, all round | Placeholder for "reasonable clearance" (R10) — revisit when the guard (component 14) is modeled |

---

## 7. Open items / gaps

Grouped by whether they block modeling a component outright, or can proceed on a documented placeholder.

**Blocking**

- **G1 — Chamber mass/inertia unknown.** R15 explicitly says not to assume the preliminary shaft is adequate. Without an estimated chamber weight (and its distribution — glass, mirrors, wood?), the front axle diameter, both front-axle bearings' load rating, the hub/flange fasteners, and the hand-force/crank-arm ergonomics all remain provisional. **Needed:** a chamber weight estimate (or a worst-case placeholder the user is willing to design against).
- **G2 — Front-end layout unknown.** How far, and in what direction (above/below/beside), does the drive shaft's small sprocket sit from the chamber axle's large sprocket? This sets the sprocket center distance, chain length, guard shape, and whether the chain fouls the chamber's rotating envelope. **Needed:** a front-end layout sketch or dimensioned coordinates.
- **G3 — Frame geometry unknown.** Cross-section and material of the wooden frame at each of the ≥3 bearing-mount locations. Required to size the structural mounting plates/brackets (component 13) and their fastener pattern into wood. **Needed:** frame member dimensions at each mount point.
- **G4 — Chamber hub interface unknown.** Nothing in the prompt describes how the rotating chamber physically attaches to its axle (bolt circle, hole count, chamber material/thickness at the attachment point). Component 12 cannot be modeled without this. **Needed:** chamber-side attachment geometry (likely from whatever separate design defines the chamber itself).

**Sourcing-dependent (need a specific vendor part, not just a decision)**

- **G5 — Bearing selection.** Pillow block vs. flange, bolt pattern, base footprint — needed to model components 4, 5, 11 against real geometry instead of a generic stand-in.
- **G6 — Sprocket hub details.** Keyway size, set-screw arrangement, hub OD/length, exact bore — needed for components 6, 7 and for whatever shaft-collar/key design result from G7.

**Design decisions (no missing information, just need a call)**

- **G7 — Shaft-to-hub attachment method.** Key + keyway vs. clamp/set-screw collars only (A5). Affects every hub part and the shaft cross-section.
- **G8 — Hand-grip bearing type.** Plain bushing vs. rolling-element bearing (A6).
- **G-tension — Is the tensioning mount (component 9) the same physical part as the front drive-shaft bearing mount (component 4), or a separate idler/slide?** Assumed the former (A7); flag if that's wrong, since it changes the component count.
- **G16 — Crank arm material adequacy.** PETG is the repo's default print material, but a 178 mm lever arm under repeated hand torque, printed with a keyway or set-screw pocket near the shaft interface, is a plausible fatigue/stress-concentration risk. Worth a quick hand-force check once G1 gives a real required torque; may end up as a metal arm or a PETG arm with a metal shaft insert rather than pure PETG.

**Non-blocking (placeholder values above are fine to model against, revisit later)**

- **G9 — Sprocket center distance / chain length** (section 4): can proceed with the 300 mm placeholder; recompute chain length and re-check wrap angle once G2 resolves the real distance.
- **G10 — Chain tensioning slot travel:** propose ≥ 1 pitch (12.7 mm) of adjustment; confirm once real chain length (G2/G9) is fixed.
- **G13 — Eyepiece position** is referenced ("beside and slightly below the eyepiece") but the eyepiece itself is out of scope of this prompt. A placeholder coordinate is needed so the viewing-end bearing mount and crank have something concrete to reference.

---

## 8. Proposed CAD file structure

Given the part count and the make/buy split, this project does not fit the pole-foot pattern of one `.scad` with a `part` switch. Proposed layout, to be created once the blocking gaps in section 7 have at least placeholder answers:

    kaleidoscope-crank-drive/
      kaleidoscope-crank-drive-cad-prompt.md
      kaleidoscope_crank_drive_spec.md   (this file)
      cad/
        params.scad          -- shared parametric values (section 6), single source of truth
        crank_arm.scad        [MAKE]
        hand_grip.scad         [MAKE] + pin as a buy-part reference
        drive_shaft.scad      [BUY  - reference geometry]
        bearing_mount_end.scad         [MAKE bracket, BUY bearing insert as reference]
        bearing_mount_intermediate.scad [MAKE bracket, BUY bearing insert as reference]
        sprocket_12t.scad     [BUY  - reference geometry, section 4]
        sprocket_60t.scad     [BUY  - reference geometry, section 4]
        chain_path.scad        -- non-physical reference curve, not exported to STL
        tension_mount.scad    [MAKE]
        chamber_axle.scad     [BUY  - reference geometry]
        axle_bearing_mount.scad        [MAKE bracket, BUY bearing insert as reference]
        chamber_hub.scad      [MAKE]  -- blocked on G4
        mounting_bracket.scad [MAKE]  -- blocked on G3
        chain_guard.scad      [MAKE]  -- model last, needs section 4 finalized
        assembly.scad          -- includes all of the above, positioned per section 4

Purchased-part files (`drive_shaft`, `sprocket_*`, `chamber_axle`, the bearing-insert
reference geometry) exist to support assembly visualization and clearance
checking, and should be clearly marked non-manufactured in their header comment
— this keeps the eventual "which parts are bought vs. printed" deliverable
(R16) unambiguous straight from the file list.

## 9. Suggested sequencing

1. Resolve or explicitly placeholder G1-G4 (the four blocking gaps) and G7/G8/G-tension (the three free decisions) — none of these require sourcing, just information or a call.
2. Model the **buy** reference parts first (shaft, axle, sprockets via section 4's formulas) — they're needed as context for every bracket that mounts around them, and they don't depend on G5/G6.
3. Model brackets/mounts (4, 5, 9, 11, 13) against the buy parts and section 3's placeholders; revisit once G5 gives real bearing footprints.
4. Model the fully-custom parts with no off-the-shelf reference (crank arm, hand grip, chamber hub) — hub is blocked on G4.
5. Model the chain guard last, once the real sprocket OD (G6) and center distance (G2/G9) are in.
6. Assemble, produce the exploded/assembled views, and only then revisit shaft/bearing/hub sizing against real loads (G1, R15) before calling anything build-ready.
