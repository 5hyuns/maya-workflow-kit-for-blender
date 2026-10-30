"""#123: Maya FX / Rendering / Hypershade menu items on Blender's own systems — every newly wired item runs headless
and leaves the Blender result a Maya user expects (cloth, particles, Mantaflow, rigid bodies, fields, toon and
volume materials, World colour)."""

import os
from importlib import import_module

import bmesh
import bpy

import kit

fx = import_module(kit.MODULE + ".operators.fx")
fx_more = import_module(kit.MODULE + ".operators.fx_more")
render_more = import_module(kit.MODULE + ".operators.render_more")
units = import_module(kit.MODULE + ".operators.units")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
menu_sets = import_module(kit.MODULE + ".ui.menu_sets")
notices = import_module(kit.MODULE + ".ui.notices")
editor_menu_map = import_module(kit.MODULE + ".ui.editor_menu_map")

FX_PATHS = (
    "nParticles/Fill Object", "nParticles/Instancer",
    *(f"nParticles/Create Options/{s}" for s in ("Point", "Balls", "Cloud", "Thick Cloud", "Water")),
    "Fluids/Add/Edit Contents/Emitter", "Fluids/Edit Fluid Resolution",
    "nCloth/Rest Shape/Set Rest To Start Shape", "nCloth/Rest Shape/Connect Input Mesh to Rest Shape",
    "nCloth/Rest Shape/Connect Selected Mesh to Rest Shape",
    *(f"nCloth/Paint Vertex Properties/{p}" for p in ("Input Attract", "Stretch", "Compression", "Bend",
                                                       "Rest Length Scale")),
    *(f"nConstraint/{c}" for c in ("Transform Constraint", "Disable Collision", "Remove Dynamic Constraint",
                                   "Select Members", "Add Members", "Remove Members", "Replace Members")),
    "nCache/Create Particle Disk Cache", "nCache/Transfer Cache To Input Mesh",
    "nCache/Edit Oversampling or Cache Settings...",
    "Fields/Solvers/Volume Curve", "Fields/Solvers/Initial State/Set for Selected",
    "Fields/Solvers/Initial State/Set for All Dynamic", "Fields/Solvers/Set Active Key",
    "Fields/Solvers/Set Passive Key", "Fields/Solvers/Break Rigid Body Connections",
    "Fields/Solvers/Rigid Body Solver Attributes", "Fields/Solvers/Create Rigid Body Solver",
    "Effects/Flow/Create Curve Flow", "Effects/Flow/Delete Selected Flow", "Effects/Collide with Effect",
)
RENDER_PATHS = (
    "Lighting/Shading/Transfer Maps...", "Toon/Reverse Surfaces", "Stereo/Create",
    *(f"Toon/Assign Fill Shader/{k}" for k in ("Solid Color", "Light Angle Two Tone", "Shaded Brightness Two Tone",
                                               "Shaded Brightness Three Tone", "Dark Profile", "Rim Light",
                                               "Circle Highlight")),
    *(f"Toon/Set Camera Background Color/{c}" for c in ("persp", "front", "side", "top")),
)
HS_PATHS = (
    *(f"Hypershade/Create/{p}" for p in (
        "General Utilities/Uv Chooser", "Particle Utilities/Particle Sampler", "Environment Textures/Env Ball",
        "Environment Textures/Env Cube", "Environment Textures/Env Sky", "Color Utilities/Color Composite",
        "Color Utilities/Color Correct", "Scalar Utilities/Float Composite", "Scalar Utilities/Float Correct",
        "2D Textures/Mountain", "3D Textures/Stucco", "Image Plane",
        *editor_menu_map.HS_EXTRA)),
    "Hypershade/Window/Connection Editor...", "Hypershade/Window/Connect Selected...",
    "Hypershade/Edit/Duplicate/With Connections to Network",
)


# --- helpers ----------------------------------------------------------------------------------------------------------

def _scene():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for coll in (bpy.data.meshes, bpy.data.particles, bpy.data.materials, bpy.data.curves):
        for d in list(coll):
            if d.users == 0:
                coll.remove(d)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0
    sc.unit_settings.length_unit = 'CENTIMETERS'
    sc.frame_start, sc.frame_end, sc.use_preview_range = 1, 24, False
    if sc.rigidbody_world is not None:
        bpy.ops.rigidbody.world_remove()
    bpy.context.window_manager.allset_nparticle_style = 'POINT'
    sc.frame_set(1)
    return sc


