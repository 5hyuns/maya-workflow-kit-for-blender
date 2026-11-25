# Release notes 0.24.0 (GitHub release)

Text for the GitHub release of v0.24.0. Full list: the 0.24.0 section of `CHANGELOG.md`.

---

**0.24.0 — UV commands follow the selection, Transfer Attributes, soft select and Multi-Cut fixes** (Blender 5.2 LTS and 5.3)

Hello everyone. This version is mostly about the UV Editor: shell commands, projections and the UV Toolkit now work on
the shells you picked, the way Maya does. It also fixes Transfer Attributes, soft select with the Scale Tool,
Multi-Cut across faces and Wedge, all from your reports. Thank you for them.

Install it over 0.23.0 (or 0.8.0 – 0.22.0) as usual; shelves, hotkeys, scenes and the kit's settings are kept.
(Removing the kit before installing deletes them: use Export Settings first.)
Supported: Blender 5.2 LTS and 5.3. Other versions are not tested: the extension still installs on Blender 5.0 and
5.1, but they may have problems. For Blender 4.5 LTS keep using 0.6.2.

## Modeling

- **Mesh > Transfer Attributes (#554):** select the source mesh, then the target: the target takes the source's vertex
  normals, vertex positions, UV sets and color sets, and keeps following the source. With Vertex normal On a
  hard-edged low-poly mesh takes the smooth normals of the mesh around it. The option box opens Transfer Attributes
  Options. (It used to add an empty Data Transfer modifier that transferred nothing.)
- **Select > Convert Selection > To Contained Edges / To Contained Faces:** select only what the selection fully holds.
- **Fixed:** Multi-Cut cuts straight across the faces between two points that share no face (#545); Wedge takes the
  edge you picked before switching to face mode as its hinge, and draws the hinge edge (#546); with soft select on,
  dragging a Scale handle moves the points around the selection by the falloff (#548), and moving an object no longer
  drags the objects next to it (#547); Bevel with an absolute Offset next to a twisted face (#213, part).

## UV Editor

- **Image > Measure Pixel Distance:** the width, height and diagonal of the selected UVs in pixels, for map sizes 4096
  down to 128 (also in the Shift+right-click UV marking menu).
- **Image > Dim:** draws the image darker under the UVs, with Image Dim Options for the amount.
- **3D Cut and Sew UV Tool (#555):** double-click an edge to cut its whole edge loop, Ctrl+double-click to sew it.
- **Hotkey Editor (#551):** the UV Toolkit's Pivot, Edit Pivot, Reset, Snap and Measure buttons, Unfold (Option),
  Layout (Option) and the Select Overlapping / Non-Overlapping / Back-Facing / Front-Facing UVs commands can take a key.
- **Fixed:** with UV Sync Selection, Flip, Normalize, Snap and Stack, Optimize and Orient Shells to Edges leave shells
  that only share a vertex with the selection alone, and Unfold, Layout, Orient, Stack, Snap, Randomize, Unitize and
  Texel Density Set work on the shells beside a selected edge or vertex (#549); Cut UV Edges and Create UV Shell leave
  shells that are already separate where they are (#550); with UV Sync Selection off, the projections project only
  the picked UV faces (#553); Unfold keeps a shell's direction, and Optimize treats a shell with one pinned UV as free
  (#521).

## Channel Box

- **SHAPES rows (#481):** cameras show Lens Squeeze Ratio, Shutter Angle and Center Of Interest; point, directional,
  spot and area lights show Shad Color, Use Depth Map Shadows and Dmap Bias (spot lights also Dropoff); a locator shows
  Local Position and Local Scale.

## Contributors

- None this time: every change in 0.24.0 was made in this repository. (PR #536 by @cnzim was already part of 0.23.0.)

## Thank you

This version was shaped by your reports. Thank you, every one of you, for taking the time to write down what broke or felt off:

- @Sddtx: Transfer Attributes not transferring vertex normals (#554), with screenshots of both sides that showed at once what was missing.
- @invaderzod: Multi-Cut not connecting points with edges between them (#545).
- @YoruQueenOfNight: soft select not working with the Scale Tool (#548).
- @dlobser: new objects moving together (#547). We fixed the case we could reproduce; please tell us in the issue if it still happens to you.
- @JinxSwe: the follow-up on Wedge (#546): the picked edge was not shown and not used when picked first. Thank you for coming back to it.
- @ganesh2004jadhav-boop: moving vertices along their normals (#552). Ctrl+middle-drag with the Move Tool already does this in component mode; we checked it again thanks to your question.
- @jixueliang: the Bevel corner comparison in #213, with exact settings and counts. The corner shape you found is on our list for a later version.

Please keep telling us what breaks or feels off in real work: an issue or a Discussion post is always welcome.
