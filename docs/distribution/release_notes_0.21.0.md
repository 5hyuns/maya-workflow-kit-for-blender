# Release notes 0.21.0 (GitHub release)

Text for the GitHub release of v0.21.0. Full list: the 0.21.0 section of `CHANGELOG.md`.

---

**0.21.0 — plain Blender materials, Maya nonlinear deformers, reworked UV tools, Selection Constraint: Angle and edge-sliding Rotate / Scale** (Blender 5.2 LTS and 5.3)

Hello everyone, and thank you for the reports since 0.20.1. This version changes how new materials are made (please
read the first section), makes the nonlinear deformers and many UV tools work like Maya, and fixes a long list of
smaller differences.

Install it over 0.20.1 (or 0.8.0 – 0.20.0) as usual; shelves, hotkeys, scenes and the kit's settings are kept.
(Removing the kit before installing deletes them: use Export Settings first.)
Supported: Blender 5.2 LTS and 5.3. Other versions are not tested: the extension still installs on Blender 5.0 and
5.1, but they may have problems. For Blender 4.5 LTS keep using 0.6.2.

## Materials: plain Blender materials (please read)

- **New materials are plain Principled BSDF materials** with Blender's own values: shelf buttons, Assign New
  Material, Assign Favorite Material, the Hypershade and the lambert1 every new object gets. They look the same in
  Eevee and Cycles as any Blender material and export to FBX, glTF and USD with their colour and textures. Lambert,
  Blinn, Phong, Standard Surface and the other kinds give the material its Maya name, labels and Attribute Editor
  layout; a texture connected to Color goes straight to Base Color.
- **Your saved scenes render as before.** Nothing is converted when you open them. To turn their kit materials into
  plain Principled materials, use **Lighting/Shading > Convert Old Kit Materials** once. A texture on Color then
  shows a little brighter, because Blender's Base Color has no extra diffuse factor.
- Ramp Shader, Layered Shader and Use Background keep their extra nodes, and Surface Shader its glow, for now.

## Deformers

- **Twist, Squash, Flare, Sine and Wave (#457, #461, #493):** deform like Maya in the handle's space on meshes,
  curves, lattices and NURBS surfaces, with the deformers' own attributes in the Channel Box and the Attribute
  Editor. Squash has Start Smoothness and End Smoothness (#492).

## Modeling

- **Rotate and Scale tools (#429):** Ctrl+Shift+drag keeps every vertex sliding along one of its own edges, like Maya.
- **Selection Constraint: Angle (#435):** in the Modeling Toolkit and the tool option menus; one click picks a flat or
  gently curved patch.
- **Selection (#438, #445, #455, #456):** the edge marquee picks every edge it touches, Symmetry selects the mirror
  partners of clicks, marquees and lassos, and Grow / Shrink and To Edge Loop on borders follow Maya's rules.
- **Edge loops and flow (#466, #491):** Edit Edge Flow keeps a border-to-border loop on the surface, and Insert / Offset
  Edge Loop with edge flow put the new loop on the same curve.
- **Also fixed:** Circularize on faces (#465), Fill Hole with one border edge (#463), Extrude along a curve (#444, #490),
  Ungroup (#464, #478), polygon primitives' Height Baseline and Create UVs (#480), creation node axes (#454), option
  window axes (#443), and edit mode no longer stalls on a dense mesh (#452).

## UV

- **Sew UV Edges, Move and Sew, Unfold and Layout (#483 – #486):** shells stay in place when sewn, cuts inside a shell
  are kept, and Layout keeps the shells' orientation with one texel density.
- **Planar, Cylindrical, Spherical and Automatic (#439, #440, #442, #487, #488):** projections follow the scene axes and
  the selection like Maya, and Automatic groups faces into shells like Maya.
- **3D Grab UV Tool (#434)** no longer raises an error over the 3D View.

## Animation and the Channel Box

- **Keys and tangents (#467, #469, #471, #472, #476):** Linear tangents and Linear infinity follow Maya, locked
  channels are not keyed, Paste Keys Insert with Copies and Bake Simulation tangents are fixed.
- **Channel Box and Attribute Editor (#477, #481, #482):** renaming cleans up the typed name, cameras and lights show
  Maya's SHAPES rows, and Film Aperture is in inches.
- **Cameras and lights (#468, #479):** new cameras and directional lights start like Maya's.
- **Image planes (#436):** Alpha Gain, Display Mode and Image Name in the Attribute Editor.
- **Playback (#344):** idle viewport drawings and frame updates do less on every frame.

## Rigging

- **Skinning (#459, #460, #462):** Bind Skin to selected joints and Copy Skin Weights are fixed.
- **Aim / Up vectors and Motion Paths (#453)** read the node's own axes; Show > Joints off keeps curve-shape controls
  (#451).

## Layout and windows

- **Maya layout panels (#458):** a switch to Blender and back, or a file reopen, keeps the viewport panels and their
  display settings.
- **Tool Box, Status Line, Help Line (#437, #447, #448):** hiding them closes their row or column cleanly.
- **Also fixed:** Frame Selected on several objects frames them as closely as Maya (#473), kit editor windows come to the front when asked again (#450), the Marking Menu Editor's shelf
  buttons (#446), the Shelf Editor's Python command (#441), another add-on's timeline header (#449), and macOS Cmd
  for the kit's Ctrl keys (#432).

## Known differences

- The known differences listed in `CHANGELOG.md` still apply.

## Thank you

Thanks to @pixelkeyblade18 (#344), @suenwaichit (#435), @Kill-butterfly (#436), @invader-zimm (#437), @envwarby
(#438 – #441), @magmastk (#452) and @JinxSwe (#458) for reports that showed what to fix. Please keep telling us what
breaks or feels off in real work.

Maya Workflow Kit is a free, personal open-source project: no paid version, no donations requested, and no commercial
goal behind it.