def _select(*obs):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[-1] if obs else None


def _run(path, **extra):
    """Run a Maya menu path's action the way the menu does, without dialogs (EXEC)."""
    kind, target, props = menu_map.spec(path)
    props.update(extra)
    if kind == "prop":
        return menu_sets.set_prop(bpy.context, target, props)
    mod, name = target.split(".")
    return getattr(getattr(bpy.ops, mod), name)('EXEC_DEFAULT', **props)


def _grid(name, z=0.0, size=4.0, subdiv=6):
    k = units.maya_unit()
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=subdiv, y_subdivisions=subdiv, size=size * k, location=(0, 0, z * k))
    ob = bpy.context.active_object
    ob.name = name
    return ob


def _cube(name="pCube1", z=0.0, size=2.0):
    k = units.maya_unit()
    bpy.ops.mesh.primitive_cube_add(size=size * k, location=(0, 0, z * k))
    ob = bpy.context.active_object
    ob.name = name
    return ob


def _cloth(ob):
    _select(ob)
    assert bpy.ops.allset.fx_ncloth() == {'FINISHED'}
    return fx_more.cloth_of(ob)


def _play(sc, last):
    for f in range(sc.frame_start, last + 1):
        sc.frame_set(f)


def _world_z(ob, depsgraph=None):
    depsgraph = depsgraph or bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(depsgraph)
    me = ev.to_mesh()
    zs = [(ob.matrix_world @ v.co).z for v in me.vertices]
    ev.to_mesh_clear()
    return zs


# --- the menu entries -------------------------------------------------------------------------------------------------

def test_every_new_item_is_mapped_with_a_blender_tooltip():
    for path in FX_PATHS + RENDER_PATHS + HS_PATHS:
        assert path in menu_map.MAP, path
        n = notices.NOTICES.get(path)
        assert n is not None and "Blender" in n[1], path
        tip = notices.tooltip(path, True)
        assert tip.startswith(f"Maya: {path}  →  Blender: "), tip
        kind, target, _props = menu_map.spec(path)
        if kind == "op":
            mod, name = target.split(".")
            assert hasattr(bpy.types, f"{mod.upper()}_OT_{name}") or target.split(".")[0] not in {"allset"}, target
    for twin, source in (("Stereo/Create", "Create/Cameras/Stereo Camera"),
                         ("Hypershade/Create/Image Plane", "Create/Free Image Plane"),
                         ("Effects/Collide with Effect", "Fluids/Make Collide")):
        assert menu_map.MAP[twin] == menu_map.MAP[source], twin


# --- nParticles ---------------------------------------------------------------------------------------------------------

def test_fill_object_fills_the_volume_on_a_grid():
    sc = _scene()
    cube = _cube(size=4.0)
    _select(cube)
    assert _run("nParticles/Fill Object") == {'FINISHED'}
    psys = cube.particle_systems[0]
    s = psys.settings
    assert psys.name.startswith("nParticle") and s.emit_from == 'VOLUME' and s.distribution == 'GRID'
    assert s.frame_start == s.frame_end == sc.frame_start and s.grid_resolution == fx_more.FILL_RESOLUTION
    sc.frame_set(2)
    ev = cube.evaluated_get(bpy.context.evaluated_depsgraph_get())
    alive = [p for p in ev.particle_systems[0].particles if p.alive_state == 'ALIVE']
    assert len(alive) > 50, len(alive)
    half = 2.0 * units.maya_unit() * 1.01
    assert all(abs(p.location.x) <= half and abs(p.location.y) <= half for p in alive)


def test_instancer_renders_the_selected_objects_on_the_particles():
    _scene()
    assert bpy.ops.allset.fx_emitter() == {'FINISHED'}
    emitter = bpy.context.active_object
    ball = _cube("pSphere1")
    _select(ball, emitter)
    assert _run("nParticles/Instancer") == {'FINISHED'}
    s = emitter.particle_systems[0].settings
    assert s.render_type == 'OBJECT' and s.instance_object == ball and s.particle_size == 1.0
    box = _cube("pCube2")
    _select(ball, box, emitter)
    assert _run("nParticles/Instancer") == {'FINISHED'}
    assert s.render_type == 'COLLECTION' and set(s.instance_collection.objects) == {ball, box}
    assert s.instance_collection.name.startswith("instancer")


