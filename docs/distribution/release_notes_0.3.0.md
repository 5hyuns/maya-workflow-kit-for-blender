# Release notes 0.3.0 (store text)

Paste into extensions.blender.org → the listing → *Upload new version* → **Release notes** (English, short). Full list:
`CHANGELOG.md` 「0.3.0」; GitHub release notes are built from the same text.

---

**0.3.0 — closer to Maya** (Blender 4.5 LTS – 5.2)

Changed
- The viewport looks like Maya without any theme: green / white selection, Maya component and grid colours, Maya
  manipulator colours, dark-blue wireframe, smooth Smooth Mesh Preview.
- The dock works like Maya's: vertical tabs on its edge, as narrow as Maya's with the Channel Box up, INPUTS collapsed,
  Layer Editor always visible.
- 26 more Maya option windows with Maya's own fields and defaults — joints, IK, skinning, blend shapes, constraints,
  key editing (Scale Keys is new), Parent, Connect, Circularize, Duplicate Special and more. Aim aims along +X like Maya.
- Edit Mesh Connect, Merge, Symmetrize, Smooth and Bevel give Maya's results; Bevel and edge / vertex Extrude act at
  once and stay editable.
- Ctrl+A opens the Attribute Editor / Channel Box in every mode; more Select and Ctrl+RMB conversions (along loop,
  perimeters, face path, UVs); Alt+RMB dolly in the UV Editor.
- New Scene asks to save; opened files come up in the Maya layout; tool settings survive New / Open; FBX, OBJ,
  Alembic and USD round trips keep Maya's axes, scale and names.
- Graph Editor shows centimetres; Render Current Frame works in a new scene; Maya material and light defaults.
- Marking menus stay inside the window and grey out far fewer items; the menu bar folds into » at 150 % UI scale;
  hundreds more Maya menu icons.

Fixed
- Maya mode could fail to switch on when another add-on was installed.
- Double-click edge loop selection error in Blender 5.1 / 5.2.
- Faces could not be moved right after Extrude; F12 left UV sync on.

Thanks to everyone who reported problems from real work.

Autodesk and Maya are registered trademarks or trademarks of Autodesk, Inc. This extension is not affiliated with or
endorsed by Autodesk, Inc.
