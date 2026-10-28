# Smart Extrude

**Edit Mesh > Smart Extrude**, the **Polygons > Smart Extrude** shelf button and
**Shift+RMB > Smart Extrude** in face mode activate the combined manipulator.

1. Select a region on a closed mesh. Vertex and edge selections convert to their
   incident faces.
2. Drag the normal arrow outward to grow the region, or inward to carve a pocket.
   Continue through the opposite surface to cut a hole. Intersections with other
   shells of the same mesh are stitched automatically.
3. Use the rings to rotate and the end boxes to scale the cap. The centre square
   scales uniformly. Consecutive drags edit the same extrusion while its output
   remains selected; selecting a different region starts a new extrusion.
4. Hold **J** for incremental movement/rotation/scale. Type a value for exact input
   (rotation is entered in degrees). **Enter** or mouse release confirms;
   **Esc/right-click** restores the geometry and selection from before the drag.
   Hold **Shift** for precision; changing precision mid-drag keeps the current depth.
5. **G** repeats the accumulated extrusion parameters on the current selection.
   Undo/Redo restores topology as well as positions. **Q/W/E/R** leave the tool.

The tool header / Tool Settings expose **Component**, **Object**, **World** and
**Custom Pivot** orientation, and **Keep Faces Together**. Component orientation
inherits the kit's edited pivot frame. A component pivot placed with D is captured
before the first drag so changing cap topology cannot move the operation's pivot.

## Geometry and limits

- Positive signed sweep volumes are united with the input; negative volumes are
  subtracted with Blender's Exact Boolean solver. This supports outward overlap,
  inward corners, concave face regions, partial/full cut-through and disconnected
  shells **inside one mesh object**. Other objects are never Boolean operands.
- Input must be closed, manifold and have consistent face winding. Open surfaces,
  loose edges, shape-key meshes, zero object scale and simultaneous editing of
  several objects are rejected with an explanatory warning. Use positive scale.
- Start by dragging the normal arrow. Moving/scaling entirely within the original
  face plane has no solid volume to add or remove; these values can be combined
  with a subsequent normal movement of the same extrusion.
- Invalid output, including a cut that removes the entire object, is rejected
  atomically. During a drag the last valid mesh and gizmo position remain visible;
  releasing after rejection keeps that preview and reports a warning. Escape
  still restores the pre-drag mesh. No temporary operands or user modifiers remain.
- Original material slots and UV layers pass through the solver. Cap UVs inherit
  their source corners; cut/side UVs may need unwrapping. Coplanar generated edges
  and Boolean splits within each original face are dissolved, preserving original
  polygon boundaries and material/UV discontinuities. Planar cut panels become
  quads/n-gons. A polygon with an enclosed hole still needs support edges because
  Blender cannot store a single face with an inner boundary.
- Output may contain triangles and n-gons. This is not a quad retopology tool or a
  copy of Autodesk's proprietary solver. Extreme or self-crossing transforms may
  need smaller steps.
- Only the last matching Smart Extrude per object stays editable by the handles;
  it is session history, not a modifier stack saved in the blend file.

Previews rebuild from a frozen mesh, are limited to at most ten evaluations per
second and slow down adaptively when evaluation is expensive. Release commits the
latest validated preview; Escape restores the exact pre-drag snapshot.
Axis translation uses a fixed mapping at the gesture's start depth to avoid
perspective vanishing-point jumps during long cuts or near-axial views. The
manipulator displays the transform of the accepted mesh, including after the
moving cap has passed entirely through the object.

Ordinary **Extrude/Ctrl+E** and the legacy **Shift+drag** extrusion are separate
and retain their existing behavior. Autodesk also distinguishes these workflows:
[Smart Extrude](https://help.autodesk.com/cloudhelp/2026/ENU/Maya-Modeling/files/GUID-64343508-9FC9-451F-AE8A-A21C09242516.htm)
and [polySmartExtrude](https://help.autodesk.com/cloudhelp/2026/ENU/Maya-Tech-Docs/Commands/polySmartExtrude.html).

## Regression coverage

`tests/test_smart_geometry.py` checks volumes/manifold topology for outward/inward
sweeps, pockets, concave regions, corners, partial/full holes and separate shells.
`tests/test_smart_extrude.py` covers component conversion, orientation/transforms,
UVs/materials, repeated commands, atomic rejection and temporary-data cleanup.
`tests/gui/gui_smart_extrude.py` exercises actual handles, live previews, shared
Move/Rotate/Scale history, Undo/Redo, J, numeric input, cancellation and G in a
sandbox Blender window.
`tests/gui/gui_smart_extrude_cut.py` additionally checks long inward drags across
the exit plane, near-axial views, precision toggles, clean walls and rejection
without resetting a valid preview.
