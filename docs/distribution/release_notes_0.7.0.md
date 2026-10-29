# Release notes 0.7.0 (GitHub release)

Text for the GitHub release of v0.7.0. Full list: `CHANGELOG.md`. Before publishing, run the maintainer
checklist in .

---

**0.7.0 — Smart Extrude, pivot editing, a Maya Scale manipulator, and the fixes from your reports** (Blender 5.2 LTS; for Blender 4.5 LTS keep using 0.6.2)

Install it over 0.6.2, 0.6.1, 0.6.0 or 0.5.0 as usual; shelves, hotkeys, scenes and the kit's settings are kept.

Added
- Smart Extrude (Edit Mesh > Smart Extrude, the Polygons shelf, the face marking menu): grow or carve faces inside a
  closed mesh; pushed through it cuts a hole, and where it meets another part of the mesh the two join, with quad
  walls and no extra points on straight edges, like Maya (#207).
- Pivot editing with D: tap D (or Insert) to keep editing the pivot, click a vertex, edge or face to move the pivot
  there and turn it to that component; Move and Rotate follow the edited pivot (#207).
- Make Live for several meshes at once, Prevent Negative Scale for component scaling (#207).
- Create > Lights > Dome Light: an image-based light with a domeLight1 locator; Rotate turns the image, Intensity
  sets the strength (#201).
- Snapping in the EP / CV Curve Tools and arc tools: hold X, C or V while placing or dragging a point; middle drag
  moves the last point (#208).
- A preference to use Blender's navigation gizmo instead of the ViewCube (#209).

Fixed
- The Scale manipulator works like Maya's: the centre handle scales uniformly, axis and plane handles scale along
  them, Ctrl+drag on an axis scales the other two (#200).
- Graph Editor: selected objects without keys are listed, the tangent buttons have their own row, only selected keys
  show handles, S sets keys, F / A frame like Maya and Shift+middle drag locks to time or value (#192).
- Bevel, Extrude and Smooth leave their Maya node in the Channel Box INPUTS, in object mode too, and a blend shape
  shows as blendShape1 (#204).
- A drag off the Move / Rotate / Scale manipulator draws a marquee even when the tool's Drag setting is Tweak (#205).
- After a Shift+drag duplicate the Outliner rows stay still and the duplicate goes last, like Maya (#217).
- Kit windows (Hypershade, Render Settings, editors) open again at their last size and place (#203).
- IK on chains of three or more bones splits the bend between the joints like Maya (#181); bevelling part of a
  cylinder cap rim gives Maya's shape (#182); two driven keys on one channel no longer show a stale value (#186).
- Skin weights from a Maya FBX add up to 1 per vertex like Maya's own import (#189). Maya's FBX export leaves out
  weights of 0.001 and below; Skin > Prune Small Weights at 0.0011 before exporting keeps every weight in the file.
- Scenes with many objects: moving, editing or selecting costs about 0.6 ms more than plain Blender (was 2.9 ms) (#191).
- When part of Maya mode can't start, the kit takes everything back and says why, instead of leaving menus that don't
  open; switching back to Blender always removes the Maya menu bar (#198, #199). Commands on a hidden object warn
  instead of printing a Python error (#187, #196).
- The kit's settings survive switching the add-on off and on in Preferences > Add-ons.

Changed
- 0.7.0 is supported and tested on Blender 5.2 LTS only for now. It also installs on Blender 5.0 and 5.1, but those
  are not tested and may have problems. On Blender 4.5 LTS keep using 0.6.2.

The known differences listed in `CHANGELOG.md` still apply.

## Why this exists

Many artists learned 3D in Maya and spent years building muscle memory there. When they need to work in Blender,
because a team, a client, a class or a personal project uses it, that muscle memory works against them. This kit tries
to make that part a little easier. It is not meant to replace Maya or to move anyone away from it; many people use
both, and the kit is for the moments when you are in Blender and want your hands to feel at home.

Maya Workflow Kit is a free, personal open-source project: no paid version, no donations requested, and no commercial
goal behind it.

## Thank you

@youngmin2k contributed pivot editing, Prevent Negative Scale, Smart Extrude and Make Live (#207) and the hidden-mesh
component-mode fix (#196). @Fizkefaaz reported the Scale manipulator (#200) and the missing INPUTS nodes (#204),
@Kevorama the Tweak drag with a full analysis and test (#205), @Oxiidus the curve tool snapping (#208),
@invader-zimm asked for Blender's navigation gizmo (#209), @leo2ard for the Dome Light (#201) and for kit windows that
remember their size (#203), @swarnava05 reported the Graph Editor (#192), @Zhadowcode99 the menus and the switch on
Blender 5.1 (#198, #199), and @Weeliano the Outliner after a Shift+drag duplicate, with a video (#217). Please keep
telling us what breaks or feels off in real work.

Special thanks to [@ajitta](https://github.com/ajitta) for the wonderful Claude Code skills
([superclaude](https://github.com/ajitta/superclaude) and [know-your-unknowns](https://github.com/ajitta/know-your-unknowns))
that helped us plan, build and review this release. 🙏

Autodesk and Maya are registered trademarks or trademarks of Autodesk, Inc. This extension is not affiliated with or
endorsed by Autodesk, Inc.
