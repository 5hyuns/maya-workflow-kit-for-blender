# Release notes 0.14.0 (GitHub release)

Text for the GitHub release of v0.14.0. Full list: the 0.14.0 section of `CHANGELOG.md`.

---

**0.14.0 — Shelf Editor, In-View Editor middle drag, Transform Component rotate ring, T in object mode, and the fixes from your reports** (Blender 5.2 LTS)

Install it over 0.13.0 (or 0.8.0 – 0.12.0) as usual; shelves, hotkeys, scenes and the kit's settings are kept.
(Removing the kit before installing deletes them: use Export Settings first.)
Supported: Blender 5.2 LTS. Other versions are not tested: the extension still installs on Blender 5.0 and 5.1,
but they may have problems. For Blender 4.5 LTS keep using 0.6.2.

## New

- Windows > Settings/Preferences > Shelf Editor: add, rename, reorder and delete shelves and buttons, and edit a
  button's label, icon, tooltip and command; changes stay a draft until Save (from @LoongVeeng, #310).
- In-View Editor: a plain middle drag anywhere in the view changes the yellow row, and a middle click picks a row
  without changing it. New options in Preferences, all off: a drag-speed control in the In-View Editor's title, moving
  the In-View Editor by its title, and the marking menu's Quick Gestures and Submenu Return Ring (from @LoongVeeng,
  #301).
- Edit Mesh > Transform (Transform Component) has the rotate ring and the world / local switch on its manipulator
  (#321).
- T in object mode stays in object mode and shows the newest input node's manipulator and In-View Editor, a
  primitive's creation node included; the node picked in Channel Box INPUTS wins (#327).
- Time Slider shows exactly the playback range, the Range Slider row fits short timelines without a scrollbar, and
  Playblast brings its player to the front (#319).

## Fixed

- Keyed constraint target weights drive the constraint while you scrub, on objects and joints; S keys the open
  constraint's weights, also with the mouse over the Channel Box or another panel. One target follows any weight
  above 0 and 0 leaves the node on its own channels; with two or more targets, every weight 0 puts the node back on
  its own place, like Maya (#329).
- Modify > Match Transformations takes the last picked node as the source, rig controls included (#338).
- Mesh > Fill Hole closes the selected border loops, and Bridge closes a single border loop with one face (#337).

## Known differences

- In-View Editor: a middle drag changes values more slowly than Maya's, and the editor sits beside its object rather
  than at a fixed place in the view.
- The known differences listed in `CHANGELOG.md` still apply.

## Thank you

Thanks to @LoongVeeng for the Shelf Editor and the In-View Editor / marking menu work (#310, #301), and for the
reports and ideas: @swarnava05 (#319), @Olivier-bit (#321), @psokk (#327), @ArcticZA (#329, #338) and @GUYVERZERO
(#337). Please keep telling us what breaks or feels off in real work.

Maya Workflow Kit is a free, personal open-source project: no paid version, no donations requested, and no commercial
goal behind it.
