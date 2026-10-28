# Release notes 0.6.0 (store text)

Paste into extensions.blender.org → the listing → *Upload new version* → **Release notes** (English, short). Full list:
`CHANGELOG.md` 「0.6.0」; GitHub release notes are built from the same text. Before uploading, run the maintainer
checklist in `docs/release_checklist.md`.

---

**0.6.0 — rigging that behaves like Maya 2026** (Blender 4.5 LTS – 5.2)

Joints, IK, skinning and constraints now follow Maya 2026 (measured with mayapy), and a rig made in the kit reaches
Maya and game engines the way a Maya rig does.

Added
- Joints can be moved after placement (Move tool), and Skin > Move Skinned Joints moves a bound skeleton.
- Skinning methods Classic Linear, Dual Quaternion and Weight Blended; Bind Skin gets Maya's options.
- Spline IK Twist and Roll, constraint Interp Type, every Aim world up type.
- Four View as four real panels, each with its own shading, Show menu and camera.
- UV Shell selection in the 3D View and the UV Editor; UV Automatic keeps its history node.
- Game Exporter as a window that stays open; Rigify rigs export only their deforming joints with Maya-safe names.
- Animation layers on joints, and in-between blend shapes written as Maya blendShape in-betweens.

Changed
- Orient Joint, IK RP (default pole vector, twist), skin commands and pick walk give Maya 2026's results.
- Cylinder, Extrude and Bevel number vertices and faces like Maya; keys get Maya 2026's auto tangents.
- Step Snap is kept per tool; wrong selections print Maya's own error messages.
- Hotkeys, shelves and Graph Editor / Dope Sheet menus follow Maya 2026.

Fixed
- Shift+drag on the manipulator runs Smart Duplicate / Smart Extrude again.
- Hotbox menu-name clicks no longer run a menu item; a held Space keeps the hotbox up.
- UV Editor freezes and a crash when moving UVs on large meshes.
- Top menus not responding right after install; install error on Python 3.14 builds of Blender.
- Rigify controls keep Pose mode; Selection Highlighting can be turned off; the D pivot grabs the manipulator at once.

Upgrade
- Install over 0.5.0 as usual; shelves, hotkeys and scenes are kept. Disabling and re-enabling the extension resets
  its own preferences (Blender drops add-on preferences on disable), so note custom settings first.

Known differences
- IK RP on chains of 3 or more bones: the middle joints bend slightly differently from Maya (2-bone chains match) (#181).
- Bevelling only part of a cylinder cap rim gives a different shape from Maya (whole rims match) (#182).
- Dual Quaternion skinning with a scaled joint scales about the bone, Maya about the origin.
- Pose Space Deformation blends each pose linearly; overlapping poses differ from Maya.
- Motion path roll on 3D paths can differ from Maya by a few degrees.
- On Blender 5.1, Cycles renders Maya Ambient and Volume lights too dark; use Blender 4.5, 5.2 or EEVEE for them.
- Fixes planned for 0.7.0: Time Slider frame numbers grow with a tall timeline (#179); G does not repeat a face
  extrusion on a new selection (#184); switching back to Blender doesn't bring back a custom workspace (#185).

Thanks to everyone who reported problems after 0.5.0: @Egminator (#170), @todd-mrcool (#171), @Rickamykazy1 (#173),
@esonstyle (#174), @Kevorama (#175), @CommonDirt (#176), @ryankentpaule (#177), @GimpTOOTS (#178), @LSKianhao (#179),
@Weeliano (#183, #184) and @The-Maize (#185). Please keep reporting what breaks in real work.

Autodesk and Maya are registered trademarks or trademarks of Autodesk, Inc. This extension is not affiliated with or
endorsed by Autodesk, Inc.
