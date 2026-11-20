# Release notes 0.20.0 (GitHub release)

Text for the GitHub release of v0.20.0. Full list: the 0.20.0 section of `CHANGELOG.md`.

---

**0.20.0 — marking menus and the Move tool closer to Maya, UV Unfold, Layout, Straighten Shell and Camera-based fixed, easier Paint Skin Weights, and Maya's Image Plane menus** (Blender 5.2 LTS and 5.3)

Hello everyone, and thank you for the reports. This release is mostly made of them: marking menus now pick,
open submenus and run quick marks the way Maya does, the Move tool gets Maya's Ctrl, slide and along-normal drags,
the UV tools keep your selection and Straighten Shell and Camera-based work, and Paint Skin Weights is easier to
use on a posed skin.

Install it over 0.19.0 (or 0.8.0 – 0.18.0) as usual; shelves, hotkeys, scenes and the kit's settings are kept.
(Removing the kit before installing deletes them: use Export Settings first.)
Supported: Blender 5.2 LTS and 5.3. Other versions are not tested: the extension still installs on Blender 5.0 and
5.1, but they may have problems. For Blender 4.5 LTS keep using 0.6.2. Versions after 5.3 are not offered the
extension until they are tested.

## Marking menus

- **Reaching every item (#387):** a radial submenu opens when the pointer rests on it for a moment, like Maya; a
  stroke that keeps moving goes over it, so list rows beyond it can be reached (Ctrl+RMB: To Shell under To Faces).
  A rest opens the highlighted submenu when its box lies on the way from the centre to the pointer (#412).
- **Which item is highlighted:** off the item boxes, the highlighted item is the one whose box lies nearest the
  pointer's direction (#406), and the centre where nothing is highlighted is 10 px, like Maya (#411).
- **Quick marks (#406):** a stroke released soon after the press runs the item of its direction, never the list row it ends
  on; a release within 0.1 s of the press runs nothing, like Maya (#414). A quick click in the centre still keeps
  the menu up.
- In Isolate Select, RMB on an object seen through a hole in another opens the marking menu for the object you see
  (#395).

## Move tool

- **Ctrl+drag (#383):** Ctrl+drag on an axis arrow moves in the plane of the other two axes, like Maya; on the
  Extrude manipulator Ctrl+drag works the same way and on a scale cube scales the other two axes. Ctrl+drag along
  the axis with grid snapping is now the preference "Ctrl+Drag on a Move Axis Snaps", off by default.
- **Slide (#391, #410):** in component mode, Ctrl+Shift+drag on a handle slides the selected components along their
  edges, with a "slide" label under the mouse for the whole drag.
- **Along normals (#394):** in component mode, Ctrl+middle-drag moves the selected components along their normals.

## UV

- **Unfold and Layout** keep the mesh and UV selection, with UV Sync Selection on or off and with several meshes in
  edit mode (#404).
- **Straighten Shell (#393, #413)** straightens the selected UV edge loop along U or V and unfolds the rest of its
  shell around it, so a ribbon shell becomes a straight strip.
- **Camera-based (#392)** maps a selected object from the 3D View in object mode, and also works from a separate UV
  Editor window.

## Skin and Paint Skin Weights

- **A posed skin keeps its pose in component mode (#397, #407):** components, colours and preselection stay on the
  posed mesh, also for skins bound before or by Blender's own tools and with every Normalize Weights mode. Paint Skin
  Weights shows its wireframe the first time on a mesh, and opening it again after Select mode stays in the tool
  (#405).
- **F frames the selected vertices (#399)** where the posed mesh shows them.
- **Lasso select (#401):** Select mode selects vertices with a box or a lasso (Tool Settings > Brush > Select).
- **Mirror Skin Weights Options (#402):** the option box opens its window (Mirror across, Direction, Influence
  Association, Normalize), so -X onto +X works too.

## Image planes

- **Image Plane button (#398):** the viewport panel toolbar's Image Plane button picks an image file and makes an image
  plane facing that view, or in front of the camera a camera view looks through.
- **Menus (#409):** View > Image Plane (Import Image..., Import Movie..., Image Plane Attributes) and a right-click
  menu on the Image Plane button (Import Image..., Display Mode None / RGBA, Delete), like Maya.

## Other fixes

- **Average Vertices (#396)** rounds the selected vertices at once instead of waiting for a drag, with its
  Iterations editable afterwards.
- **Quad Draw (#389):** a Shift+drag relax no longer pulls the mesh's far side through to the front.
- An object-mode click no longer stops on a "'NoneType' object" error with an empty curve or one whose Geometry Nodes
  output is only instances (#390).
- **Hotkey Editor (#386):** every keyboard key Blender has can be assigned, including the "<" key of German and other
  European keyboards.
- **Option boxes (#403):** a command whose settings are its own (Edit Mesh > Add Divisions, Skin > Smooth Skin
  Weights and others) shows them on a click of its option box.
- **Translations (#408):** every option window shows its texts in Japanese and Chinese (Simplified / Traditional).

## Known differences

- The known differences listed in `CHANGELOG.md` still apply.

## Thank you

Thanks to @AlEuf01 (#397, #399, #401, #402), @envwarby (#383, #386), @GUYVERZERO (#395, #396), @JinxSwe (#398),
@leo2ard (#387), @magmastk (#390), @PucaJam (#389) and @suenwaichit (#391, #392, #393, #394) for reports that showed
what to fix. Please keep telling us what breaks or feels off in real work.

Maya Workflow Kit is a free, personal open-source project: no paid version, no donations requested, and no commercial
goal behind it.
