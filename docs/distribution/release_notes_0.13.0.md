# Release notes 0.13.0 (GitHub release)

Text for the GitHub release of v0.13.0. Full list: the 0.13.0 section of `CHANGELOG.md`.

---

**0.13.0 — Smart Bevel, modular Graph Editor windows, Connect Tool, Universal Manipulator on components, and the fixes from your reports** (Blender 5.2 LTS)

Install it over 0.12.0 (or 0.8.0 – 0.11.0) as usual; shelves, hotkeys, scenes and the kit's settings are kept.
(Removing the kit before installing deletes them: use Export Settings first.)
Supported: Blender 5.2 LTS. Other versions are not tested: the extension still installs on Blender 5.0 and 5.1,
but they may have problems. For Blender 4.5 LTS keep using 0.6.2.

## New

- Edit Mesh > Smart Bevel, Maya 2027's bevel: a width in scene units kept below what the edges around allow, edge
  filters (Selected / Hard / by Angle), border edges set hard, smoothing angle and arc welding, as an editable
  polySmartBevel node with a Width arrow; also in the Modeling Toolkit and the Shift+RMB menus (#303).
- Universal Manipulator on components: Ctrl+T in a component mode puts the box around the selected vertices, edges or
  faces; corners scale, edge arrows rotate, the centre moves, a typed length sets the size (#318).
- Modular editor windows: the Graph Editor, Dope Sheet and UV Editor panes have a Panels menu with Tear Off / Tear Off
  Copy, and a floating editor window docks back at the bottom, left, right or top of the viewport (#319).
- Skeleton > HumanIK leads to Rigify: meta-rig, Generate Rig, rig settings, bone rig type and rig controls (#319).
- Connect Tool: Mesh Tools > Connect is interactive, with Slide / Segments / Pinch, a middle-drag that re-does the
  last connection and Maya's selection rules (#322).
- Edit Mesh > Transform as an editable node, Extrude along a selected curve, edge extrusion that keeps connected
  edges together, Insert Knot that keeps the curve's shape, UDIM grid option, Light Linking editors (#321).
- Booleans keep construction history and Delete takes a result's hidden inputs with it (#324).
- Panel toolbar camera list (every camera, New Perspective / Orthographic, Stereo Cameras) and Alt+LMB+MMB dolly
  (#325).
- Constraint target weights are Channel Box channels you can select and key (#329).
- Joint Size in Metre Scenes preference (#328); Radius to Hierarchy and B-Bone / Envelope bone display (#320).
- Search and Replace Names takes $ and ^ like Maya; Grow / Shrink Selection on non-US keyboards and in the UV Editor
  (#322).
- Selection highlight (green lead, white others) in Rendered shading (#330).
- T shows the last extrude / bevel manipulator and In-View Editor (#327).

## Fixed

- Channel Box clicks respond at once: only the editors that show the channels redraw (#316).
- Outliner h hides exactly the picked rows (#322); a box over rig controls picks every control in it (#323).
- Edge bevels in centimetre scenes keep their edges (#321); a 3-segment bevel shades its strips alike (#331).
- Marking menus: a radial submenu goes back to its parent menu (#332); G after Ctrl+G groups again (#333); a kit
  window is not written to disk while it is dragged (#334); a joint Radius confirmed with Enter redraws at once (#320).

## Known differences

- Smart Bevel is this kit's bevel geometry with Maya 2027's options: Cutback Relaxation and Remove Isolated Arcs are
  not available, and Depth works like Bevel's Depth (1 round, 0 flat, -1 concave).
- The Universal Manipulator on components goes beyond Maya, which shows no manipulator for a component selection.
- The known differences listed in `CHANGELOG.md` still apply.

## Thank you

Thanks for the reports and ideas: @tutulk (#303), @DAI3rd (#316), @swarnava05 (#319), @AlEuf01 (#320), @Olivier-bit
(#321), @river5300 (#322), @ArcticZA (#323, #329), @purple-movies (#324), @mfjooste (#325), @psokk (#327), @zzador
(#328), @GIBBETGAMES (#330, #331, #333, #334) and @haithamcolorcolor-spec (#332). Please keep telling us what breaks
or feels off in real work.

Maya Workflow Kit is a free, personal open-source project: no paid version, no donations requested, and no commercial
goal behind it.

Autodesk and Maya are registered trademarks or trademarks of Autodesk, Inc. This extension is not affiliated with or
endorsed by Autodesk, Inc.
