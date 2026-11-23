# Release notes 0.22.0 (GitHub release)

Text for the GitHub release of v0.22.0. Full list: the 0.22.0 section of `CHANGELOG.md`.

---

**0.22.0 — Maya hands, Blender materials and lights; UV Editor toolkit, option windows and brush tools** (Blender 5.2 LTS and 5.3)

Hello everyone. This version draws a clear line: menus, hotkeys, marking menus and the Attribute Editor layout stay
Maya's, while shaders, lights and render start values are Blender's own. Please read the first two sections before
you update, because new materials and lights behave differently from 0.21.0.

> **What changes for you after updating**
> - **New materials are Blender's Principled BSDF** with Blender's values (Assign New Material, Hypershade, shelf).
> - **No lambert1:** new objects have no material until you assign one.
> - **New lights use Blender's values**, and the Intensity row shows Blender's Power, so the number looks different.
> - **Scenes saved with an earlier version open unchanged:** nothing in them is converted.

Install it over 0.21.0 (or 0.8.0 – 0.20.1) as usual; shelves, hotkeys, scenes and the kit's settings are kept.
(Removing the kit before installing deletes them: use Export Settings first.)
Supported: Blender 5.2 LTS and 5.3. Other versions are not tested: the extension still installs on Blender 5.0 and
5.1, but they may have problems. For Blender 4.5 LTS keep using 0.6.2.

## Materials (please read)

- **One New Material.** Assign New Material (Shift+T), Assign Favorite Material, Hypershade Create > Materials, the
  Hypershade Favorites list and the shelf's Standard Surface Material button all make the same material: Blender's
  Principled BSDF with Blender's values, named Material, Material.001 and so on. The Lambert, Blinn, Phong, Phong E,
  Anisotropic and OpenPBR shelf buttons stay in place, greyed, and point to it.
- **No lambert1.** New objects have no material (Blender's grey). Use Assign New Material to give one.
- **Attribute Editor:** a material tab shows the Principled BSDF inputs by Blender's names, in the order of Blender's
  material panel. Texture connection with the map buttons works as before.
- **Ramp Shader, Layered Shader, Surface Shader and Use Background** are greyed; their tooltip and the Help Line say
  how to build the same thing in the Shader Editor.

## Lights and cameras (please read)

- **New lights have Blender's own values** (power, falloff, spot cone and penumbra, area size, directional Angle).
- **The Intensity row shows Blender's Power** (a directional light: Strength) as it is, so the number looks different
  from before. Keys on it keep working. The Decay Rate row is greyed: Blender lights fall off with distance squared.
- New cameras keep Blender's depth of field values; the layout file's image size is Blender's 1920 x 1080.

## Animation

- **Pose Breakdowner (#496):** Key > Pose Breakdowner, Relax Pose to Breakdown and Push Pose from Breakdown, right
  below Set Breakdown Key, run Blender's pose in-between tools in Pose Mode.
- **Fixed:** picking another tool (Q / W / E / R, the toolbar, the Tool Box or a menu entry) ends Skin > Move Skinned
  Joints like Maya; before, only F8 or Move Skinned Joints again did (#415).

## UV Editor

- **UV Toolkit Transform (#494, #509):** Pivot, Move by a step or to typed U / V values, Rotate, Scale and Snap of the
  selected shells, with value presets, Step Snap rows, Retain Component Spacing and Distribute U / V. The toolkit's
  buttons show a picture and their text from the left edge.
- **Option windows (#497, #502):** Unfold, Layout, Optimize, Auto Seams, Move and Sew, Merge, Stitch Together, Flip and
  the other Modify commands open their option windows.
- **Optimize (#498, #510, #511):** evens out UV distortion, with the Legacy (relax) method.
- **UV brush tools (#500, #512 – #519):** Unfold, Optimize, Cut, Sew, Pin, Smear, Smudge, Lattice, Grab and Pinch work
  on the UVs under the brush, with their brush marking menu and options.
- **Marking menus (#499, #501):** Ctrl+right-click converts the selection, Ctrl+Shift+right-click shows the active
  tool's options.
- **Stitch Together, Flip and Layout (#503, #505, #506):** Stitch Together stitches every selected border edge at once,
  Flip uses its options, Layout can spread shells over UDIM tiles.
- **Fixed:** Shift+marquee toggles what it catches, like Shift+click (#524); Convert Selection converts the selection
  (#507); the toolkit's Flip buttons use the Flip options (#520); Stitch Together on a mirrored shell (#523) and Layout
  over several tiles (#522) give Maya's result; Unitize makes every face its own shell (#526); faces picked in the 3D
  View highlight only their own UV edges (#527).

## Marking menus

- **Pictures (#525):** marking menu items show their command's picture left of the label, like Maya.
- **Fixed on Blender 5.3 (#528):** option box squares and other closed outlines (marquee and lattice frames, the
  Graph Editor scale box, the UV brush circle) draw every side.

## Older scenes

- **Nothing is converted when you open a scene.** Materials, lambert1, lights and cameras made by earlier versions
  render as they were saved. Lighting/Shading > Convert Old Kit Materials still turns older kit materials into plain
  Principled BSDF materials.

## Known differences

- The known differences listed in `CHANGELOG.md` still apply.

## Thank you

Thanks to @suenwaichit (#494), @envwarby (#524, #526, #527) and @quangvupantheravn (#495) for the UV Editor and marking menu
reports, to @cnzim for the Move Skinned Joints follow-up (#415), and to everyone for the reports and
ideas since 0.21.0. Please keep telling us what breaks or feels off in real work.

Maya Workflow Kit is a free, personal open-source project: no paid version, no donations requested, and no commercial
goal behind it.