def test_create_options_style_applies_to_new_particles():
    _scene()
    assert _run("nParticles/Create Options/Balls") == {'FINISHED'}
    assert bpy.context.window_manager.allset_nparticle_style == 'BALLS'
    bpy.ops.allset.fx_emitter()
    assert bpy.context.active_object.particle_systems[0].settings.display_method == 'CIRC'
    _run("nParticles/Create Options/Water")
    bpy.ops.allset.fx_emitter()
    assert bpy.context.active_object.particle_systems[0].settings.physics_type == 'FLUID'
    _run("nParticles/Create Options/Point")
    bpy.ops.allset.fx_emitter()
    s = bpy.context.active_object.particle_systems[0].settings
    assert s.display_method == 'DOT' and s.physics_type == 'NEWTON'


# --- Fluids -------------------------------------------------------------------------------------------------------------

def _domain(x=5.0):
    dom = _cube("fluid1", size=10.0)
    dom.location.x = x * units.maya_unit()
    md = dom.modifiers.new("Fluid", 'FLUID')
    md.fluid_type = 'DOMAIN'
    return dom, md


def test_fluid_emitter_and_resolution():
    _scene()
    dom, md = _domain()
    _select(dom)
    assert _run("Fluids/Add/Edit Contents/Emitter") == {'FINISHED'}
    em = bpy.context.active_object
    assert em.name == "fluidEmitter1" and em.hide_render
    flow = next(m for m in em.modifiers if m.type == 'FLUID')
    assert flow.fluid_type == 'FLOW' and flow.flow_settings.flow_behavior == 'INFLOW'
    assert (em.location - dom.location).length < 1e-6
    radius = max(v.co.length for v in em.data.vertices)
    assert abs(radius - fx_more.EMITTER_RADIUS * units.maya_unit()) < 1e-5, radius
    _select(dom)
    assert _run("Fluids/Edit Fluid Resolution", resolution=24) == {'FINISHED'}
    assert md.domain_settings.resolution_max == 24


# --- nCloth -------------------------------------------------------------------------------------------------------------

def test_rest_shape_items():
    _scene()
    rest = _grid("restMesh", z=3.0)
    cloth = _grid("pPlane1")
    md = _cloth(cloth)
    _select(rest, cloth)
    assert _run("nCloth/Rest Shape/Connect Selected Mesh to Rest Shape") == {'FINISHED'}
    assert md.settings.rest_shape_key is not None and md.settings.rest_shape_key.name == "restMesh"
    _select(cloth)
    assert _run("nCloth/Rest Shape/Set Rest To Start Shape") == {'FINISHED'}
    assert md.settings.rest_shape_key == cloth.data.shape_keys.reference_key


def test_paint_vertex_properties_fill_the_cloth_slots():
    _scene()
    cloth = _grid("pPlane1")
    md = _cloth(cloth)
    for label, (slot, group) in (("Input Attract", ("vertex_group_mass", "nClothInputAttract")),
                                 ("Bend", ("vertex_group_bending", "nClothBend")),
                                 ("Rest Length Scale", ("vertex_group_shrink", "nClothRestLengthScale"))):
        assert _run(f"nCloth/Paint Vertex Properties/{label}") == {'FINISHED'}
        assert bpy.context.mode == 'PAINT_WEIGHT'
        assert getattr(md.settings, slot) == group and cloth.vertex_groups.active.name == group
        bpy.ops.object.mode_set(mode='OBJECT')
        # weight 0 everywhere: painting starts from the cloth's own value
        assert all(g.weight == 0.0 for v in cloth.data.vertices for g in v.groups
                   if cloth.vertex_groups[g.group].name == group)


# --- nConstraint --------------------------------------------------------------------------------------------------------

def _edit_select(ob, indices):
    _select(ob)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    bm = bmesh.from_edit_mesh(ob.data)
    for f in bm.faces:
        f.select_set(False)
    for v in bm.verts:
        v.select_set(v.index in indices)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def _corner(ob):
    """Indices of the vertices on the grid's -y edge."""
    ys = [v.co.y for v in ob.data.vertices]
    lo = min(ys)
    return {v.index for v in ob.data.vertices if abs(v.co.y - lo) < 1e-6}


