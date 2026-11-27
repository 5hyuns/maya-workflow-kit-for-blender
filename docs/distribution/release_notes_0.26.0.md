# Release notes 0.26.0 (GitHub release)

Text for the GitHub release of v0.26.0. Full list: the 0.26.0 section of `CHANGELOG.md`.

---

**0.26.0 — A Hypershade for Maya hands, UV soft select colours, the joint marking menu** (Blender 5.2 LTS and 5.3)

Hello everyone. This version starts on the Hypershade: Maya and Blender build materials differently, so the kit keeps
Blender's own shader nodes and gives them the Hypershade's hands — the right-click menus, Tab, the middle-mouse drag
and the Property Editor a Maya user reaches for without thinking. It also brings fixes from your reports in the UV
Editor, the shelf and Interactive Creation. Thank you for every one of them.

Install it over 0.25.0 (or 0.8.0 – 0.24.0) as usual; shelves, hotkeys, scenes and the kit's settings are kept.
(Removing the kit before installing deletes them: use Export Settings first.)
Supported: Blender 5.2 LTS and 5.3. Other versions are not tested: the extension still installs on Blender 5.0 and
5.1, but they may have problems. For Blender 4.5 LTS keep using 0.6.2.

## Hypershade

- **Right-click node menus:** in the graph, a right-click opens the marking menu for what is under the mouse (empty
  graph, material, texture, utility node or the Material Output), with Inputs / Outputs lists and commands that act on
  that node. Entries Blender has no counterpart for are greyed with a note on what to use instead.
- **Tab to create a node, 1 - 4 and stream keys:** type a node name where the mouse is; 1 - 4 collapse or show sockets,
  , . / select along the stream, = and - zoom.
- **Middle-mouse drag to connect:** drop a node on another to pick the input from a list; Ctrl+middle-mouse makes the
  default connection at once.
- **Browser swatch menu:** a right-click on a material swatch lists Assign Material To Viewport Selection, Select
  Objects with Material, Graph Network, Rename and the rest of the swatch menu.
- **Property Editor follows the Graph:** a picked texture or utility node shows its own settings. File and Checker
  from the map button come with a place2dTexture (Repeat UV and Offset), and the map button of a connected attribute
  goes to the connected node.
- **Create: a Blender section (#577):** every Blender shader node by Blender's names, next to the Maya section; a
  shader click makes a new material with it.

## UV Editor

- **Soft select colours (#579):** with soft select on, the UVs a UV Move / Rotate / Scale will move are coloured from
  yellow to black across the falloff radius, and follow a drag.
- **Fixed:** a single click on UVs, edges or faces (plain, Shift, Ctrl+Shift or Ctrl) moves the manipulator to the
  picked components at once, not only a marquee selection (#579, #582).

## Modeling and workflow

- **Joint marking menu (#578):** a right-click on a joint opens Set / Assume Preferred Angle, Edit Joints and Select /
  Select Hierarchy.
- **Fixed:** Shelf Editor Create buttons work in component mode and leave it for object mode, like the menu (#583);
  Delete History while Interactive Creation waits for the height keeps the shape instead of scaling it to 0, and
  another tool finishes it (#577); the option box of Reverse Surfaces, Add Divisions, Average Vertices, Poke, Edit
  Edge Flow and Quadrangulate runs on the whole mesh in object mode (#580).

## Contributors

- None this time: every change in 0.26.0 was made in this repository.

## Thank you

Thank you, truly. Every fix in this version started with someone who took the time to report a problem or share an
idea, and the kit only gets closer to Maya because you tell us where it falls short. Thank you, every one of you:

- @envwarby: the UV manipulator staying put after a single click (#582) and Create not working in component mode
  (#583), both with videos that showed exactly what happened, and many more reports we are still working on.
- @suenwaichit: soft select colours in the UV Editor and the pivot not jumping to the picked UVs (#579), with a video.
- @xishan2126: how far the Hypershade is from Maya's, and the shape scaling to 0 after the History clear button (#577).
  The Hypershade work in this version started from your report.

There is still a lot to improve, and your reports are what move it forward. Please keep telling us what breaks or
feels off in real work: an issue or a Discussion post is always welcome, and every one is read with thanks.
