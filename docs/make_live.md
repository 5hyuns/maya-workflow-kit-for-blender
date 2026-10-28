# Make Live

Select one or more mesh objects in Object Mode and click the **magnet** on the
Status Line, or use **Modify > Make Live**. The arrow beside it opens **Make Live
History**; the name field opens the same menu. An empty selection, selecting the
current live list again, or choosing **No Live Surface** turns Live off.
Middle-click the magnet or history arrow to toggle the most recent live list.

Live meshes are deselected and cannot be picked or box-selected in the viewport.
Their Maya Outliner labels use dark green **`#009954`** (sRGB 0, 153, 84).
Their wire overlay uses the same colour in Wireframe or Wireframe on Shaded;
shaded-only mode does not force wires on. This is independent of the selection
wire preference. Transform channels and animation are not locked.

The native Outliner remains available for reference management: select a live
row there, then use **Remove Selected** in the history menu, or use its explicit
**Remove <name>** entry. **Add Selected** adds meshes without replacing the list.
The last 16 distinct lists are remembered in the scene. Renaming a mesh preserves
its identity. Deleting it removes it from usable targets. Undo/Redo, save/reload
and disabling/re-enabling the addon reconcile selection restrictions; leaving
Live restores the original selection restriction, including an existing lock.

## Working on the surfaces

- **Move centre and plane handles** project the moving selection's pivot onto
  the live meshes, including in Mesh Edit Mode. Other meshes in front are ignored.
  Moving off the references keeps the last valid preview. Shift gives precision,
  J gives steps, Esc restores the original selection, and release commits one
  undoable move. Single-axis arrows retain native movement, as in Maya.
- **Quad Draw** queries the entire live list, including hidden references and
  evaluated modifiers. It edits a separate retopology mesh, never a live mesh.
  Without a live list its existing visible-mesh/construction-plane fallback stays
  available.
- Snap preferences remain independent. Explicit grid, vertex, edge and curve
  snapping takes precedence and delegates Move to Blender's native transform;
  that path can query geometry outside the live list. Turn those snap modes off
  when you want the dedicated live-surface Move behavior.

Uniform-scale reference meshes use Blender's native local BVH with world-space
query results, avoiding large Python vertex/face lists. Nonuniform scale and
shear use world-space BVHs so nearest-distance queries remain exact. Geometry
and transform updates invalidate entries; frame/file/undo changes clear them.
Releasing a reference from its last live scene drops its cached BVH immediately.
Quad Draw's non-live fallback retains its working cache across unrelated edits.

The cache holds at most 64 entries, evicting the least recently queried surface
under an estimated 256 MiB budget. One oversized surface can occupy it alone.
This estimate bounds retained entries, not peak process memory: evaluated mesh
data, Blender's own caches and allocator retention can still be substantial on
million-polygon references. No geometry is baked into the reference object.

The Outliner reads its visible pixels once per draw and reuses row matches only
while the native pixels, names, scale and row positions agree. Changed rows use
glyph bounds to narrow the search. This preserves rename, selection, filtering
and scrolling without rescanning every translation on every redraw. Both its
glyph and region caches are bounded.

## Scope and validation

This implementation targets mesh surfaces, not Maya NURBS or GPU cache surfaces.
Multi-Cut's live constraint is still unavailable. The native Outliner colour is
drawn over matched visible labels because Blender exposes no Python per-row text
colour API. Unmatched labels keep their native text. Virtual camera/set rows
only occupy free rows and never cover native objects; enlarge a short Outliner
to see more virtual entries.

Automated checks use the repository's sandbox harness in Blender 5.2.2 LTS:

```text
python tests/run.py -k make_live,step144_poly,step59_pivot_snap,enable_disable
python tests/run.py -k live_performance,maya_startup
python tests/gui/run.py --no-build -k gui_make_live,gui_live_surface_move
python tests/gui/run.py --no-build -k gui_live_outliner_performance,gui_maya_saved_startup
python tests/gui/run.py --no-build -k gui_make_live --ui-scale 1.25
python tests/gui/run.py --no-build -k gui_make_live --ui-scale 1.5
```

The GUI checks verify rendered colour, viewport picking, native Outliner
management, renamed/filtered/scrolled rows, history and Undo/Redo, actual Move
handles and Quad Draw on a second live mesh. Maya itself was not run; behavior
was compared with the Autodesk documentation and supplied screenshots.

## Autodesk references

- [Status Line: Make Live and history](https://help.autodesk.com/cloudhelp/2026/ENU/Maya-Basics/files/GUID-86E5CEDA-4100-40AE-8F95-346206CF8456.htm)
- [Live surfaces and display](https://help.autodesk.com/cloudhelp/2026/ENU/Maya-Basics/files/GUID-3FEA0E22-E66B-4311-A52E-AAA5C6778E6E.htm)
- [Manage live objects from the Outliner](https://help.autodesk.com/cloudhelp/2026/ENU/Maya-Basics/files/GUID-46B74E76-CAB7-479E-B18B-C369292307AB.htm)
- [Move on live surfaces](https://help.autodesk.com/cloudhelp/2026/ENU/Maya-Basics/files/GUID-FF6DDE20-B1BF-4A78-8232-948665F3A904.htm)
- [makeLive command](https://help.autodesk.com/cloudhelp/2026/ENU/Maya-Tech-Docs/CommandsPython/makeLive.html)
