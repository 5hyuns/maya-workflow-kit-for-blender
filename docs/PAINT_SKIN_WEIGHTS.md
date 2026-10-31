# Paint Skin Weights

Enable Maya mode, select a skinned mesh, and choose **Skin > Paint Skin Weights**. Like Maya, the plain menu item
starts the tool and leaves the Channel Box as the Channel Box; the tool's settings are in **Tool Settings**: the menu's
option box or a double-click on the paint tool opens them, as in Maya.
Q/W/E/R leave painting with the mesh still selected (Maya: the Select / Move / Rotate / Scale tool).

The sections follow Maya 2026 Tool Settings, then two Blender extras:

| Section | Contents |
|---|---|
| Skin Clusters | The skin (Armature modifier = skinCluster), influence count, Normalize Weights (Interactive), Lock-relative |
| Influences | Search, sort (hierarchy / name / group order), lock menu, influence list, lock others / unlock all |
| Brush | Brush asset, Maya operations Replace / Add / Scale / Smooth (+ Blender Subtract / Average / Smear), Value, Opacity, Radius, value presets, Flood, Sample, Pick joint, gradients, profile (falloff), blend, front faces, size units, multi-paint, existing weights only |
| Visualization | Weight opacity, contours, zero weights, colour ramp (Maya's numeric weight display has no Blender counterpart) |
| Stroke | Stroke method / spacing, stabilizer, reflection X / Y / Z, mirrored influence names, radial copies, topology matching |
| Stylus Pressure | Radius / Opacity / Jitter pressure with curves |
| Display | Brush outline, brush on surface, cursor display, wireframe, overlays, joints in front |
| Skin Commands *(Blender extra)* | Set Value, Normalize, Smooth, Levels, Mirror, Prune, Limit, Quantize, Invert, Transfer, Automatic / Envelope weights (Maya has these in the Skin menu) |
| Selection Masking *(Blender extra)* | Vertex / face masks and their selection commands |

Flood applies the chosen operation and opacity to the active influence and keeps locked influences.

Skin weight layers like Maya's Skin Tools: the **Skin Tools (layers)** button in Skin Clusters opens the Skin Tools
window (Initialize Skin Layers, Layers, Influences with the Mask, Paint / Set Weights / Mirror). Once a mesh has
layers, Skin > Paint Skin Weights opens Skin Tools instead of this tool.

Not done yet (GitHub issues): Maya's influence context menu (Select / Add / Remove Affected Verts), several
skinClusters per mesh (Maya 2024 and later).

## Validation

`tests/integration/blender_weight_workspace.py` (brush families, gradients, Flood maths and masks, locks,
normalization, transfer, automatic / envelope weights, filtering, re-entry) and
`tests/integration/blender_weight_workspace_ui.py` (every section collapsed and expanded in a Tool Settings dock) pass on
Blender 5.2; `tests/gui/gui_step58_skin.py` paints through the Tool Settings influence list.
