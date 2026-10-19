"""Step 68: Maya FX — simulation scale (decision 10), nucleus, nParticles emitter / Emit from Object, nCloth, Passive,
rigid bodies, nCache. Plan + measurements: docs/steps/step_68.md; GUI: tests/gui/gui_step68_fx.py."""

import types
from importlib import import_module

import bpy

import kit

fx = import_module(kit.MODULE + ".operators.fx")
units = import_module(kit.MODULE + ".operators.units")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
shelf_map = import_module(kit.MODULE + ".ui.shelf_map")
ae = import_module(kit.MODULE + ".ui.attribute_editor")
ae_layout = import_module(kit.MODULE + ".ui.ae_layout")


class Rec:
    def __init__(self, log=None):
        self.log = [] if log is None else log

    def __getattr__(self, name):
        def call(*args, **kw):
            self.log.append((name, args, kw))
            if name == "panel":
                return Rec(self.log), Rec(self.log)
            if name == "operator":
                props = types.SimpleNamespace()
                self.log[-1] = (name, args, kw, props)
                return props
            return Rec(self.log)
        return call

    def __setattr__(self, name, value):
        if name == "log":
            object.__setattr__(self, name, value)


def _scene(cm=True):
    """Fresh objects; cm = the Allset template's units (m + cm display: one Maya unit = 0.01 BU)."""
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for ps in list(bpy.data.particles):
        bpy.data.particles.remove(ps)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0
    sc.unit_settings.length_unit = 'CENTIMETERS' if cm else 'METERS'
    sc.frame_start, sc.frame_end, sc.use_preview_range = 1, 120, False
    sc.render.fps, sc.render.fps_base = 24, 1.0
    if sc.rigidbody_world is not None:
        bpy.ops.rigidbody.world_remove()
    nuc = sc.allset_nucleus
    nuc["exists"] = False
    nuc["space_scale"], nuc["gravity"], nuc["substeps"] = 1.0, fx.MAYA_GRAVITY, fx.MAYA_SUBSTEPS
    nuc["gravity_direction"] = (0.0, -1.0, 0.0)
    sc.gravity = (0.0, 0.0, -9.81)
    sc.frame_set(1)
    return sc


def _grid(name, size_units, z_units, subdiv=10):
    k = units.maya_unit()
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=subdiv, y_subdivisions=subdiv, size=size_units * k,
                                    location=(0, 0, z_units * k))
    ob = bpy.context.active_object
    ob.name = name
    return ob


def _select(*obs):
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0] if obs else None


def _play(sc, last):
    for f in range(sc.frame_start, last + 1):
        sc.frame_set(f)


# --- scale --------------------------------------------------------------------------------------

def test_scale_formulas():
    sc = _scene(cm=True)
    nuc = sc.allset_nucleus
    assert abs(units.maya_unit() - 0.01) < 1e-9
    assert abs(fx.sim_scale(sc) - 0.01) < 1e-9
    g = fx.gravity_vector(sc)
    assert abs(g[0]) < 1e-9 and abs(g[1]) < 1e-9 and abs(g[2] + 0.098) < 1e-7, g
    nuc["space_scale"] = 0.01                      # real centimetres
    assert abs(fx.gravity_vector(sc)[2] + 9.8) < 1e-6
    nuc["space_scale"] = 1.0
    assert fx.maya_to_blender((0, 0, 1)) == (0, -1, 0) and fx.maya_to_blender((0, 1, 0)) == (0, 0, 1)
    assert fx.cloth_quality(3) == 5 and fx.cloth_quality(6) == 10 and fx.rigid_substeps(3) == 10
    sc = _scene(cm=False)
    assert abs(fx.gravity_vector(sc)[2] + 9.8) < 1e-5


# --- emitter --------------------------------------------------------------------------------------

def _fall(cm):
    sc = _scene(cm)
    assert bpy.ops.allset.fx_emitter() == {'FINISHED'}
    ob = bpy.data.objects["emitter1"]
    _play(sc, 25)                                   # one second at 24 fps
    psys = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).particle_systems[0]
    zs = [p.location.z for p in psys.particles if p.alive_state == 'ALIVE']
    return min(zs) / units.maya_unit(), len(zs)        # the oldest particles: one second of fall


