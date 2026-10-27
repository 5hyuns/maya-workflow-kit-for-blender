# Release notes 0.5.0 (store text)

Paste into extensions.blender.org → the listing → *Upload new version* → **Release notes** (English, short). Full list:
`CHANGELOG.md` 「0.5.0」; GitHub release notes are built from the same text.

---

**0.5.0 — the animation chain, Maya 2026 menus and Maya's editors** (Blender 4.5 LTS – 5.2)

Added
- Rig controls from NURBS curves: parent a curve shape to a joint, with Maya's wireframe colours.
- Constraints with several weighted targets, Set Driven Key with Maya's tangents, IK / FK switching.
- Blend shapes with in-betweens, combinations and corrective shapes; Pose Space Deformation with a Pose Editor.
- Paint Skin Weights shows weight numbers on the vertices and follows Maya 2026's tool settings.
- Rigs go to Maya and back through FBX with matching joints, skin and keys.
- Quaternion bones show Rotate X / Y / Z and key with S.
- Game Exporter clips, Motion Trail Editor, Attach to Motion Path and Flow Path Object.
- Preferences window and Hotkey Editor; Component, Shape, Connection and Reference Editors.
- More Graph Editor, animation layer, UV Editor, Curves and Deform commands; Ambient and Volume lights.
- Joints feel like Maya objects: click a joint to pick it, live Channel Box while dragging, a Paint Skin Weights
  workspace (contributed by @cnzim).

Changed
- Menus follow Maya 2026.
- Bake Simulation and the Joint Tool behave like Maya 2026.
- Renders match Maya's brightness; new scenes have Maya's startup cameras and names.

Fixed
- Snapping works again after turning Step Snap off.
- Right-click marking-menu flicks pick the right item everywhere in the view.
- Animation layer keys show in the Channel Box and Graph Editor.

Known limits
- Pose Space Deformation blends each pose linearly; overlapping poses differ from Maya.
- Motion path roll on 3D paths can differ from Maya by a few degrees.
- In-between shapes reach game engines as plain shape keys.

Thanks to @cnzim for the joint, Channel Box and weight-painting work, and to everyone who reported problems from real
work.

Autodesk and Maya are registered trademarks or trademarks of Autodesk, Inc. This extension is not affiliated with or
endorsed by Autodesk, Inc.