def test_transform_constraint_pins_and_hooks_the_vertices():
    sc = _scene()
    cloth = _grid("pPlane1", z=5.0)
    md = _cloth(cloth)
    edge = _corner(cloth)
    _edit_select(cloth, edge)
    assert _run("nConstraint/Transform Constraint") == {'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    empty = bpy.data.objects["dynamicConstraint1"]
    assert empty[fx_more.MARK] == cloth.name
    names = [m.name for m in cloth.modifiers]
    assert names.index("dynamicConstraint1") < names.index(md.name), names
    assert md.settings.vertex_group_mass == fx_more.PINS
    assert fx_more.members(cloth, fx_more.PINS) == edge == fx_more.members(cloth, "dynamicConstraint1")
    # the pinned edge stays up while the rest falls, and follows the empty
    _play(sc, 12)
    zs = _world_z(cloth)
    k = units.maya_unit()
    assert all(abs(zs[i] - 5.0 * k) < 1e-4 for i in edge), [zs[i] for i in edge]
    assert min(zs) < 5.0 * k - 1e-3
    sc.frame_set(1)
    empty.location.z += 2.0 * k
    bpy.context.view_layer.update()
    zs = _world_z(cloth)
    assert all(abs(zs[i] - 7.0 * k) < 1e-4 for i in edge), [zs[i] for i in edge]
    # membership commands work on the newest constraint
    extra = min(set(range(len(cloth.data.vertices))) - edge)
    _edit_select(cloth, {extra})
    assert _run("nConstraint/Add Members") == {'FINISHED'}
    assert fx_more.members(cloth, "dynamicConstraint1") == edge | {extra}
    assert _run("nConstraint/Remove Members") == {'FINISHED'}
    assert fx_more.members(cloth, "dynamicConstraint1") == edge
    _edit_select(cloth, set())
    assert _run("nConstraint/Select Members") == {'FINISHED'}
    assert set(fx_more.selected_verts(cloth)) == edge
    _edit_select(cloth, {extra})
    assert _run("nConstraint/Replace Members") == {'FINISHED'}
    assert fx_more.members(cloth, "dynamicConstraint1") == {extra} == fx_more.members(cloth, fx_more.PINS)
    # Disable Collision = the collision exclusion group
    assert _run("nConstraint/Disable Collision") == {'FINISHED'}
    cs = md.collision_settings
    assert cs.vertex_group_object_collisions == fx_more.NO_COLLIDE == cs.vertex_group_self_collisions
    assert fx_more.members(cloth, fx_more.NO_COLLIDE) == {extra}
    bpy.ops.object.mode_set(mode='OBJECT')
    # Remove Dynamic Constraint on the empty
    _select(empty)
    assert _run("nConstraint/Remove Dynamic Constraint") == {'FINISHED'}
    assert "dynamicConstraint1" not in bpy.data.objects and "dynamicConstraint1" not in cloth.modifiers
    assert cloth.vertex_groups.get("dynamicConstraint1") is None and md.settings.vertex_group_mass == ""
    # on the cloth: the rest (the collision group) goes too
    _select(cloth)
    assert _run("nConstraint/Remove Dynamic Constraint") == {'FINISHED'}
    assert cloth.vertex_groups.get(fx_more.NO_COLLIDE) is None and cs.vertex_group_object_collisions == ""


# --- Initial state / caches -----------------------------------------------------------------------------------------

def test_initial_state_and_transfer_cache_write_the_simulated_cloth():
    sc = _scene()
    cloth = _grid("pPlane1", z=5.0)
    _cloth(cloth)
    _play(sc, 8)
    fallen = sorted(_world_z(cloth))
    _select(cloth)
    assert _run("nCache/Transfer Cache To Input Mesh") == {'FINISHED'}
    assert any(md.type == 'CLOTH' for md in cloth.modifiers)
    base = sorted((cloth.matrix_world @ v.co).z for v in cloth.data.vertices)
    assert max(abs(a - b) for a, b in zip(base, fallen)) < 1e-5
    assert base[0] < 5.0 * units.maya_unit() - 1e-3


def test_initial_state_for_rigid_bodies_and_break_connections():
    sc = _scene()
    cube = _cube(z=10.0)
    _select(cube)
    assert _run("Fields/Solvers/Create Rigid Body Solver") == {'FINISHED'}
    assert sc.rigidbody_world is not None
    bpy.ops.allset.fx_rigid(type='ACTIVE')
    _play(sc, 10)
    z = cube.matrix_world.translation.z
    assert z < 10.0 * units.maya_unit()
    assert _run("Fields/Solvers/Initial State/Set for All Dynamic") == {'FINISHED'}
    assert abs(cube.location.z - z) < 1e-6
    _play(sc, 14)
    z2 = cube.matrix_world.translation.z
    _select(cube)
    assert _run("Fields/Solvers/Break Rigid Body Connections") == {'FINISHED'}
    assert cube.rigid_body is None and abs(cube.location.z - z2) < 1e-6


def test_rigid_body_active_passive_keys():
    sc = _scene()
    cube = _cube(z=10.0)
    _select(cube)
    bpy.ops.allset.fx_rigid(type='ACTIVE')
    sc.frame_set(1)
    assert _run("Fields/Solvers/Set Passive Key") == {'FINISHED'}
    assert cube.rigid_body.kinematic
    sc.frame_set(10)
    assert _run("Fields/Solvers/Set Active Key") == {'FINISHED'}
    assert not cube.rigid_body.kinematic
    fcs = {fc.data_path for fc in kit.fcurves(cube)}
    assert "rigid_body.kinematic" in fcs and "location" in fcs, fcs


def test_particle_disk_cache_bakes_to_disk():
    sc = _scene()
    sc.frame_end = 6
    folder = os.path.join(bpy.app.tempdir or os.environ.get("TEMP", "."), "issue123")
    os.makedirs(folder, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(folder, "disk_cache.blend"))
    bpy.ops.allset.fx_emitter()
    em = bpy.context.active_object
    _select(em)
    assert _run("nCache/Create Particle Disk Cache") == {'FINISHED'}
    pc = em.particle_systems[0].point_cache
    assert pc.use_disk_cache and pc.is_baked


# --- Fields / Effects -------------------------------------------------------------------------------------------------

def test_volume_curve_and_curve_flow():
    _scene()
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0))
    cu = bpy.context.active_object
    _select(cu)
    assert _run("Fields/Solvers/Volume Curve") == {'FINISHED'}
    assert cu.field.type == 'GUIDE'
    cu.field.type = 'NONE'
    assert _run("Effects/Flow/Create Curve Flow") == {'FINISHED'}
    assert cu.field.type == 'GUIDE'
    ems = [o for o in bpy.data.objects if o.get(fx_more.FLOW) == cu.name]
    assert len(ems) == 1 and ems[0].particle_systems
    first = cu.matrix_world @ cu.data.splines[0].bezier_points[0].co
    assert (ems[0].location - first).length < 1e-6
    _select(cu)
    assert _run("Effects/Flow/Delete Selected Flow") == {'FINISHED'}
    assert cu.field.type == 'NONE' and not [o for o in bpy.data.objects if fx_more.FLOW in o]


