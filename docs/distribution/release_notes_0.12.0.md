# Release notes 0.12.0 (GitHub release)

Text for the GitHub release of v0.12.0. Full list: the 0.12.0 section of `CHANGELOG.md`.

---

**0.12.0 — Graph Editor tangent handles like Maya, joint sizes in metre scenes, closer Bevel corners** (Blender 5.2 LTS)

Install it over 0.11.0 (or 0.8.0 – 0.10.0) as usual; shelves, hotkeys, scenes and the kit's settings are kept.
(Removing the kit before installing deletes them: use Export Settings first.)
Supported: Blender 5.2 LTS. Other versions are not tested: the extension still installs on Blender 5.0 and 5.1,
but they may have problems. For Blender 4.5 LTS keep using 0.6.2.

## New

- Graph Editor tangent handles like Maya: in Maya mode a non-weighted tangent is drawn at a fixed length on screen
  along its direction, and dragging it only turns it; a weighted tangent sits at its real end. Click, drag,
  middle-drag with the Move Keys tool and marquee-select handle ends. A preference turns it off (#296).

## Fixed

- Joints are no longer drawn far too large in a scene shown in metres: a joint's Radius and Joint Size are
  centimetres in every scene unit (#311).

## Changed

- Bevel: a tip where two bevelled edges meet, and a corner of three bevelled edges whose angles differ a lot, now
  come closer to Maya's shape. These are approximations and still differ from Maya (#213).

## Known differences

- The known differences listed in `CHANGELOG.md` still apply.

## Thank you

Thanks for the reports: @meggaimg70-a11y (#296) and @pixelkeyblade18 (#311). Please keep telling us what breaks or
feels off in real work.

Maya Workflow Kit is a free, personal open-source project: no paid version, no donations requested, and no commercial
goal behind it.

Autodesk and Maya are registered trademarks or trademarks of Autodesk, Inc. This extension is not affiliated with or
endorsed by Autodesk, Inc.
