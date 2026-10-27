# Maintainer release checklist (30 minutes)

Run before publishing a release, after the automated QA (`tools/qa/`, `tools/release_check.py`, `tools/dogfood.py`).
Use a sandbox Blender config (the `BLENDER_USER_*` block at the top of `docs/manual_checks.md` — never the real
`%APPDATA%` config), install the new zip by **drag and drop**, and keep Maya 2026 open next to it.

Mark each line ✔ / ✘ with a one-line note. Any ✘ that is a **crash, data loss or enable failure** holds the release.

- [ ] (2 min) Install → Make Maya → restart: no error popup or console traceback; menu bar, shelf and Channel Box show.
- [ ] (3 min) Install over a config that used the previous release (update): my shelf, hotkeys and preferences are kept.
- [ ] (3 min) Hand memory: Alt+LMB / MMB / RMB navigation, Q/W/E/R, Space hotbox, Shift+RMB marking menu, F / A
      framing, 4 / 5 / 6 shading — feels like Maya.
- [ ] (3 min) **Toggles Off → On → Off → On**: Snap to Grid, Step Snap, Soft Select, Symmetry in changing orders; check
      each time with a real Move that the icon matches what happens (#139).
- [ ] (4 min) Rig line: 3 joints → Orient Joint → Bind Skin → Paint Skin Weights briefly → Q to leave → control curve →
      Parent Constraint. Ctrl+Z and Shift+Z after each step.
- [ ] (3 min) Animation: 3 keys, add an animation layer and key on it → Bake Simulation → values are not doubled.
- [ ] (3 min) Game Exporter FBX → open in Maya 2026: scale in cm, joint orientation, number of clip takes.
- [ ] (2 min) Four View ↔ Single (Space tap) round trip, save → reopen → the four panels keep their settings.
- [ ] (2 min) Maya ↔ Blender switch twice: the Blender side looks like factory Blender, back in Maya everything returns.
- [ ] (2 min) Two or three add-ons I normally use enabled (Rigify included) while repeating some of the above.
- [ ] (2 min) Open a .blend saved with the previous release: no errors, the rig works.
- [ ] (1 min) The release notes' "Known limits" match what actually happens (for example Blender 5.1 Cycles Ambient).

Release candidate: put the zip on a separate beta channel (GitHub pre-release or a `tools/build_repo.py` repository)
for 3–7 days; ship when no crash / data-loss report came in.