def test_create_emitter():
    sc = _scene(cm=True)
    assert bpy.ops.allset.fx_emitter() == {'FINISHED'}
    ob = bpy.data.objects["emitter1"]
    assert bpy.context.active_object == ob and ob.select_get()
    assert len(ob.data.vertices) == 1 and tuple(ob.location) == (0, 0, 0) and ob.hide_render
    psys = ob.particle_systems[0]
    st = psys.settings
    assert psys.name == "nParticle1" and st.name == "nParticle1", (psys.name, st.name)
    assert st.emit_from == 'VERT' and st.count == 500 and (st.frame_start, st.frame_end) == (1, 120), st.count
    # Blender's hard minimum particle size is 0.001 m (= 0.1 unit in a cm scene; step 68 「계획」)
    assert abs(st.particle_size - 0.001) < 1e-7 and abs(st.factor_random - 0.01) < 1e-7, (st.particle_size, st.factor_random)
    assert abs(st.display_size - 0.001) < 1e-7, "viewport dots in Maya units, not 10-unit balls"
    assert sc.allset_nucleus.exists and abs(sc.gravity.z + 0.098) < 1e-6
    # a second emitter: Maya numbering
    bpy.ops.allset.fx_emitter()
    assert "emitter2" in bpy.data.objects and bpy.data.objects["emitter2"].particle_systems[0].name == "nParticle2"


def test_particles_fall_like_maya():
    cm, n = _fall(cm=True)
    m, _n = _fall(cm=False)
    # same motion in Maya units in a cm scene and a m scene (decision 10); the oldest fell ~0.5 * 9.8 * 1^2 = 4.9
    # units (+/- the omni speed of 1 unit/s)
    assert n > 50, n
    assert abs(cm - m) < 1e-3 * abs(m), (cm, m)
    assert -6.5 < cm < -3.5, cm


def test_emit_from_object():
    _scene(cm=True)
    a, b = _grid("pPlane1", 1, 0), _grid("pPlane2", 1, 3)
    _select(a, b)
    assert bpy.ops.allset.fx_emit_from_object() == {'FINISHED'}
    assert [o.particle_systems[0].name for o in (a, b)] == ["nParticle1", "nParticle2"]


# --- nCloth / colliders / rigid bodies ------------------------------------------------------------------

def test_ncloth_on_every_selected_and_nucleus():
    sc = _scene(cm=True)
    a, b = _grid("pPlane1", 1, 2), _grid("pPlane2", 1, 4)
    _select(a, b)
    assert bpy.ops.allset.fx_ncloth() == {'FINISHED'}
    mds = [next(m for m in o.modifiers if m.type == 'CLOTH') for o in (a, b)]
    assert [m.name for m in mds] == ["nCloth1", "nCloth2"]
    for md in mds:
        # 0.015 x maya_unit, clamped to Blender's hard minimum 0.001 m (= 0.1 unit, Maya's nCloth thickness [K])
        assert abs(md.collision_settings.distance_min - 0.001) < 1e-7, md.collision_settings.distance_min
        assert abs(md.settings.tension_stiffness - 15 * 0.01) < 1e-6, md.settings.tension_stiffness
        assert md.settings.quality == 5
    # nucleus: Space Scale 0.01 = real cm: gravity 9.8, stiffness back to Blender's
    sc.allset_nucleus.space_scale = 0.01
    assert abs(sc.gravity.z + 9.8) < 1e-5
    assert abs(mds[0].settings.tension_stiffness - 15) < 1e-4
    sc.allset_nucleus.space_scale = 1.0
    sc.allset_nucleus.substeps = 6
    assert all(md.settings.quality == 10 for md in mds)
    sc.allset_nucleus.gravity_direction = (1.0, 0.0, 0.0)
    assert abs(sc.gravity.x - 0.098) < 1e-6 and abs(sc.gravity.z) < 1e-7
    # Remove nCloth
    _select(b)
    bpy.ops.allset.fx_remove_ncloth()
    assert not any(m.type == 'CLOTH' for m in b.modifiers) and fx.CLOTH_G_PROP not in b


def test_cloth_lands_on_passive_collider():
    """A 1 unit cloth falls on a passive ground plane and rests on it: with Blender's 0.015 m collision distance it
    would hover 1.5 units above (research/maya/workflows/fx.md:76)."""
    sc = _scene(cm=True)
    ground = _grid("pPlane1", 10, 0, subdiv=2)
    _select(ground)
    assert bpy.ops.allset.fx_passive() == {'FINISHED'}
    assert abs(ground.collision.thickness_outer - 0.001) < 1e-7      # 0.02 x 0.01, clamped to 0.001 m
    assert ground.modifiers[-1].name == "nRigid1"
    cloth = _grid("pPlane2", 1, 2)
    _select(cloth)
    bpy.ops.allset.fx_ncloth()
    _play(sc, 60)
    me = cloth.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    zs = [(cloth.matrix_world @ v.co).z / units.maya_unit() for v in me.vertices]
    cloth.to_mesh_clear()
    assert -0.2 < min(zs) and max(zs) < 0.5, (min(zs), max(zs))


