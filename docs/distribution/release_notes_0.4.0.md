# Release notes 0.4.0 (store text)

Paste into extensions.blender.org → the listing → *Upload new version* → **Release notes** (English, short). Full list:
`CHANGELOG.md` 「0.4.0」; GitHub release notes are built from the same text.

---

**0.4.0 — modeling, deformers, UVs and animation tools** (Blender 4.5 LTS – 5.2)

Added
- Maya-style Quad Draw, Create Polygon, Append to Polygon, Insert / Offset Edge Loop and Slide Edge tools.
- Deform menu with Maya-like deformers (Lattice, Wrap, Delta Mush, ShrinkWrap, Nonlinear, Cluster, Soft Modification,
  Wire and more), their option windows, Channel Box attributes and Paint Weights; export / import deformer weights.
- UV Editor shell tools (Stack, Orient, Snap, Distribute, Normalize, Move and Sew ...) and display keys.
- Curve tools: CV / EP Curve Tool, arcs, Rebuild, Attach, Detach, Cut, Fillet, Straighten, Move Seam.
- Maya's factory workspaces and Reset Current Workspace.
- Animation Snapshot and ghosting (Ghost Selected, Ghosting Editor).
- Maya's default light, Render Sequence / Batch Render windows, Test Resolution, Grid options.
- Joint labelling, Smooth Mesh Preview to Polygons, Align Tool, Ctrl+Shift+click a menu item onto the shelf.

Changed
- Option boxes (❒) open with one click.
- One undo step per Maya command; no Blender redo panel popping up.
- Channel Box: Maya's right-click menus everywhere in it, rows that fit the narrow dock, Maya numbers and names.
- Graph Editor in Maya terms: channel names, key commands, selection modifiers (also Dope Sheet, UV Editor, Outliner).
- Marking menus have Maya's size; manipulators show no Blender tooltips; messages go to the Command Line.
- Hiding, deleting or exporting a parent takes its children, like Maya.

Fixed
- The selection wire now follows skinned and simulated meshes while playing.
- A new cube after Delete is named pCube1 again.
- Paint Skin Weights options on Blender 5.x.

Thanks to everyone who reported problems from real work.

Autodesk and Maya are registered trademarks or trademarks of Autodesk, Inc. This extension is not affiliated with or
endorsed by Autodesk, Inc.
