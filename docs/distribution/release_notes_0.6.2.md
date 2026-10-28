# Release notes 0.6.2 (GitHub release)

Text for the GitHub release of v0.6.2. Full list: `CHANGELOG.md` 「0.6.2」. Before publishing, run the maintainer
checklist in `docs/release_checklist.md`.

---

**0.6.2 — G after an extrude, switching back to Blender, and a few things from your reports** (Blender 4.5 LTS – 5.2)

Install it over 0.6.1, 0.6.0 or 0.5.0 as usual; shelves, hotkeys and scenes are kept.

Fixed
- G after an extrude: drag the extrude manipulator, select another face, press G, and it extrudes the new face like
  Maya. Before, G rebuilt the first extrusion (#184).
- Switching back to Blender after starting in the Maya layout brings back your own workspaces and shows the one you
  had open, with no restart. Your startup file is only read, never written (#185).
- A taller Time Slider looks like Maya's: frame numbers stay at the top in their normal size, ticks grow only in the
  lower part, and the current frame number stays at the bottom (#190).
- Attribute Editor sections: an open section draws its controls in a framed area under the section arrow, so the
  hierarchy is easy to read (#194).

Added
- Shift+drag on the Move / Rotate / Scale manipulator now extrudes selected vertices too, and the new vertices move
  with the drag. Faces and edges already worked (#183).
- Quad Draw: hold Tab and drag a border vertex in an inner corner to fill that corner with a quad. A preview shows
  the new edges while you drag (#180).
- Panels > Perspective > New makes persp1, persp2 … with the settings and starting place of the scene's persp camera,
  looks through it in that panel and lists it in the menu. One undo takes it back (#193).

The known differences listed in `CHANGELOG.md` still apply.

## Thank you

@Weeliano reported the Shift+drag vertex extrude (#183) and the G repeat after an extrude (#184) with exact steps.
@The-Maize found the switch back to Blender (#185), @swarnava05 the tall Time Slider (#190), @Egminator asked for
the Quad Draw corner fill (#180), and @LSKianhao suggested Panels > Perspective > New (#193) and the Attribute Editor
section layout (#194). Please keep telling us what breaks or feels off in real work.

Autodesk and Maya are registered trademarks or trademarks of Autodesk, Inc. This extension is not affiliated with or
endorsed by Autodesk, Inc.
