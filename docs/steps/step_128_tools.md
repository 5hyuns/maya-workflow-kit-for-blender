# Step 128 — 툴 전수 표 (Maya 옵션 박스가 있는 메뉴 항목)

생성: `tmp/audit128_issues/tool_inventory.py` (blender -b, kit 0.2.0 소스). 메뉴셋 사이 중복 제거.
열: Maya 메뉴 경로 / 구현(kit = `allset.*`, blender = Blender 연산자·툴, - = 미매핑 회색) / 옵션 박스가 여는 것
(window = Maya 필드 옵션 창(필드 수 + 회색), tool = 툴 + Tool Settings(Blender 패널), redo = Blender Adjust Last Operation,
generic = '설정 없음' 창, dialog = 연산자 자체 창, none = 미매핑) / 관련 이슈.

Tool Box 툴: Select / Lasso / Paint Select = Maya Tool Settings 섹션 없음 (#29), Move / Rotate / Scale = Maya 섹션 있음 (step 106).

요약 (Maya 옵션 박스 항목 386개): dialog 11, generic 50, none 160, redo 124, tool 14, window 27

| Maya 메뉴 항목 | 구현 | 대상 | 옵션 박스 | 이슈 |
|---|---|---|---|---|
| Cache/Alembic Cache/Export All to Alembic... | blender | `wm.alembic_export` | dialog |  |
| Cache/Alembic Cache/Export Selection to Alembic... | blender | `wm.alembic_export` | dialog |  |
| Cache/Alembic Cache/Import Alembic... | blender | `wm.alembic_import` | dialog |  |
| Cache/GPU Cache/Export All... | blender | `wm.alembic_export` | dialog |  |
| Cache/GPU Cache/Export Selection... | blender | `wm.alembic_export` | dialog |  |
| Cache/GPU Cache/Import... | blender | `wm.alembic_import` | dialog |  |
| Cache/Geometry Cache/Append to Cache | - | `-` | none |  |
| Cache/Geometry Cache/Create New Cache | blender | `wm.alembic_export` | dialog |  |
| Cache/Geometry Cache/Delete Cache | - | `-` | none |  |
| Cache/Geometry Cache/Delete Cache Frame | - | `-` | none |  |
| Cache/Geometry Cache/Export Cache | blender | `wm.alembic_export` | dialog |  |
| Cache/Geometry Cache/Merge Caches | - | `-` | none |  |
| Cache/Geometry Cache/Paint Cache Weights Tool | - | `-` | none |  |
| Cache/Geometry Cache/Replace Cache | - | `-` | none |  |
| Cache/Geometry Cache/Replace Cache Frame | - | `-` | none |  |
| Constrain/Aim | kit | `allset.constrain` | redo | #35 |
| Constrain/Closest Point | kit | `allset.constrain` | redo | #35 |
| Constrain/Geometry | kit | `allset.constrain` | redo | #35 |
| Constrain/Modify Constrained Axis... | - | `-` | none | #35 |
| Constrain/Motion Paths/Attach to Motion Path | kit | `allset.constrain` | redo | #35 |
| Constrain/Motion Paths/Flow Path Object | - | `-` | none | #35 |
| Constrain/Normal | - | `-` | none | #35 |
| Constrain/Orient | kit | `allset.constrain` | window (6+2 회색) |  |
| Constrain/Parent | kit | `allset.constrain` | window (10+2 회색) |  |
| Constrain/Point | kit | `allset.constrain` | window (6+2 회색) |  |
| Constrain/Point On Poly | kit | `allset.constrain` | redo | #35 |
| Constrain/Pole Vector | kit | `allset.pole_vector` | generic | #35 |
| Constrain/Proximity Pin | - | `-` | none | #35 |
| Constrain/Remove Target | - | `-` | none | #35 |
| Constrain/Scale | kit | `allset.constrain` | redo | #35 |
| Constrain/Tangent | - | `-` | none | #35 |
| Constrain/UV Pin | - | `-` | none | #35 |
| Control/Create Character Set | blender | `anim.keying_set_add` | generic |  |
| Control/Create Subcharacter Set | - | `-` | none |  |
| Control/Redirect | - | `-` | none |  |
| Create/Adobe(R) Illustrator(R) Object... | - | `-` | none |  |
| Create/Asset/Create Asset | - | `-` | none |  |
| Create/Asset/Create Asset with Transform | - | `-` | none |  |
| Create/Construction Plane | - | `-` | none |  |
| Create/Curve Tools/Bezier Curve Tool | kit | `allset.create` | redo |  |
| Create/Curve Tools/CV Curve Tool | kit | `allset.create` | redo |  |
| Create/Curve Tools/EP Curve Tool | - | `-` | none |  |
| Create/Curve Tools/Pencil Curve Tool | kit | `allset.pencil_curve` | generic |  |
| Create/Curve Tools/Three Point Circular Arc | - | `-` | none |  |
| Create/Curve Tools/Two Point Circular Arc | - | `-` | none |  |
| Create/Free Image Plane | kit | `allset.create` | redo |  |
| Create/Lights/Ambient Light | - | `-` | none |  |
| Create/Lights/Area Light | kit | `allset.create` | redo |  |
| Create/Lights/Directional Light | kit | `allset.create` | redo |  |
| Create/Lights/Point Light | kit | `allset.create` | redo |  |
| Create/Lights/Spot Light | kit | `allset.create` | redo |  |
| Create/Lights/Volume Light | - | `-` | none |  |
| Create/NURBS Primitives/Circle | kit | `allset.create` | redo |  |
| Create/NURBS Primitives/Cone | kit | `allset.create` | redo |  |
| Create/NURBS Primitives/Cube | kit | `allset.create` | redo |  |
| Create/NURBS Primitives/Cylinder | kit | `allset.create` | redo |  |
| Create/NURBS Primitives/Plane | kit | `allset.create` | redo |  |
| Create/NURBS Primitives/Sphere | kit | `allset.create` | redo |  |
| Create/NURBS Primitives/Square | kit | `allset.create` | redo |  |
| Create/NURBS Primitives/Torus | kit | `allset.create` | redo |  |
| Create/Polygon Primitives/Cone | kit | `allset.create` | window (5+5 회색) |  |
| Create/Polygon Primitives/Cube | kit | `allset.create` | window (8+3 회색) |  |
| Create/Polygon Primitives/Cylinder | kit | `allset.create` | window (6+4 회색) |  |
| Create/Polygon Primitives/Disc | kit | `allset.create` | redo |  |
| Create/Polygon Primitives/Gear | - | `-` | none |  |
| Create/Polygon Primitives/Helix | - | `-` | none |  |
| Create/Polygon Primitives/Pipe | - | `-` | none |  |
| Create/Polygon Primitives/Plane | kit | `allset.create` | window (6+1 회색) |  |
| Create/Polygon Primitives/Platonic Solid | kit | `allset.create` | redo |  |
| Create/Polygon Primitives/Prism | kit | `allset.create` | redo |  |
| Create/Polygon Primitives/Pyramid | kit | `allset.create` | redo |  |
| Create/Polygon Primitives/Soccer Ball | - | `-` | none |  |
| Create/Polygon Primitives/Sphere | kit | `allset.create` | window (5+1 회색) |  |
| Create/Polygon Primitives/Spherical Harmonics | - | `-` | none |  |
| Create/Polygon Primitives/Super Ellipse | - | `-` | none |  |
| Create/Polygon Primitives/Torus | kit | `allset.create` | window (6+1 회색) |  |
| Create/Polygon Primitives/Ultra Shape | - | `-` | none |  |
| Create/Sets/Partition | - | `-` | none |  |
| Create/Sets/Set | kit | `allset.create_set` | dialog |  |
| Curves/Align | - | `-` | none |  |
| Curves/Attach | blender | `curve.make_segment` | generic |  |
| Curves/Bend | - | `-` | none |  |
| Curves/CV Hardness | - | `-` | none |  |
| Curves/Curl | - | `-` | none |  |
| Curves/Cut | - | `-` | none |  |
| Curves/Detach | blender | `curve.split` | generic |  |
| Curves/Duplicate Surface Curves | - | `-` | none |  |
| Curves/Extend/Extend Curve | blender | `curve.extrude_move` | redo |  |
| Curves/Extend/Extend Curve On Surface | - | `-` | none |  |
| Curves/Fillet | - | `-` | none |  |
| Curves/Fit B-spline | - | `-` | none |  |
| Curves/Insert Knot | blender | `curve.subdivide` | redo |  |
| Curves/Intersect | - | `-` | none |  |
| Curves/Offset/Offset Curve | kit | `allset.offset_curve` | redo |  |
| Curves/Offset/Offset Curve On Surface | - | `-` | none |  |
| Curves/Open/Close | blender | `curve.cyclic_toggle` | redo |  |
| Curves/Project Tangent | - | `-` | none |  |
| Curves/Rebuild | - | `-` | none |  |
| Curves/Reverse Direction | blender | `curve.switch_direction` | generic |  |
| Curves/Scale Curvature | - | `-` | none |  |
| Curves/Smooth | blender | `curve.smooth` | generic |  |
| Curves/Smooth#2 | blender | `curve.smooth` | generic |  |
| Curves/Straighten | - | `-` | none |  |
| Deform/Blend Shape | kit | `allset.blend_shape` | generic | #34 |
| Deform/Blend Shape#2/Add | kit | `allset.blend_shape` | generic | #34 |
| Deform/Blend Shape#2/Remove | blender | `object.shape_key_remove` | redo | #34 |
| Deform/Blend Shape#2/Swap | - | `-` | none | #34 |
| Deform/Cluster | kit | `allset.cluster` | generic | #34 |
| Deform/Delta Mush | blender | `object.modifier_add` | redo | #34 |
| Deform/Jiggle/Jiggle Deformer | - | `-` | none | #34 |
| Deform/Jiggle/Jiggle Disk Cache | - | `-` | none | #34 |
| Deform/Lattice | blender | `object.modifier_add` | redo | #34 |
| Deform/Mirror Deformer Weights | blender | `object.vertex_group_mirror` | redo | #34 |
| Deform/Morph | - | `-` | none | #34 |
| Deform/Nonlinear/Bend | kit | `allset.nonlinear` | redo | #34 |
| Deform/Nonlinear/Flare | kit | `allset.nonlinear` | redo | #34 |
| Deform/Nonlinear/Sine | blender | `object.modifier_add` | redo | #34 |
| Deform/Nonlinear/Squash | kit | `allset.nonlinear` | redo | #34 |
| Deform/Nonlinear/Twist | kit | `allset.nonlinear` | redo | #34 |
| Deform/Nonlinear/Wave | blender | `object.modifier_add` | redo | #34 |
| Deform/Paint Weights/Blend Shape | blender | `paint.weight_paint_toggle` | generic | #34 |
| Deform/Paint Weights/Cluster | blender | `paint.weight_paint_toggle` | generic | #34 |
| Deform/Paint Weights/Delta Mush | blender | `paint.weight_paint_toggle` | generic | #34 |
| Deform/Paint Weights/Jiggle | blender | `paint.weight_paint_toggle` | generic | #34 |
| Deform/Paint Weights/Lattice | blender | `paint.weight_paint_toggle` | generic | #34 |
| Deform/Paint Weights/Nonlinear | blender | `paint.weight_paint_toggle` | generic | #34 |
| Deform/Paint Weights/Proximity Wrap | blender | `paint.weight_paint_toggle` | generic | #34 |
| Deform/Paint Weights/Set Membership | blender | `paint.weight_paint_toggle` | generic | #34 |
| Deform/Paint Weights/ShrinkWrap | blender | `paint.weight_paint_toggle` | generic | #34 |
| Deform/Paint Weights/Tension | blender | `paint.weight_paint_toggle` | generic | #34 |
| Deform/Paint Weights/Texture Deformer | blender | `paint.weight_paint_toggle` | generic | #34 |
| Deform/Paint Weights/Wire | blender | `paint.weight_paint_toggle` | generic | #34 |
| Deform/Point On Curve | - | `-` | none | #34 |
| Deform/Pose Space Deformation/Create Pose Interpolator | - | `-` | none | #34 |
| Deform/Proximity Wrap | blender | `object.modifier_add` | redo | #34 |
| Deform/Sculpt | - | `-` | none | #34 |
| Deform/ShrinkWrap | blender | `object.modifier_add` | redo | #34 |
| Deform/Soft Modification Tool | kit | `allset.soft_mod` | redo | #34 |
| Deform/Solidify | blender | `object.modifier_add` | redo | #34 |
| Deform/Tension | - | `-` | none | #34 |
| Deform/Texture | blender | `object.modifier_add` | redo | #34 |
| Deform/Wire | - | `-` | none | #34 |
| Deform/Wire#2/Add | - | `-` | none | #34 |
| Deform/Wire#2/Add Holder | - | `-` | none | #34 |
| Deform/Wire#2/Parent Base Wire | - | `-` | none | #34 |
| Deform/Wire#2/Remove | - | `-` | none | #34 |
| Deform/Wire#2/Reset | - | `-` | none | #34 |
| Deform/Wire#2/Wire Dropoff Locator | - | `-` | none | #34 |
| Deform/Wrap | blender | `object.modifier_add` | redo | #34 |
| Deform/Wrinkle | - | `-` | none | #34 |
| Edit Mesh/Add Divisions | blender | `mesh.subdivide` | redo | #33 |
| Edit Mesh/Assign Invisible Faces | - | `-` | none | #33 |
| Edit Mesh/Average Vertices | blender | `mesh.vertices_smooth` | redo | #33 |
| Edit Mesh/Bevel | blender | `mesh.bevel` | window (4+5 회색) |  |
| Edit Mesh/Bridge | blender | `mesh.bridge_edge_loops` | window (2+3 회색) |  |
| Edit Mesh/Chamfer Vertices | blender | `mesh.bevel` | redo | #33 |
| Edit Mesh/Circularize | kit | `allset.circularize` | generic | #33 |
| Edit Mesh/Connect | blender | `mesh.vert_connect_path` | generic | #33 |
| Edit Mesh/Duplicate | blender | `mesh.duplicate_move` | redo | #33 |
| Edit Mesh/Edit Edge Flow | kit | `allset.edge_flow` | redo | #33 |
| Edit Mesh/Extract | blender | `mesh.separate` | redo | #33 |
| Edit Mesh/Extrude | kit | `allset.extrude` | window (3+4 회색) |  |
| Edit Mesh/Merge | blender | `mesh.remove_doubles` | window (2+0 회색) |  |
| Edit Mesh/Poke | blender | `mesh.poke` | redo | #33 |
| Edit Mesh/Project Curve on Mesh | - | `-` | none | #33 |
| Edit Mesh/Split Mesh with Projected Curve | blender | `mesh.knife_project` | redo | #33 |
| Edit Mesh/Transform | blender | `builtin.transform` | tool | #33 |
| Edit Mesh/Wedge | kit | `allset.wedge` | redo | #33 |
| Edit/Delete by Type/Channels | kit | `allset.delete_by_type` | redo |  |
| Edit/Delete by Type/Non-Deformer History | kit | `allset.delete_history` | redo |  |
| Edit/Delete by Type/Non-particle Expressions | - | `-` | none |  |
| Edit/Delete by Type/Static Channels | kit | `allset.delete_by_type` | redo |  |
| Edit/Duplicate Special | kit | `allset.duplicate_special` | window (6+4 회색) |  |
| Edit/Group | kit | `allset.group` | window (2+0 회색) |  |
| Edit/Keys/Bake Simulation | blender | `nla.bake` | window (6+4 회색) |  |
| Edit/Keys/Copy Keys | kit | `allset.time_keys` | redo |  |
| Edit/Keys/Cut Keys | kit | `allset.time_keys` | redo |  |
| Edit/Keys/Delete Keys | blender | `anim.keyframe_clear_v3d` | generic |  |
| Edit/Keys/Paste Keys | kit | `allset.time_keys` | redo |  |
| Edit/Keys/Scale Keys | - | `-` | none |  |
| Edit/Keys/Snap Keys | kit | `allset.time_keys` | redo |  |
| Edit/LOD (Level of Detail)/Create LOD Group | - | `-` | none |  |
| Edit/LOD (Level of Detail)/Generate LOD Meshes | - | `-` | none |  |
| Edit/Parent | kit | `allset.parent` | generic |  |
| Edit/Transfer Attribute Values | - | `-` | none |  |
| Edit/Ungroup | kit | `allset.ungroup` | generic |  |
| Edit/Unparent | kit | `allset.unparent` | generic |  |
| Effects/Fire | kit | `allset.quick_smoke` | redo |  |
| Effects/Fireworks | - | `-` | none |  |
| Effects/Flow/Create Curve Flow | - | `-` | none |  |
| Effects/Flow/Create Surface Flow | - | `-` | none |  |
| Effects/Flow/Delete Selected Flow | - | `-` | none |  |
| Effects/Lightning | - | `-` | none |  |
| Effects/Shatter | - | `-` | none |  |
| Effects/Smoke | kit | `allset.quick_smoke` | redo |  |
| Generate/Auto Paint/Paint Grid | - | `-` | none |  |
| Generate/Auto Paint/Paint Random | - | `-` | none |  |
| Generate/Brush Animation/Bake Spring Animation | - | `-` | none |  |
| Generate/Brush Animation/Loop Brush Animation | - | `-` | none |  |
| Generate/Brush Animation/Make Brush Spring | - | `-` | none |  |
| Generate/Curve Utilities/Make Pressure Curve | - | `-` | none |  |
| Generate/Paint Effects Tool | - | `-` | none |  |
| Generate/Preset Blending | - | `-` | none |  |
| Key/Bake Simulation | blender | `nla.bake` | window (6+4 회색) |  |
| Key/Copy Keys | kit | `allset.time_keys` | redo | #35 |
| Key/Create Character Set | - | `-` | none | #35 |
| Key/Create Subcharacter Set | - | `-` | none | #35 |
| Key/Cut Keys | kit | `allset.time_keys` | redo | #35 |
| Key/Delete Keys | blender | `anim.keyframe_clear_v3d` | generic | #35 |
| Key/Paste Keys | kit | `allset.time_keys` | redo | #35 |
| Key/Redirect | - | `-` | none | #35 |
| Key/Scale Keys | - | `-` | none | #35 |
| Key/Set Breakdown Key | kit | `allset.set_key` | window (1+6 회색) |  |
| Key/Set Key | kit | `allset.set_key` | window (1+6 회색) |  |
| Key/Snap Keys | kit | `allset.time_keys` | redo | #35 |
| Mesh Display/Apply Color | - | `-` | none |  |
| Mesh Display/Average | blender | `mesh.average_normals` | redo |  |
| Mesh Display/Create Empty Set | blender | `geometry.color_attribute_add` | redo |  |
| Mesh Display/Paint Vertex Color Tool | blender | `paint.vertex_paint_toggle` | generic |  |
| Mesh Display/Prelight (Maya) | - | `-` | none |  |
| Mesh Display/Reverse | blender | `mesh.flip_normals` | redo |  |
| Mesh Display/Set Vertex Normal | - | `-` | none |  |
| Mesh Display/Set to Face | blender | `mesh.set_normals_from_faces` | redo |  |
| Mesh Display/Soften/Harden Edges | kit | `allset.soften_harden` | dialog |  |
| Mesh Display/Vertex Normal Edit Tool | blender | `transform.rotate_normal` | redo |  |
| Mesh Tools/Append to Polygon | blender | `builtin.poly_build` | tool | #30 |
| Mesh Tools/Connect | kit | `allset.connect` | generic | #33 |
| Mesh Tools/Crease Tool | kit | `allset.crease_tool` | tool | #33 |
| Mesh Tools/Create Polygon | blender | `builtin.poly_build` | tool | #30 |
| Mesh Tools/Insert Edge Loop | blender | `builtin.loop_cut` | tool | #31 |
| Mesh Tools/Make Hole | kit | `allset.make_hole` | generic | #33 |
| Mesh Tools/Multi-Cut | blender | `builtin.knife` | tool | #27 #28 |
| Mesh Tools/Offset Edge Loop | blender | `mesh.offset_edge_loops_slide` | redo | #31 |
| Mesh Tools/Paint Reduce Weights | - | `-` | none | #33 |
| Mesh Tools/Paint Transfer Attributes | - | `-` | none | #33 |
| Mesh Tools/Quad Draw | blender | `builtin.poly_build` | tool | #30 |
| Mesh Tools/Sculpting Tools/Amplify Tool | kit | `allset.sculpt_tool` | redo | #33 |
| Mesh Tools/Sculpting Tools/Bulge Tool | kit | `allset.sculpt_tool` | redo | #33 |
| Mesh Tools/Sculpting Tools/Clone Target Tool | - | `-` | none | #33 |
| Mesh Tools/Sculpting Tools/Erase Target Tool | - | `-` | none | #33 |
| Mesh Tools/Sculpting Tools/Fill Tool | kit | `allset.sculpt_tool` | redo | #33 |
| Mesh Tools/Sculpting Tools/Flatten Tool | kit | `allset.sculpt_tool` | redo | #33 |
| Mesh Tools/Sculpting Tools/Foamy Tool | kit | `allset.sculpt_tool` | redo | #33 |
| Mesh Tools/Sculpting Tools/Freeze Tool | kit | `allset.sculpt_tool` | redo | #33 |
| Mesh Tools/Sculpting Tools/Grab Tool | kit | `allset.sculpt_tool` | redo | #33 |
| Mesh Tools/Sculpting Tools/Imprint Tool | - | `-` | none | #33 |
| Mesh Tools/Sculpting Tools/Knife Tool | kit | `allset.sculpt_tool` | redo | #33 |
| Mesh Tools/Sculpting Tools/Mask Target Tool | - | `-` | none | #33 |
| Mesh Tools/Sculpting Tools/Pinch Tool | kit | `allset.sculpt_tool` | redo | #33 |
| Mesh Tools/Sculpting Tools/Relax Tool | kit | `allset.sculpt_tool` | redo | #33 |
| Mesh Tools/Sculpting Tools/Repeat Tool | kit | `allset.sculpt_tool` | redo | #33 |
| Mesh Tools/Sculpting Tools/Scrape Tool | kit | `allset.sculpt_tool` | redo | #33 |
| Mesh Tools/Sculpting Tools/Sculpt Tool | kit | `allset.sculpt_tool` | redo | #33 |
| Mesh Tools/Sculpting Tools/Smear Tool | kit | `allset.sculpt_tool` | redo | #33 |
| Mesh Tools/Sculpting Tools/Smooth Target Tool | - | `-` | none | #33 |
| Mesh Tools/Sculpting Tools/Smooth Tool | kit | `allset.sculpt_tool` | redo | #33 |
| Mesh Tools/Sculpting Tools/Spray Tool | kit | `allset.sculpt_tool` | redo | #33 |
| Mesh Tools/Sculpting Tools/Wax Tool | kit | `allset.sculpt_tool` | redo | #33 |
| Mesh Tools/Slide Edge | blender | `builtin.edge_slide` | tool | #31 |
| Mesh Tools/Target Weld | kit | `allset.target_weld_tool` | tool | #33 |
| Mesh/Booleans/Difference | kit | `allset.boolean` | redo | #33 |
| Mesh/Booleans/Intersection | kit | `allset.boolean` | redo | #33 |
| Mesh/Booleans/Union | kit | `allset.boolean` | redo | #33 |
| Mesh/Clipboard Actions/Clear Clipboard | - | `-` | none | #33 |
| Mesh/Clipboard Actions/Copy Attributes | - | `-` | none | #33 |
| Mesh/Clipboard Actions/Paste Attributes | - | `-` | none | #33 |
| Mesh/Combine | kit | `allset.combine` | window (1+2 회색) |  |
| Mesh/Conform | blender | `object.modifier_add` | redo | #33 |
| Mesh/Mirror | kit | `allset.mirror` | dialog | #33 |
| Mesh/Quadrangulate | blender | `mesh.tris_convert_to_quads` | redo | #33 |
| Mesh/Reduce | blender | `object.modifier_add` | redo | #33 |
| Mesh/Remesh | blender | `object.modifier_add` | redo | #33 |
| Mesh/Retopologize | blender | `object.quadriflow_remesh` | redo | #33 |
| Mesh/Smooth | blender | `object.modifier_add` | window (3+5 회색) |  |
| Mesh/Smooth Proxy/Crease Tool | kit | `allset.crease_tool` | tool | #33 |
| Mesh/Smooth Proxy/Remove Subdiv Proxy Mirror | - | `-` | none | #33 |
| Mesh/Smooth Proxy/Subdiv Proxy | blender | `object.modifier_add` | redo | #33 |
| Mesh/Transfer Attributes | blender | `object.modifier_add` | redo | #33 |
| Mesh/Transfer Shading Sets | blender | `object.make_links_data` | redo | #33 |
| Modify/Asset/Add to Asset | - | `-` | none | #33 |
| Modify/Asset/Assign Template... | - | `-` | none | #33 |
| Modify/Asset/Export Proxy Asset... | - | `-` | none | #33 |
| Modify/Asset/Publish Attributes | - | `-` | none | #33 |
| Modify/Asset/Publish Connections | - | `-` | none | #33 |
| Modify/Asset/Remove from Asset | - | `-` | none | #33 |
| Modify/Bake Pivot | kit | `allset.bake_pivot` | generic | #33 |
| Modify/Convert/Geometry to Bounding Box | - | `-` | none | #33 |
| Modify/Convert/NURBS to Polygons | blender | `object.convert` | redo | #33 |
| Modify/Convert/NURBS to Subdiv | - | `-` | none | #33 |
| Modify/Convert/Paint Effects to Curves | - | `-` | none | #33 |
| Modify/Convert/Paint Effects to NURBS | - | `-` | none | #33 |
| Modify/Convert/Paint Effects to Polygons | - | `-` | none | #33 |
| Modify/Convert/Polygon Edges to Curve | blender | `object.convert` | redo | #33 |
| Modify/Convert/Polygons to Subdiv | - | `-` | none | #33 |
| Modify/Convert/Subdiv to NURBS | - | `-` | none | #33 |
| Modify/Convert/Subdiv to Polygons | - | `-` | none | #33 |
| Modify/Convert/Texture to Geometry | - | `-` | none | #33 |
| Modify/Freeze Transformations | kit | `allset.freeze_transform` | window (3+3 회색) |  |
| Modify/Paint Attributes Tool | - | `-` | none | #33 |
| Modify/Paint Scripts Tool | - | `-` | none | #33 |
| Modify/Replace Objects | blender | `object.make_links_data` | redo | #33 |
| Modify/Reset Transformations | kit | `allset.reset_transform` | window (3+0 회색) |  |
| Modify/Snap Together Tool | kit | `allset.snap_together` | redo | #33 |
| Modify/Transformation Tools/Move Normal Tool | blender | `transform.shrink_fatten` | redo | #33 |
| Modify/Transformation Tools/Move Tool | blender | `builtin.move` | tool | #33 |
| Modify/Transformation Tools/Proportional Modification Tool | blender | `wm.context_toggle` | redo | #33 |
| Modify/Transformation Tools/Rotate Tool | blender | `builtin.rotate` | tool | #33 |
| Modify/Transformation Tools/Scale Tool | blender | `builtin.scale` | tool | #33 |
| Modify/Transformation Tools/Soft Modification Tool | blender | `wm.context_toggle` | redo | #33 |
| Modify/Transformation Tools/Universal Manipulator | blender | `builtin.transform` | tool | #33 |
| Select/Contiguous Edges | kit | `allset.select_loops` | redo |  |
| Select/Similar | blender | `object.select_grouped` | redo |  |
| Select/Surface Border | - | `-` | none |  |
| Skeleton/Assume Preferred Angle | kit | `allset.assume_preferred_angle` | generic | #32 |
| Skeleton/Connect Joint | blender | `armature.parent_set` | redo | #32 |
| Skeleton/Create IK Handle | kit | `allset.ik_handle` | generic | #32 |
| Skeleton/Create IK Spline Handle | kit | `allset.ik_spline_handle` | generic | #32 |
| Skeleton/Create Joints | kit | `allset.joint_tool` | generic | #32 |
| Skeleton/Mirror Joints | kit | `allset.mirror_joints` | redo | #32 |
| Skeleton/Orient Joint | kit | `allset.orient_joint` | redo | #32 |
| Skeleton/Set Preferred Angle | kit | `allset.set_preferred_angle` | generic | #32 |
| Skin/Bind Skin | kit | `allset.bind_skin` | window (3+5 회색) |  |
| Skin/Copy Skin Weights | kit | `allset.copy_skin_weights` | generic | #32 |
| Skin/Edit Influences/Add Influence | kit | `allset.add_influence` | generic | #32 |
| Skin/Export Weight Maps... | - | `-` | none | #32 |
| Skin/Interactive Bind Skin | - | `-` | none | #32 |
| Skin/Interactive Bind Skin Tool | - | `-` | none | #32 |
| Skin/Mirror Skin Weights | kit | `allset.mirror_skin_weights` | redo | #32 |
| Skin/Move Skinned Joints | - | `-` | none | #32 |
| Skin/Paint Skin Weights | kit | `allset.paint_skin_weights` | generic | #32 |
| Skin/Prune Small Weights | blender | `object.vertex_group_clean` | redo | #32 |
| Skin/Smooth Skin Weights | blender | `object.vertex_group_smooth` | redo | #32 |
| Skin/Substitute Geometry | - | `-` | none | #32 |
| Skin/Unbind Skin | kit | `allset.unbind_skin` | generic | #32 |
| Surfaces/Align | - | `-` | none |  |
| Surfaces/Attach | - | `-` | none |  |
| Surfaces/Bevel | - | `-` | none |  |
| Surfaces/Bevel Plus | kit | `allset.bevel_plus` | generic |  |
| Surfaces/Birail/Birail 1 Tool | - | `-` | none |  |
| Surfaces/Birail/Birail 2 Tool | - | `-` | none |  |
| Surfaces/Birail/Birail 3+ Tool | - | `-` | none |  |
| Surfaces/Booleans/Difference Tool | - | `-` | none |  |
| Surfaces/Booleans/Intersection Tool | - | `-` | none |  |
| Surfaces/Booleans/Union Tool | - | `-` | none |  |
| Surfaces/Boundary | - | `-` | none |  |
| Surfaces/Detach | - | `-` | none |  |
| Surfaces/Duplicate NURBS Patch | - | `-` | none |  |
| Surfaces/Extend | - | `-` | none |  |
| Surfaces/Extrude | kit | `allset.surface_extrude` | generic |  |
| Surfaces/Insert Isoparms | blender | `curve.subdivide` | redo |  |
| Surfaces/Intersect | - | `-` | none |  |
| Surfaces/Loft | kit | `allset.loft` | generic |  |
| Surfaces/Offset | - | `-` | none |  |
| Surfaces/Open/Close | blender | `curve.cyclic_toggle` | redo |  |
| Surfaces/Planar | kit | `allset.surface_planar` | generic |  |
| Surfaces/Project Curve on Surface | - | `-` | none |  |
| Surfaces/Rebuild | - | `-` | none |  |
| Surfaces/Reverse Direction | blender | `curve.switch_direction` | generic |  |
| Surfaces/Revolve | blender | `object.modifier_add` | redo |  |
| Surfaces/Round Tool | - | `-` | none |  |
| Surfaces/Sculpt Geometry Tool | - | `-` | none |  |
| Surfaces/Square | - | `-` | none |  |
| Surfaces/Stitch/Global Stitch | - | `-` | none |  |
| Surfaces/Stitch/Stitch Edges Tool | - | `-` | none |  |
| Surfaces/Stitch/Stitch Surface Points | - | `-` | none |  |
| Surfaces/Surface Editing/Surface Editing Tool | - | `-` | none |  |
| Surfaces/Surface Fillet/Circular Fillet | - | `-` | none |  |
| Surfaces/Surface Fillet/Fillet Blend Tool | - | `-` | none |  |
| Surfaces/Surface Fillet/Freeform Fillet | - | `-` | none |  |
| Surfaces/Trim Tool | - | `-` | none |  |
| Surfaces/Untrim | - | `-` | none |  |
| UV/3D Cut and Sew UV Tool | kit | `allset.cut_sew_tool_set` | generic |  |
| UV/3D Grab UV Tool | - | `-` | none |  |
| UV/Auto Seams | - | `-` | none |  |
| UV/Automatic | blender | `uv.smart_project` | window (2+3 회색) |  |
| UV/Camera-based | blender | `uv.project_from_view` | redo |  |
| UV/Contour Stretch | blender | `uv.follow_active_quads` | redo |  |
| UV/Cylindrical | blender | `uv.cylinder_project` | redo |  |
| UV/Merge UVs | blender | `uv.weld` | generic |  |
| UV/Normal-Based | kit | `allset.uv_planar` | window (2+3 회색) |  |
| UV/Planar | kit | `allset.uv_planar` | window (2+3 회색) |  |
| UV/Spherical | blender | `uv.sphere_project` | redo |  |
| Visualize/Create Animated Sweep | - | `-` | none |  |
| Visualize/Create Animation Snapshot | - | `-` | none |  |
| Visualize/Create Editable Motion Trail | blender | `object.paths_calculate` | redo |  |
| Visualize/Create Turntable... | - | `-` | none |  |
