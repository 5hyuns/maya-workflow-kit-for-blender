# Step 169 — Deform completion

Backlog `backlog_164.json` #6 (재점검 11차 `step_163_quant.md` §6 #4): Deform 41 % (30 / 74), 20 dead option boxes,
9 "Blender has no settings" (`option_generic`) boxes under Paint Weights.

## 계획

Measurement first (mayapy, `research/maya/re/deform_169.md`): Wire deformer on a 10 × 10 plane (40 × 40 faces) with
a straight 4-CV cubic curve — translate / rotate / twist / scale / CV edit / envelope / dropoff, dropoff locators;
wire edit commands (Reset / Show Base Wire / Remove); ShrinkWrap edit commands; lattice Reset / Remove Tweaks;
prune. The wire rule found (§1 there) reproduces every measured point to 1e-7 in a pure-Python model
(`tmp/s169/model.py`) before any Blender code is written.

Design (delegated):
- **Wire = a Geometry Nodes modifier** `wire1` (shared node group `.Allset Wire`), not a Hook: a Hook moves points by
  `w (M p − p)`, but Maya rotates the offset by `w × angle` and ignores twist / scale of the curve object (measured:
  30° turn → Hook off by 0.012, twist / scale → Hook moves points Maya leaves alone). The group reads the wire and
  `curve1BaseWire` (a hidden copy of the curve, like Maya's) through Object Info, turns both into polylines at the
  curve's evaluated points (the same count, uniform in parameter), finds the nearest base edge, and applies
  `p + env · [w (c' − c) + (R(T→T', w · rotation · angle) (p − c) − (p − c))]`, `w = (1 − (d / D)²) · weight`.
  Dropoff locators = 4 slots (param, percent × envelope) on the modifier, piecewise `g(t) = 1 − (1 − t²)²` between
  [0, locators…, 1] with scale 1 at both ends (measured).
- Wire edit items: Add (another curve on the same object = another wire node; delegated), Remove, Reset (the curve
  goes back to its base), Show Base Wire, Parent Base Wire, Wire Dropoff Locator — Maya option windows "Add / Remove /
  Reset / Parent Base Wire Options" (Specify node + Wire node) and "Wire Dropoff Locator Options" (Envelope, Percent).
  Add Holder stays greyed (holders: no Blender form).
- ShrinkWrap: Set Target / Remove Target / Add surfaces / Remove surfaces on the Shrinkwrap modifier; Set / Remove
  Inner Object stay greyed (Blender's Shrinkwrap has no inner object).
- Lattice: Reset Lattice / Remove Lattice Tweaks on the kit `ffd` lattice; Prune Membership Cluster / Lattice / Wire
  = drop zero-weight points from the deformer's vertex group (Maya 2022's component tags pruned nothing in the
  measurement: "No components could be pruned.").
- Point On Curve: locator at the selected curve point + Hook on that control point (Point weight = hook strength).
- Paint Weights boxes (incl. new Wire) = the Maya "Paint Attributes Tool" window (Paint operation, Profile, Opacity,
  Value, Radius(U)) through `skin.apply_paint_settings`.

Order: measurement → model check → implementation (the GN group needs the rule) → tests. Lanes were not split into
sub-agents: every lane edits `deformers.py` / `menu_map.py` / `notices.py` / `option_windows_deform.py` (delegated).

## 한 것

- **Wire** = kit deformer (`operators/wire_deformer.py`, `deformers._wire`): select the objects, then the curve
  (Maya's Wire Tool order); `wire1` = Geometry Nodes modifier on `.Allset Wire`, weights = vertex group `wire1`,
  `curve1BaseWire` = hidden copy of the curve, curve1 selected afterwards. Channel Box INPUTS: Envelope, Rotation,
  Dropoff Distance[0] (`deformers.ATTRS["wire"]`). Option box = "Wire Tool" window (Envelope, Dropoff distance).
- **Wire >** Add / Remove / Reset / Show Base Wire / Parent Base Wire (`allset.wire_edit`) and Wire Dropoff Locator
  (`allset.wire_dropoff_locator`, edit-mode point on the wire curve → locator + slot) with Maya's option windows and
  messages (`operators/deform_edit.py`, `option_windows_deform.py`). Add Holder stays greyed (notice).
- **ShrinkWrap >** Set Target / Remove Target / Add surfaces / Remove surfaces (`allset.shrink_wrap_edit`); Set /
  Remove Inner Object greyed with a notice. **Lattice >** Reset Lattice / Remove Lattice Tweaks
  (`allset.lattice_edit`, base from the `ffdNBase` Hook). **Prune Membership >** Cluster / Lattice / Wire
  (`allset.prune_membership`). **Point On Curve** (`allset.point_on_curve` + "Point On Curve Options").
- **Paint Weights** boxes (10 incl. Wire and Set Membership) = "Paint Attributes Tool" / "Paint Blend Shape Weights
  Tool" windows (Paint operation, Profile, Opacity, Value, Radius(U)) through `skin.apply_paint_settings`
  (normalize `None` = deformer weights, never normalized). Paint Weights > Wire works (curve or mesh selected).

## 검증

- `research/maya/re/deform_169.md` (mayapy): wire rule, dropoff locators, edit items, ShrinkWrap, lattice, prune.
- `tests/test_step169_deform.py` 13 / 13: wire vs mayapy (`tests/maya169_wire_data.py`) — translate D 1 / 2,
  sideways, envelope 0.5, curve above, rotate 30° (rotation 1 / 0), twist, scale, CV edit: worst **1.03e-5**
  (CV edit), others ≤ 1e-6; dropoff locators (1 at 0.5, 1 at 0.25, 2) worst 7e-7; painted weights; Reset / Show Base /
  Parent Base / Remove / Add; ShrinkWrap edits; lattice reset / tweaks; prune; Point On Curve; Paint windows;
  **Deform 48 / 74 = 65 %** (was 30 = 41 %), **generic 0** (was 9), **dead 12** (was 20).
- Headless full: 1577 / 1579 on the first run (`test_step125_name` — the hidden node group name `.Allset Wire` added
  to its HIDDEN list like `.Allset Smooth Preview Shading`; `test_step144_deform` GREYED list still had Wire) → fixed,
  those + related files 54 / 54.
- GUI: `gui_step169_wire` 4 / 4 + `gui_step144_deform` 9 / 9. Screenshots checked: the plane bends along the moved +
  bent wire (front view), curve1BaseWire shown and selected in the Outliner, Paint Attributes Tool window.
- `tools/menu_count.py --options`: window 86 → **103**, generic 45 → **36**, dead 223 → **215**, redo 120 = 120;
  menus 51.1 → 52.5 % (unique paths).

## 남은 것

- Wire: holders (Add Holder), Crossing Effect / Tension / Local Influence / Scale[], more than 4 dropoff locators;
  distances are measured in the deformed object's space (a scaled object reads them scaled). Add makes one extra
  influence modifier per curve (`wire1curve2`), not shown as its own INPUTS node.
- Still dead (12): Tension, Solidify, Morph, Wrinkle, Pose Interpolator, Sculpt, Jiggle Deformer / Disk Cache, Blend
  Shape Swap, Add Holder, Paint Weights Tension / Jiggle.
