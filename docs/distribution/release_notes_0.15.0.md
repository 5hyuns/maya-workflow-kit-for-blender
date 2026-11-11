# Release notes 0.15.0 (GitHub release)

Text for the GitHub release of v0.15.0. Full list: the 0.15.0 section of `CHANGELOG.md`.

---

**0.15.0 — A Maya Outliner tree with joints, Ctrl+D makes a plain copy, camera gates and fits like Maya, Render Sequence per camera again, faster Maya-mode playback, Traditional Chinese, and the fixes from your reports** (Blender 5.2 LTS)

Install it over 0.14.0 (or 0.8.0 – 0.13.0) as usual; shelves, hotkeys, scenes and the kit's settings are kept.
(Removing the kit before installing deletes them: use Export Settings first.)
Supported: Blender 5.2 LTS. Other versions are not tested: the extension still installs on Blender 5.0 and 5.1,
but they may have problems. For Blender 4.5 LTS keep using 0.6.2.

## New

- Traditional Chinese translation of the kit's menus, marking menus, shelves and tooltips (from @yoyomaimai, #341).
- Render > Render Sequence renders every camera whose Renderable check is on again, one after another, each camera's
  frames in its own folder; in Maya mode Render Settings has a Common panel with Skip existing frames and Renderable
  Cameras (#252).
- Modify > Match Transformations: all five items open option windows (#350).
- Texture file browsers start in the project's sourceimages folder in Maya mode (#349).
- Alt+LMB+MMB zooms the Graph Editor, Dope Sheet, Node Editor, NLA and UV Editor like their Alt+RMB (#325).
- Viewport panel toolbar: Bookmarks (also View > Bookmarks and a Bookmark Editor) and 2D Pan/Zoom work (#346).
- View > Camera Tools > 2D Pan/Zoom Tool is a tool: drag to pan or zoom, Ctrl+drag zooms into a box (#346).

## Changed

- The `\` key works like Maya's 2D Pan/Zoom in every view: tap it to turn 2D Pan/Zoom on or off, hold it and
  middle-drag to pan, right-drag to zoom (before, `\` + left drag panned and `\` + middle drag zoomed) (#346).
- Ctrl+D, Shift+D and Smart Duplicate make a plain copy, like Maya: the geometry as it shows at the current frame,
  without history, deformers, shape keys, keys or constraints, so animating the original no longer moves the copy;
  particle systems (hair) and Collision are not copied. Duplicate Special's new Duplicate input graph and Duplicate
  input connections options give the other kinds of copy (input connections is what Ctrl+D did before) (#347).
- The last picked object leads after a box, lasso, Outliner range or Select All too: Match Transformations takes it as
  the source, and in Maya mode it is the active object the Channel Box, Attribute Editor and selection wire show
  (#338).
- New cameras start with the fit Maya gives them: Fill for Create > Cameras, Horizontal for the persp / top / front /
  side cameras of a new scene; older cameras keep Blender's Auto fit (#345).
- The Maya Outliner is a Maya tree drawn by the kit: joints are rows under their parent joint (#348 — the joints
  couldn't be seen before), objects in creation order, sets last; click / Ctrl / Shift picks, a left drag selects,
  a middle drag parents, double-click or Enter renames, F reveals the selection, and the right-click menu has Shapes,
  Reveal Selected, Hide In Outliner, Sets, Display and Show.
- Create Camera From View (Ctrl+Shift+C, panel View menu) copies the camera the view looks through, the view looks
  through the copy and the selection stays; Panels > Orthographic has New > Front / Back / Right / Left / Top / Bottom.
- Component mode D / Insert keeps the Move / Rotate / Scale manipulator with pivot handles (with other tools, the
  Select tool included, they do nothing), and a placed component pivot moves with the components (#351).
- Render > Render Sequence runs with the options saved in its window; options saved with 0.8.0 are used again, so
  check its option box once (#252).

## Fixed

- Alt+LMB+MMB dolly: letting go of one button carries on with the one still held (#343).
- Faster playback in Maya mode with rigged characters (#344).
- Camera gates: the Film Gate is the film back and sits on the Resolution Gate like Maya, and the Attribute Editor's
  Fit Resolution Gate has Fill, Horizontal, Vertical and Overscan (#345).
- Soften Edge, Harden Edge and Soften/Harden Edges show their result on meshes with history, and one Ctrl+Z takes it
  back in component mode (#342).
- Edge slides keep the UV layout, and Preserve UVs gives the right UVs with the Scale tool and the Universal
  Manipulator (#340).
- Auto Key keys a changed constraint weight that already has keys (#329).
- Panels > Tear Off / Tear Off Copy keep the panel menu bar and toolbar (#346).
- The option box works in menus opened from the Space hotbox (#350).
- The UV Editing shelf's UV Editor button opens the UV Editor window (#352).
- UV Unfold no longer freezes Blender on dense meshes, and UV > Sew UV Edges, Merge UVs, Cut UV Edges, Delete UVs,
  Split UVs and Auto Seams use the 3D View selection when UV Sync Selection is off (#354).

## Known differences

- Component pivot: Undo doesn't yet take back an edit of the pivot alone (moving it with D); Maya's Undo does.
- Duplicate input graph: the copy's deformers still use the original's skeleton, lattice or cluster handles; Maya
  copies those too.
- Outliner: Blender edits joints in Pose Mode, so a joint and a mesh can't be picked together; Ctrl+clicking a mesh
  row after a joint keeps the whole skeleton selected with it (what Bind Skin needs).
- Saving the scene while Render Sequence renders several cameras saves the camera and output folder of the camera
  being rendered; save before or after the sequence.
- 2D Pan/Zoom in Blender's own persp view: it has no film offset, so the kit turns the view about its eye and narrows
  its lens (the zoom stops at 250 mm); views that look through a camera and the top / front / side views pan and zoom
  exactly like Maya.
- The known differences listed in `CHANGELOG.md` still apply.

## Thank you

Thanks to @yoyomaimai for the Traditional Chinese translation (#341), and for the reports and ideas: @mfjooste (#325),
@ArcticZA (#329, #338), @kwaksaemi1028-commits (#340), @psokk (#342), @Nichosen (#343), @pixelkeyblade18 (#344),
@rethink-studios (#345), @haithamcolorcolor-spec (#346), @Fizkefaaz (#347), @Arminanimator (#348), @DAI3rd (#349,
#252), @KMller (#350), @Drawingonwhite (#351), @jadelion-creator (#352) and @sushilthakur236 (#354).
Please keep telling us what breaks or feels off in real work.

Maya Workflow Kit is a free, personal open-source project: no paid version, no donations requested, and no commercial
goal behind it.