def test_collide_with_effect_is_a_fluid_effector():
    _scene()
    cube = _cube()
    _select(cube)
    assert _run("Effects/Collide with Effect") == {'FINISHED'}
    assert next(m for m in cube.modifiers if m.type == 'FLUID').fluid_type == 'EFFECTOR'


# --- Rendering ------------------------------------------------------------------------------------------------------------

def test_transfer_maps_sets_up_cycles_bake():
    sc = _scene()
    sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in {
        e.identifier for e in sc.render.bl_rna.properties["engine"].enum_items} else 'BLENDER_EEVEE'
    sc.render.bake.use_selected_to_active = False
    assert _run("Lighting/Shading/Transfer Maps...") == {'FINISHED'}
    assert sc.render.engine == 'CYCLES' and sc.render.bake.use_selected_to_active


def test_toon_fills_assign_shader_to_rgb_materials():
    _scene()
    cube = _cube()
    for label, kind in menu_map._TOON_FILLS.items():
        _select(cube)
        assert _run(f"Toon/Assign Fill Shader/{label}") == {'FINISHED'}, label
        mat = cube.active_material
        assert mat is not None and len(cube.material_slots) == 1, label
        types_ = {n.bl_idname for n in mat.node_tree.nodes}
        if kind == 'SOLID_COLOR':
            assert mat.name.startswith("surfaceShader"), mat.name
            continue
        assert {'ShaderNodeShaderToRGB', 'ShaderNodeValToRGB', 'ShaderNodeEmission'} <= types_, (label, types_)
        ramps = [n for n in mat.node_tree.nodes if n.bl_idname == 'ShaderNodeValToRGB']
        assert all(r.color_ramp.interpolation == 'CONSTANT' for r in ramps)
        out = next(n for n in mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL')
        assert out.inputs["Surface"].links[0].from_node.type == 'EMISSION'
        if kind == 'SHADED_BRIGHTNESS_THREE_TONE':
            assert len(ramps[0].color_ramp.elements) == 3
        if kind == 'CIRCLE_HIGHLIGHT':
            assert types_ & {'ShaderNodeBsdfGlossy', 'ShaderNodeBsdfAnisotropic'}, types_
        if kind in {'DARK_PROFILE', 'RIM_LIGHT'}:
            assert 'ShaderNodeLayerWeight' in types_


def test_camera_background_color_is_the_world_colour():
    sc = _scene()
    assert _run("Toon/Set Camera Background Color/persp", color=(0.2, 0.3, 0.4)) == {'FINISHED'}
    bg = render_more.world_background(sc, create=False)
    assert tuple(round(c, 4) for c in bg.inputs["Color"].default_value[:3]) == (0.2, 0.3, 0.4)
    out = next(n for n in sc.world.node_tree.nodes if n.type == 'OUTPUT_WORLD')
    assert out.inputs["Surface"].links[0].from_node == bg


def test_toon_reverse_surfaces_flips_whole_meshes():
    _scene()
    cube = _cube()
    _select(cube)
    before = [p.normal.copy() for p in cube.data.polygons]
    assert bpy.ops.allset.menu_item(item="Toon/Reverse Surfaces") == {'FINISHED'}
    assert bpy.context.mode == 'OBJECT'
    after = [p.normal for p in cube.data.polygons]
    assert all((a + b).length < 1e-5 for a, b in zip(before, after))


def test_stereo_create_turns_stereoscopy_on():
    sc = _scene()
    sc.render.use_multiview = False
    assert _run("Stereo/Create") == {'FINISHED'}
    assert sc.render.use_multiview and bpy.context.active_object.name.startswith("stereoCamera")


# --- Hypershade -----------------------------------------------------------------------------------------------------------

def test_hypershade_extra_materials():
    sc = _scene()
    want = {'VOLUME_SHADER': 'ShaderNodeVolumePrincipled', 'VOLUME_FOG': 'ShaderNodeVolumeScatter',
            'LIGHT_FOG': 'ShaderNodeVolumeScatter', 'HAIR_PHYSICAL': 'ShaderNodeBsdfHairPrincipled',
            'HAIR_TUBE': 'ShaderNodeBsdfHairPrincipled', 'USD_PREVIEW': 'ShaderNodeBsdfPrincipled',
            'SHADING_MAP': 'ShaderNodeShaderToRGB'}
    for label, kind in editor_menu_map.HS_EXTRA.items():
        before = set(bpy.data.materials)
        assert _run(f"Hypershade/Create/{label}") == {'FINISHED'}, label
        new = set(bpy.data.materials) - before
        if kind == 'ENV_FOG':
            assert not new
            out = next(n for n in sc.world.node_tree.nodes if n.type == 'OUTPUT_WORLD')
            assert out.inputs["Volume"].links[0].from_node.bl_idname == 'ShaderNodeVolumePrincipled'
            continue
        (mat,) = new
        assert mat.use_fake_user and want[kind] in {n.bl_idname for n in mat.node_tree.nodes}, (label, mat.name)
        out = next(n for n in mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL')
        socket = "Volume" if kind in {'VOLUME_SHADER', 'VOLUME_FOG', 'LIGHT_FOG'} else "Surface"
        assert out.inputs[socket].is_linked, (label, socket)


def test_hypershade_nodes_add_the_blender_node():
    _scene()
    for label, node in (("General Utilities/Uv Chooser", 'ShaderNodeUVMap'),
                        ("Particle Utilities/Particle Sampler", 'ShaderNodeParticleInfo'),
                        ("Environment Textures/Env Sky", 'ShaderNodeTexSky'),
                        ("Color Utilities/Color Correct", 'ShaderNodeHueSaturation')):
        assert _run(f"Hypershade/Create/{label}") == {'FINISHED'}, label
        assert any(n.bl_idname == node and n.label == label.rsplit("/", 1)[-1]
                   for m in bpy.data.materials if m.node_tree for n in m.node_tree.nodes), label
