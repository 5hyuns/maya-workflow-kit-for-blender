# Release notes 0.20.1 (GitHub release)

Text for the GitHub release of v0.20.1. Full list: the 0.20.1 section of `CHANGELOG.md`.

---

**0.20.1 — FBX rigs, floating panels, Multi-Cut with Symmetry, Connect Tool segments, Extrude curve options and face Isolate Select** (Blender 5.2 LTS and 5.3)

Hello everyone, and thank you for the quick reports after 0.20.0. This update fixes what you ran into first and
adds a few Maya options you asked for.

Install it over 0.20.0 (or 0.8.0 – 0.19.0) as usual; shelves, hotkeys, scenes and the kit's settings are kept.
(Removing the kit before installing deletes them: use Export Settings first.)
Supported: Blender 5.2 LTS and 5.3. Other versions are not tested: the extension still installs on Blender 5.0 and
5.1, but they may have problems. For Blender 4.5 LTS keep using 0.6.2.

## Modeling

- **Multi-Cut with Symmetry (#420):** with Object, World or Topology symmetry on, cuts, Ctrl+click edge loops and
  slices are made on both sides of the mesh, and the preview shows the mirrored side too.
- **Connect Tool (#421):** typing Segments, Slide or Pinch in the tool's options redoes the connection it just made,
  like Maya. The Modeling Toolkit's Connect button opens the Connect Tool with its Connect Options.
- **Extrude (#418, #424):** the Extrude option box has Maya's Curve rows (Curve: None / Selected / Generated, Taper,
  Twist). Curve: Generated makes a straight path along the faces' normal, so a straight extrusion can taper and
  twist. An extrusion along a curve now also uses Offset, Thickness and Keep Faces Together from the option box, and
  with two curves selected the first one picked is the path, like Maya.
- **Isolate Select with faces (#427):** Ctrl+1 with faces selected shows only those faces (with vertices or edges,
  the faces around them), like Maya. Show > Isolate Select gets Add / Remove Selected Objects. Your own hidden faces
  stay hidden when you leave it.
- **Isolate Select in the four view (#422):** each panel keeps its own isolation when you switch between one view and
  four views. A marquee or lasso in an isolated view now replaces the whole selection, so hidden objects no longer
  stay selected, and on macOS Cmd+1 is Isolate Select too.
- **Rotate and Scale tools (#430):** Ctrl+middle-drag on mesh components turns each group of connected components
  about its own normal, or scales it across its normal, like Maya.

## Rigging

- **FBX import (#416):** File > Import with Maya Units and Axes keeps the rest skeleton of rigs whose bones are
  connected (for example auto-rigged characters), so the pose is clean at the bind pose.
- **Move Skinned Joints (#415):** clicking empty space, a joint's wire or the Move handle behaves as expected in every
  viewport layout and keyboard preset, Undo / Redo steps the joint selection, and the tool stays on until you choose
  another one, like Maya. Thanks to @cnzim for this fix.

## Windows and other add-ons

- **Floating panels (#417):** a floating Tool Settings, Channel Box, Attribute Editor or Modeling Toolkit that went
  behind the main window comes back to the front, at the same place, when you ask for it again (Windows menu,
  Ctrl+A, a tool's option box).
- **Next to other workflow add-ons (#423, #425, #426):** Maya mode starts and stops cleanly next to an add-on that
  changes the 3D View sidebar or the editor headers (for example Blenda 4D), and leaves that add-on's layouts and
  headers as they were.
- **Keep Blender Keys (#226):** a new add-on preference (off by default) keeps Tab (Object / Edit Mode) and Alt+E
  (Local View) as Blender keys next to the Maya keys in the 3D View. Thanks to @scoegrams for the idea.
- **More Maya menu items (#108):** Visualize > Create Turntable, Control Vertex and Surface Border selection for curves
  and surfaces, the Shape Editor's Rebuild Target, Delete All by Type > Sounds and Windows > Home now run.

## Known differences

- The known differences listed in `CHANGELOG.md` still apply.

## Thank you

Thanks to @cnzim (#415) for the pull request, and to @Darkkanji (#416), @lucafrancescoorlandi (#417, #418),
@invaderzod (#419, #420), @suenwaichit (#421), @cookies908 (#422), @NevilArt (#423) and @ganesh2004jadhav-boop (#428)
for reports that showed what to fix, and to @scoegrams (#226) for the Keep Blender Keys idea. Please keep telling us what breaks or feels off in real work.

Maya Workflow Kit is a free, personal open-source project: no paid version, no donations requested, and no commercial
goal behind it.
