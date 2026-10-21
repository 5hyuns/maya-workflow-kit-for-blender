# Release notes 0.2.1 (store text)

Paste into extensions.blender.org → the listing → *Upload new version* → **Release notes** (English, short). Full list:
`CHANGELOG.md` 「0.2.1」; GitHub release notes are built from the same section.

---

**0.2.1 — bug fixes and store compliance** (Blender 4.5 LTS – 5.2)

- Installing or enabling the kit changes nothing outside it: no theme, no preference or keymap writes, no files
  outside the extension. Maya keys come and go with Maya mode.
- Icons redrawn after Maya 2022's (shelves, Status Line, panel toolbar, Tool Box, Layer Editor, menus), sharp at 100–150 %.
- Hypershade opens in Maya's layout (Browser, Create, Material Viewer, Graph, Property Editor).
- Fixes from real-use reports: soft select radius and colours, Channel Box multi-channel drag and entry, Multi-Cut,
  Tool Settings for every tool, Auto Key button and Time Slider key ticks, primitives with Maya topology and INPUTS,
  double-click loop select, Quick Layout and camera framing, marking menus that closed while dragging.
- Ctrl+N opens a new scene in the Maya layout; the viewport panel toolbar folds into a » menu when the view is
  narrow; the layout keeps its sizes at 125 % / 150 % UI scale.
- A crash when closing editor windows opened from Maya menus is fixed.

Thanks to everyone who reported problems from real work.

Autodesk and Maya are registered trademarks or trademarks of Autodesk, Inc. This extension is not affiliated with or
endorsed by Autodesk, Inc.
