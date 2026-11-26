# Release notes 0.25.0 (GitHub release)

Text for the GitHub release of v0.25.0. Full list: the 0.25.0 section of `CHANGELOG.md`.

---

**0.25.0 — UV Unfold, Delete and Duplicate Face like Maya, joints in the Hypergraph, a UV Symmetrize brush** (Blender 5.2 LTS and 5.3)

Hello everyone. This version is built almost entirely from your reports: UV Unfold, the Delete key, Edit Mesh >
Duplicate, joints that could not be shown again or picked in the Hypergraph, the startup cameras, the Ctrl+right-click
flicks and more. Thank you for every one of them.

Install it over 0.24.0 (or 0.8.0 – 0.23.0) as usual; shelves, hotkeys, scenes and the kit's settings are kept.
(Removing the kit before installing deletes them: use Export Settings first.)
Supported: Blender 5.2 LTS and 5.3. Other versions are not tested: the extension still installs on Blender 5.0 and
5.1, but they may have problems. For Blender 4.5 LTS keep using 0.6.2.

## Modeling

- **Delete key on edges and vertices (#565):** Delete / Backspace removes the selected edges and keeps their vertices,
  and removes only the selected vertices that have two edges, like Maya. Edit Mesh > Delete Edge/Vertex (Ctrl+Delete)
  cleans up only the end vertices left with two edges, so two parallel edges of one face keep both side faces (#569).
- **Edit Mesh > Duplicate (#562):** the option box opens Duplicate Face Options from every menu, and a plain click
  uses its values, so with Separate duplicated faces off the copies stay in the same mesh. Neighbouring copied faces
  stay joined, and Offset insets their outer border.
- **Extrude manipulator (#560):** the light-blue ring turns the extruded faces, and the world / local switch moves,
  turns and scales them along the world axes.
- **Multi-Cut (#574):** hold Shift while dragging a slice to keep its angle in 10 degree steps; the tool shows the
  knife pointer.
- **Fixed:** Wedge in Multi-Component mode takes the picked edge as the hinge in either pick order (#546); the
  Multi-Component pre-selection highlight shows edges and faces, not only vertices (#572); a Smart Duplicate copy
  cancelled with right-click is always taken back (#570).

## UV Editor

- **Unfold Along U / V (#557):** one click unfolds all the way along the axis, and curved shells get the same width as
  in Maya. **Modify > Unfold (#558)** on part of a shell moves only the selected UVs.
- **Symmetrize brush:** Tools > Symmetrize (also Modify > Symmetrize, the UV Toolkit and the Shift+right-click marking
  menu) mirrors UVs across a line from the mesh's symmetry edge.
- **B for soft select (#571):** tap B to toggle soft select, hold B and drag to set the falloff radius, as in the 3D
  View. Shell and texture borders stay drawn during a UV drag.
- **Fixed:** a picked vertex or edge on a shell border shows as selected on every shell that has it, so what you see
  selected is what UV commands move (#556).

## Animation and rigging

- **Hypergraph: Hierarchy shows joints (#566):** every joint is a node under its parent joint; clicking or boxing joint
  nodes picks them, and a middle-mouse drag onto a joint parents there.
- **Hide / Show on joints (#568):** H, Ctrl+H, Alt+H, Shift+H and Display > Hide / Show work on joints in Pose and
  skeleton Edit mode; Show All, Show Last Hidden and Show > Joints bring hidden joints back.
- **Time Slider (#573):** Delete / Backspace over the Time Slider delete the selection, as in the viewport, instead of
  every key of the selected object.

## Viewport and workflow

- **Startup cameras (#564):** the clip planes and persp's Focal Length show in their views; editing a startup camera
  moves its view, and moving a view moves its camera.
- **Ctrl+right-click flicks (#561):** a quick flick converts the selection however short it is.
- **Hotkey Editor (#559):** a Save button (Blender's Save Preferences) saves your hotkeys at once.
- **Opening a file (#576)** starts on the Select tool, like Maya.

## Contributors

- None this time: every change in 0.25.0 was made in this repository.

## Thank you

This version was shaped by your reports. Thank you, every one of you, for taking the time to write down what broke or felt off:

- @envwarby: UV Unfold Along not unfolding all the way (#557), Unfold moving the whole shell (#558), the Hotkey Editor
  not saving (#559), UV vertex and edge picks on shell borders (#556), Ctrl+right-click flicks failing (#561), the
  Duplicate option box (#562) and the Delete key removing too much (#565). Seven clear reports, several with videos
  that showed exactly what happened.
- @AlEuf01: joints missing from the Hypergraph (#566), clicking a joint not selecting it (#567) and hidden joints that
  could not be shown again (#568).
- @suenwaichit: B for soft select in the UV Editor (#571) and angle snapping for Multi-Cut (#574).
- @Nichosen: the startup cameras' attributes not reaching the viewport (#564).
- @Flam7e: the world / local switch for the extrude manipulator (#560).
- @dylanpearson004-coder: meshes looking different after switching between Maya and Blender mode (#563); we checked
  every object's size across the switch thanks to your report.
- @JinxSwe: the follow-up on Wedge in Multi-Component mode (#546). Thank you for coming back to it again.
- @cnzim: the video on #567 that helped us follow the joint click step by step.

Please keep telling us what breaks or feels off in real work: an issue or a Discussion post is always welcome.
