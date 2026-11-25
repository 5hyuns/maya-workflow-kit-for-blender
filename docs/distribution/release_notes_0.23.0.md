# Release notes 0.23.0 (GitHub release)

Text for the GitHub release of v0.23.0. Full list: the 0.23.0 section of `CHANGELOG.md`.

---

**0.23.0 — Hotkey Editor with every command, Duplicate Face, viewport anti-aliasing** (Blender 5.2 LTS and 5.3)

Hello everyone. This version is mostly about the Hotkey Editor: commands that have no key in Maya are listed too, so
you can give a key to a menu item, an editor command or a UV Toolkit button. Thank you for the reports that led to
these changes.

Install it over 0.22.0 (or 0.8.0 – 0.21.0) as usual; shelves, hotkeys, scenes and the kit's settings are kept.
(Removing the kit before installing deletes them: use Export Settings first.)
Supported: Blender 5.2 LTS and 5.3. Other versions are not tested: the extension still installs on Blender 5.0 and
5.1, but they may have problems. For Blender 4.5 LTS keep using 0.6.2.

## Hotkey Editor

- **Menu item commands (#530):** every main-menu item's command is listed with Maya's name and category (Merge,
  Merge (Option), Merge to Center, Combine ...), found by command or menu label. A key you give it runs that menu
  item, or its option box for an "(Option)" command.
- **Editor commands (#537, #538, #539):** the UV Editor commands (Unfold U / V, Align and the rest), the UV Toolkit
  buttons (Custom Scripts > UV Toolkit), X-Ray (Toggle) and X-Ray Joints (Toggle), and the Graph Editor, Hypershade,
  Dope Sheet and Trax Editor commands.
- **Window toggles (#541):** Custom Scripts > Windows opens the UV Editor, Outliner, Hypershade, Graph Editor, Dope
  Sheet, Trax Editor, Node Editor or Attribute Spread Sheet, or closes it when it is open.
- **Fixed (#544):** a Blender key switched off or changed in Blender mode (the mouse wheel zoom, for one) no longer
  switches off the same Maya key; those edits come back when you return to Blender mode.

## Modeling

- **Edit Mesh > Duplicate (#542):** copies the selected faces like Maya's Duplicate Face, each face a piece of its
  own, with Separate duplicated faces and Offset, the manipulator, In-View Editor and Channel Box inputs.
- **Fixed:** Bevel on an object selection bevels every edge and stays in object mode, and World Space bevels
  non-uniformly scaled meshes evenly (#532); Circularize puts an edge loop's circle in Maya's plane and spreads the
  inner vertices of a face block like Maya (#465); Mesh Display > Apply Color and Prelight show the colours at once
  (#531); Wedge turns the faces up around the edge you pick, and Shift+click in edge mode picks an edge of the
  selected faces without dropping them (#546).

## UV Editor

- **UV Toolkit (#535):** buttons two to a row in Maya's pairs and names, with U / V choices beside Unfold Along,
  Layout Along and Flip; the arrow buttons are all one size; Measure shows its result in the Command Line.
- **Unfold options (#504):** Prevent self border intersections, Map size and Room space can be set.
- **Fixed:** UV Toolkit Move / Rotate / Scale with UV Sync Selection move only the selected faces' UVs (#540);
  UV > Automatic with 8 and 12 planes makes the same shells as Maya, also with Layout on (#488).

## Marking menus and viewport

- **Fixed (#543):** a quick flick past a radial submenu item runs that submenu's item in the same direction; for
  example Ctrl+right-click flicked left, up, right or down converts the selection to vertices, edges, UVs or faces.
- **Multisample Anti-aliasing (PR #536):** a viewport toolbar button (off) smooths selection wires and manipulator
  handles in that viewport only. Thanks to cnzim for this contribution.

## Contributors

- @cnzim: Multisample Anti-aliasing for selection wires and manipulator handles (PR #536). Thank you for the code and for the careful follow-ups.

## Thank you

This version was shaped by your reports. Thank you, every one of you, for taking the time to write down what broke or felt off:

- @envwarby: the Hotkey Editor gaps (#530, #537, #538, #539, #541), Assign Vertex Colors (#531), UV Toolkit Move / Rotate / Scale (#540), Duplicate Face (#542) and the marking menu flick (#543). Nine clear reports, each with the exact steps.
- @dylanpearson004-coder: the Bevel differences from Maya (#532).
- @suenwaichit: the UV Toolkit button layout (#535).
- @JinxSwe: Wedge (#546).
- @sofiejg: the mouse wheel zoom question in Discussion #489, which led to #544.
- @invaderzod: Multi-Cut across faces (#545). We are still checking this one and will follow up in the issue.

Please keep telling us what breaks or feels off in real work: an issue or a Discussion post is always welcome.
