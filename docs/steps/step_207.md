# Step 207 — Curves 3 (backlog #6, Issue #114)

Source: `docs/steps/step_201_quant.md` §1b (Curves 58 %, five audits unchanged), `research/maya/re/curves_156.md` /
`.json`; new Maya measurements `research/maya/re/curves_201.md` / `curves_201.json`.

## Plan

1. mayapy measurement first (one Maya at a time): Bend / Curl / Scale Curvature with option variants, CV ranges,
   moved transforms and degree 1; CV Hardness on every CV of two curves; Fit B-spline polylines; Align end pairs;
   Duplicate Surface Curves isoparms; Intersect; Lock Length moves.
2. Rules into `curves_math` / `surfaces_math` (bpy-free) and checked against the JSON in plain Python before any
   Blender code (Bend / Curl / Scale Curvature turned out to be MEL — exact port).
3. Operators `operators/curves_207.py`, option windows for Bend / Curl / Scale Curvature, menu map, tests (pure +
   operators + cm scene + undo), GUI test with a shot.
Sequential on purpose: each rule needed the measurement first, and the only parallel work (Blender tests) shares the
two Blender slots.

## Done

- Curves > **Bend / Curl / Scale Curvature** = `allset.curve_modify` (Maya modifySelectedCurves, Maya Y-up frame,
  Maya-unit amounts); object = all CVs, edit mode = the selected CV range; option windows `opt_bend_curves`,
  `opt_curl_curves`, `opt_scale_curvature` (Maya titles / labels / factory values).
- **Lock / Unlock Length** = `allset.curve_lock_length` (curve data `allset_lock_length` = Maya lockLength; a depsgraph
  handler keeps every CV leg length while the curve is edited — delegated, Maya's manipulator rule [U]).
- **CV Hardness** = `allset.curve_cv_hardness` (hardenPointCurve full multiplicity on the last selected CV).
- **Fit B-spline** = `allset.curve_fit_bspline` (degree-1 curves → `fitBsplineCurveN`).
- **Align** = `allset.curve_align` (first selected curve onto the nearest end of the other, tangent continuity).
- **Duplicate Surface Curves** = `allset.duplicate_surface_curves` (visible isoparms / picked rows).
- **Intersect** = `allset.curve_intersect` (locators at the crossings, parented to each curve).
- **Bezier Curves > Tangent Options > Uneven Anchor Tangents** = Blender Aligned handles (delegated: Even = Automatic,
  Uneven = Aligned, both keep the handle direction).
- Curves menu **21 → 32 / 36** (`tmp/curves_list.py` over `tools/menu_count` data).

## Verification

- `python tests/run.py -k step207`: 18 / 18 — 99 Maya results compared, worst 5.8e-7 (Bend / Curl / Scale Curvature /
  Smooth / Straighten 67 cases incl. CV range, transform, degree 1; CV Hardness 30 knot vectors exact; Fit B-spline 6;
  Align 5 incl. start-to-start and B-first; isoparms 12; Intersect parameters), operators on Blender objects (1e-6),
  cm scene (Maya units), Lock Length legs, undo, menu / option windows.
- `python tests/gui/run.py -k step207,step156_curves,step181_surfaces,smoke,switch,layout,enable`: 97 / 97; shot
  `tmp/shots207/gui_step207_curves.png` (bent curve + the intersect pair from the top view, locator1–4 in the result
  field).
- Full headless: 1998 / 1999 on the first run (`test_step166`: nHair > Modify Curves Bend / Curl / Scale Curvature / Lock / Unlock are menu twins → mapped through `menu_map.TWINS`), then the menu-rule files `-k step166,step101,step54,step207,step140_option,step136` 60 / 60. Menu sets total 923 → 939 / 1486, unique 785 → 801.

## Left

- Curves greyed with notices: Edit Curve Tool (curve-point manipulator), Project Tangent, Extend / Offset Curve On
  Surface (no curves on surfaces in Blender 4.5).
- Fit B-spline on curves of degree > 1 (Maya approximates within tolerance, rule [U]), CV Hardness multiplicity 1
  (soften), Align / Duplicate Surface Curves / CV Hardness / Fit B-spline / Intersect option windows (factory only).
- Lock Length under Maya's own CV manipulator is not measured (GUI drag needed).
