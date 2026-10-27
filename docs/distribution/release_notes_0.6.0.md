# Release notes 0.6.0 (store text)

Paste into extensions.blender.org → the listing → *Upload new version* → **Release notes** (English, short). Full list:
`CHANGELOG.md` 「0.6.0」; GitHub release notes are built from the same text. Before uploading, run the maintainer
checklist in `docs/release_checklist.md`.

---

**0.6.0 — rigs that reach the engine like Maya's** (Blender 4.5 LTS – 5.2)

Added
- Four View as four real panels, each with its own shading, Show menu and camera; Space toggles, and it survives
  save / open.
- Animation layers on joints: key joints on a layer with S, and Bake Simulation keeps the result.
- Rigify rigs export with only the deforming joints and Maya-safe names; pick walk follows the Rigify controls.
- In-between blend shapes reach Maya and game engines as Maya blendShape in-betweens.

Changed
- Game Exporter clips are written as separate takes with Maya scale and their own ranges.
- Orient Joint / Mirror Joints run on a plain click (❒ opens the options); FBX joints carry Maya's joint orient.
- Constraints on child joints move the joint like Maya.
- Importing a kit FBX puts skinned meshes where they were and sets the Time Slider to the file's range.
- Enable IK Solver shows its check mark; Paint Skin Weights starts on the first joint of the hierarchy.

Fixed
- Bevel on a cylinder cap rim has Maya's width.
- Delete History also removes the kit's Extrude and Bevel history.
- Values typed in the Set Driven Key window are kept until Key.

Known limits
- Pose Space Deformation blends each pose linearly; overlapping poses differ from Maya.
- Motion path roll on 3D paths can differ from Maya by a few degrees.
- On Blender 5.1, Cycles renders Maya Ambient and Volume lights too dark; use Blender 4.5, 5.2 or EEVEE for them.

Thanks to the testers whose reports shaped this cycle: @Jimejime-cc (snapping, extrude), @sporksalot (option boxes,
UI reset), @kubilaykilinc (edge loop selection), @shibberd (Blender 5.2) — and to @cnzim for the joint and weight
painting work. No new issues were opened after 0.5.0; please keep reporting what breaks in real work.

Autodesk and Maya are registered trademarks or trademarks of Autodesk, Inc. This extension is not affiliated with or
endorsed by Autodesk, Inc.
