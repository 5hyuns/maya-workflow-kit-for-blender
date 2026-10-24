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
