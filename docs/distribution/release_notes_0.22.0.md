# Release notes 0.22.0 (GitHub release)

Text for the GitHub release of v0.22.0. Full list: the 0.22.0 section of `CHANGELOG.md`.

---

**0.22.0 — Maya hands, Blender materials and lights: one New Material, no lambert1, Blender's light power** (Blender 5.2 LTS and 5.3)

Hello everyone. This version draws a clear line: menus, hotkeys, marking menus and the Attribute Editor layout stay
Maya's, while shaders, lights and render start values are Blender's own. Please read the first two sections before
you update, because new materials and lights behave differently from 0.21.0.

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

## Older scenes

- **Nothing is converted when you open a scene.** Materials, lambert1, lights and cameras made by earlier versions
  render as they were saved. Lighting/Shading > Convert Old Kit Materials still turns older kit materials into plain
  Principled BSDF materials.

## Known differences

- The known differences listed in `CHANGELOG.md` still apply.

## Thank you

Thank you for the reports and ideas since 0.21.0. Please keep telling us what breaks or feels off in real work.

Maya Workflow Kit is a free, personal open-source project: no paid version, no donations requested, and no commercial
goal behind it.