def test_rigid_bodies_in_maya_units():
    sc = _scene(cm=True)
    a, b = _grid("pPlane1", 1, 0), _grid("pPlane2", 1, 3)
    _select(a, b)
    assert bpy.ops.allset.fx_rigid(type='ACTIVE') == {'FINISHED'}
    for ob in (a, b):
        assert ob.rigid_body is not None and ob.rigid_body.type == 'ACTIVE'
        assert abs(ob.rigid_body.collision_margin - 0.04 * 0.01) < 1e-7
    assert sc.rigidbody_world.substeps_per_frame == 10 and abs(sc.gravity.z + 0.098) < 1e-6


# --- nCache -------------------------------------------------------------------------------------------

def test_ncache_bake_and_delete():
    sc = _scene(cm=True)
    sc.frame_end = 10
    cloth = _grid("pPlane1", 1, 2, subdiv=3)
    _select(cloth)
    bpy.ops.allset.fx_ncloth()
    other = _grid("pPlane2", 1, 4, subdiv=3)
    _select(other)
    bpy.ops.allset.fx_ncloth()
    pc = cloth.modifiers["nCloth1"].point_cache
    pc2 = other.modifiers["nCloth2"].point_cache
    _select(cloth)
    assert bpy.ops.allset.ncache(action='CREATE', kind='NOBJECT') == {'FINISHED'}
    assert pc.is_baked and not pc2.is_baked, "only the selection"
    assert bpy.ops.allset.ncache(action='DELETE', kind='ALL') == {'FINISHED'}
    assert not pc.is_baked
    _select()
    bpy.ops.allset.ncache(action='CREATE', kind='NOBJECT')
    assert pc.is_baked and pc2.is_baked, "nothing selected = the whole scene"
    bpy.ops.allset.ncache(action='DELETE', kind='NOBJECT')
    assert bpy.ops.allset.ncache(action='CREATE', kind='FLUID') == {'CANCELLED'}, "no fluid domain"


# --- AE / menus ---------------------------------------------------------------------------------------

def test_ae_nucleus_tab():
    _scene(cm=True)
    plane = _grid("pPlane1", 1, 2)
    assert not any(t[0] == "NUC" for t in ae.tabs(plane)), "no nucleus before kit FX"
    _select(plane)
    bpy.ops.allset.fx_ncloth()
    assert ("NUC", "nucleus1", "nucleus") in ae.tabs(plane)
    assert ae.tab_target(plane, "NUC") == bpy.context.scene.allset_nucleus
    ae.set_tab(bpy.context, "NUC")
    rec = Rec()
    ae.draw(rec, bpy.context, plane)
    props = [e[1][1] for e in rec.log if e[0] == "prop"]
    for attr in ("gravity", "gravity_direction", "substeps", "space_scale"):
        assert attr in props, (attr, props)
    labels = " ".join(e[2].get("text", "") for e in rec.log if e[0] == "label")
    assert "nucleus1" in labels and "no nucleus node" not in labels, labels
    # the Blender notice is a tooltip of the head row (step 106)
    tips = [e[3].text for e in rec.log if e[0] == "operator" and e[1][:1] == ("allset.tip",)]
    assert any("no nucleus node" in t for t in tips), tips


def test_fx_menu_and_shelf_mapping():
    assert menu_map.MAP["nParticles/Create Emitter"] == "allset.fx_emitter"
    assert menu_map.MAP["nParticles/Emit from Object"] == "allset.fx_emit_from_object"
    assert menu_map.MAP["nCloth/Create nCloth"] == "allset.fx_ncloth"
    assert menu_map.MAP["nCloth/Create Passive Collider"] == "allset.fx_passive"
    assert menu_map.MAP["nCache/Create New Cache/nObject"][0] == "allset.ncache"
    assert menu_map.MAP["Fields/Solvers/Create Active Rigid Body"] == ("allset.fx_rigid", {"type": 'ACTIVE'})
    assert shelf_map.BY_COMMAND["NCreateEmitter"][0] == "allset.fx_emitter"
    assert shelf_map.BY_COMMAND["NEmitFromObject"][0] == "allset.fx_emit_from_object"
    assert shelf_map.BY_LABEL["FX/Create nCloth"][0] == "allset.fx_ncloth"
    flat = repr(menu_map.MAP) + repr(shelf_map.BY_COMMAND) + repr(shelf_map.BY_LABEL)
    assert "particle_system_add" not in flat and "ptcache.bake_all" not in flat
