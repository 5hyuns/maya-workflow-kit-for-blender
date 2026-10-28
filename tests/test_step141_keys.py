"""Step 141 lane KEYS: Ctrl+A = Attribute Editor / Channel Box in every mode (#65), UV / Image Editor Alt+RMB dolly
without Blender's Zoom Axis preference (B4), undo-depth hint (B6), joint names restart at joint1 (#73), Gravity /
Newton field defaults (#72). Plan: docs/steps/step_141.md; notes: docs/steps/step_141_keys.md;
GUI: tests/gui/gui_step141_keys.py."""

from importlib import import_module
from pathlib import Path

import bpy
from mathutils import Vector

import kit

maya_patches = import_module(kit.MODULE + ".keymap.maya_patches")
mapping = import_module(kit.MODULE + ".keymap.mapping")
view = import_module(kit.MODULE + ".operators.view")
joints = import_module(kit.MODULE + ".operators.joints")
create = import_module(kit.MODULE + ".operators.create")
fx = import_module(kit.MODULE + ".operators.fx")
units = import_module(kit.MODULE + ".operators.units")
preferences = import_module(kit.MODULE + ".preferences")
welcome = import_module(kit.MODULE + ".welcome")

ROOT = Path(kit.__file__).resolve().parent.parent


def _items(km, t, **mods):
    return [k for k in kit.maya_kc().keymaps[km].keymap_items
            if k.active and k.type == t and k.value in ('PRESS', 'CLICK', 'CLICK_DRAG')
            and all(getattr(k, m) == mods.get(m, False) for m in ("shift", "ctrl", "alt", "oskey"))]


# --- #65 Ctrl+A ------------------------------------------------------------------------------------------------------

def test_ctrl_a_is_ae_toggle_in_every_mode():
    kms = ["Object Mode"] + [km for km, _ in maya_patches.CTRL_A_MODES]
    assert {"Mesh", "Pose", "Curve", "Armature", "UV Editor"} <= set(kms)
    for km in kms:
        got = [k.idname for k in _items(km, 'A', ctrl=True)]
        assert got == ["allset.ae_toggle"], (km, got)
        sel = [k for k in _items(km, 'A', ctrl=True, shift=True)]
        assert [k.idname.endswith("select_all") and k.properties.action == 'SELECT' for k in sel] == [True], \
            (km, [(k.idname, getattr(k.properties, "action", None)) for k in sel])


def test_alt_d_select_none_in_component_and_pose_modes():
    pose = [(k.idname, getattr(k.properties, "action", None)) for k in _items("Pose", 'D', alt=True)]
    assert pose == [("allset.select_none", None)], pose
    for km in ("Mesh", "Curve", "Armature", "Lattice", "Metaball"):
        assert [k.idname for k in _items(km, 'D', alt=True)] == ["allset.select_none"], km


def test_ctrl_a_text_editors_keep_select_all():
    # typing contexts keep their own select-all (Maya's Script Editor is a text field there too)
    for km, idname in (("Text", "text.select_all"), ("Console", "console.select_all"), ("Font", "font.select_all")):
        assert idname in [k.idname for k in _items(km, 'A', ctrl=True)], km


def test_ctrl_a_same_in_every_ic_version():
    # patches are strict only on 4.5: the 5.x IC data must have the same Ctrl+A items, or the 5.x keymap drifts
    for name in ("ic_4_5", "ic_5_0", "ic_5_1", "ic_5_2"):
        data = import_module(f"{kit.MODULE}.keymap.{name}").DATA
        by = {n: d["items"] for n, _p, d in data}
        for km, idname in maya_patches.CTRL_A_MODES:
            ctrl_a = [it for it in by[km] if it[0] == idname and it[1]["type"] == "A" and it[1].get("ctrl")
                      and not it[1].get("shift")]
            assert ctrl_a, (name, km)


def test_mapping_row_notes_every_mode():
    e = mapping.ENTRIES["ShowAttributeEditorOrChannelBox"]
    assert e["status"] == "KIT" and "step 141" in e["note"]
    doc = (ROOT / "docs" / "keymap_mapping.md").read_text(encoding="utf-8")
    row = next(ln for ln in doc.splitlines() if "ShowAttributeEditorOrChannelBox" in ln)
    assert "mesh.select_all" not in row and "Mesh: `allset.ae_toggle`" in row, row


# --- B4 UV / Image Editor dolly ----------------------------------------------------------------------------------

def test_image_editor_alt_rmb_is_kit_dolly():
    got = [k.idname for k in _items("Image", 'RIGHTMOUSE', alt=True)]
    assert got == ["allset.dolly_2d"], got
    assert getattr(bpy.types, "ALLSET_OT_dolly_2d", None) is not None


def test_dolly_2d_direction_and_maths():
    f = view.dolly_zoom_factor
    assert f(150, 0) > 1.0 and f(-150, 0) < 1.0, "drag right = zoom in, left = out (Maya)"
    assert abs(f(150, 0) - 2.0) < 1e-9 and abs(f(-150, 0) - 0.5) < 1e-9
    assert abs(f(75, 0) * f(75, 0) - f(150, 0)) < 1e-9, "steps multiply: the drag path doesn't matter"
    assert abs(f(300, 0, ui_scale=2.0) - 2.0) < 1e-9, "pixels follow the UI scale"
    # the 3D dolly and the 2D dolly agree: zoom factor = start distance / new distance
    assert abs(f(90, 30) - 1.0 / view.dolly_distance(1.0, 90, 30)) < 1e-9


def test_dolly_2d_zooms_an_image_editor():
    """exec path of a drag step: image.view_zoom(factor) under an Image Editor override (headless: the zoom getter
    reads the view, which only updates on a redraw, so this checks the call runs and is counted)."""
    win = bpy.context.window_manager.windows[0]
    area = max(win.screen.areas, key=lambda a: a.width * a.height)
    old = area.ui_type
    try:
        area.ui_type = 'UV'
        region = next(r for r in area.regions if r.type == 'WINDOW')
        with bpy.context.temp_override(window=win, area=area, region=region, space_data=area.spaces.active):
            assert bpy.ops.allset.dolly_2d.poll()
            res = bpy.ops.image.view_zoom('EXEC_DEFAULT', factor=view.dolly_zoom_factor(150, 0))
            assert res == {'FINISHED'}, res
    finally:
        area.ui_type = old


# --- B6 undo depth hint ------------------------------------------------------------------------------------------

def test_undo_hint_readme_and_app():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    sec = readme.split("## Recommended setup", 1)[1].split("\n---", 1)[0]
    assert "Undo Steps" in sec and "256" in sec and "32" in sec and "unlimited" in sec, sec
    steps = bpy.context.preferences.edit.undo_steps
    hint = preferences.undo_hint(bpy.context)
    if steps < 256:
        assert hint and "Undo Steps" in hint and str(steps) in hint, hint
    else:
        assert hint is None
    assert any("Undo" in p and "256" in p for p in welcome.PARAGRAPHS)
    assert bpy.context.preferences.edit.undo_steps == steps, "read only"


def test_undo_hint_in_preferences_panel():
    """The add-on preferences draw the hint (factory Undo Steps 32 < 256)."""
    if bpy.context.preferences.edit.undo_steps >= 256:
        return
    labels = []

    class L:
        def __getattr__(self, name):
            def call(*a, **kw):
                if name == "label":
                    labels.append(kw.get("text", ""))
                return L()
            return call

        def __setattr__(self, name, value):
            pass

    prefs = preferences.get()
    prefs.__class__.draw(type("P", (), {"layout": L(), "maya_mode": prefs.maya_mode,
                                        "__getattr__": lambda s, n: getattr(prefs, n)})(), bpy.context)
    assert any("Undo Steps" in t for t in labels), labels


# --- #73 joint names ------------------------------------------------------------------------------------------------

def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)


def _skeleton(n=3):
    ob = joints.new_skeleton(bpy.context)
    parent, names = None, []
    for i in range(n):
        parent = joints.add_joint(ob, Vector((i, 0.0, 1.0)), parent, length=0.5)
        names.append(parent)
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob, names


def test_joint_names_restart_after_delete():
    _clear()
    ob, names = _skeleton()
    assert names == ["joint1", "joint2", "joint3"], names
    _ob2, names2 = _skeleton(2)
    assert names2 == ["joint4", "joint5"], "joint names are scene-wide while skeleton1 exists"
    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    for o in list(bpy.data.objects):
        o.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.delete()
    assert any(a.users == 0 for a in bpy.data.armatures), "Blender keeps the deleted skeletons' data until a purge"
    ob3, names3 = _skeleton(2)
    assert names3 == ["joint1", "joint2"], names3
    assert ob3.name == "skeleton1", ob3.name


def test_joint_names_skip_existing_after_partial_delete():
    _clear()
    a, _ = _skeleton(2)
    b, _ = _skeleton(1)                    # joint3
    for o in bpy.context.selected_objects:
        o.select_set(False)
    a.select_set(True)
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.delete()
    _c, names = _skeleton(3)
    assert names == ["joint4", "joint5", "joint6"], names   # Maya (step 208): one past the highest, no gap filling


# --- #72 Gravity / Newton --------------------------------------------------------------------------------------------

def _scene(cm=True):
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for ps in list(bpy.data.particles):
        bpy.data.particles.remove(ps)
    sc = bpy.context.scene
    us = sc.unit_settings
    us.system, us.scale_length, us.length_unit = 'METRIC', 1.0, 'CENTIMETERS' if cm else 'METERS'
    sc.frame_start, sc.frame_end, sc.use_preview_range = 1, 120, False
    sc.render.fps, sc.render.fps_base = 24, 1.0
    nuc = sc.allset_nucleus
    nuc["exists"] = False
    nuc["space_scale"], nuc["gravity"] = 1.0, fx.MAYA_GRAVITY
    nuc["gravity_direction"] = (0.0, -1.0, 0.0)
    sc.gravity = (0.0, 0.0, -9.81)
    sc.frame_set(1)
    return sc


def test_field_strengths_follow_maya():
    for cm in (True, False):
        sc = _scene(cm)
        g = fx.sim_scale(sc)
        assert abs(g - (0.01 if cm else 1.0)) < 1e-9
        assert bpy.ops.allset.create(kind='FIELD_GRAVITY') == {'FINISHED'}
        grav = bpy.data.objects["gravityField1"]
        assert grav.field.type == 'WIND' and abs(grav.field.strength - 9.8 * g) < 1e-6, grav.field.strength
        assert grav.field.flow == 0.0, "a constant pull, no drag"
        assert grav.matrix_world.to_3x3().col[2].z < -0.99, "Maya gravity direction (0, -1, 0) = Blender -Z"
        assert bpy.ops.allset.create(kind='FIELD_NEWTON') == {'FINISHED'}
        newton = bpy.data.objects["newtonField1"]
        assert newton.field.type == 'FORCE' and abs(newton.field.strength + 5.0 * g) < 1e-6, newton.field.strength
        # Space Scale 0.01 (centimetres at their real size): the field is 100 times stronger, like the nucleus
        sc.allset_nucleus["space_scale"] = 0.01
        bpy.ops.allset.create(kind='FIELD_GRAVITY')
        assert abs(bpy.data.objects["gravityField2"].field.strength - 9.8 * g / 0.01) < 1e-6
        sc.allset_nucleus["space_scale"] = 1.0


def _emit_at(sc, x_units=0.0):
    assert bpy.ops.allset.fx_emitter() == {'FINISHED'}
    em = bpy.data.objects["emitter1"]
    em.location.x = x_units * units.maya_unit()
    st = em.particle_systems[0].settings
    st.effector_weights.gravity = 0.0          # the field alone
    st.normal_factor = st.factor_random = 0.0
    return em


def _alive(sc, em, last=25):
    for f in range(sc.frame_start, last + 1):
        sc.frame_set(f)
    psys = em.evaluated_get(bpy.context.evaluated_depsgraph_get()).particle_systems[0]
    k = units.maya_unit()
    return [p.location / k for p in psys.particles if p.alive_state == 'ALIVE']


def test_gravity_field_drops_particles_like_maya():
    """A Maya gravity field (9.8 down) drops particles like the nucleus gravity 9.8 (step 68), in a cm scene and in a
    m scene alike."""
    out = []
    for cm in (True, False):
        sc = _scene(cm)
        em = _emit_at(sc)
        em.particle_systems[0].settings.effector_weights.gravity = 1.0      # reference: the nucleus gravity
        ref = min(p.z for p in _alive(sc, em))
        sc = _scene(cm)
        em = _emit_at(sc)
        bpy.ops.allset.create(kind='FIELD_GRAVITY')
        pts = _alive(sc, em)
        assert len(pts) > 50, len(pts)
        got = min(p.z for p in pts)
        print("gravity field fall", cm, got, "nucleus", ref)
        assert max(abs(p.x) + abs(p.y) for p in pts) < 0.05, "straight down"
        assert abs(got - ref) < 0.03 * abs(ref), (cm, got, ref)
        out.append(got)
    assert abs(out[0] - out[1]) < 0.02 * abs(out[1]), out


def test_newton_field_attracts():
    sc = _scene(True)
    em = _emit_at(sc, x_units=5.0)
    bpy.ops.allset.create(kind='FIELD_NEWTON')
    pts = _alive(sc, em)
    assert len(pts) > 50
    # pulled in towards the field at the origin: 5 units/s² for one second ~ 2.5 units
    moved = 5.0 - min(p.x for p in pts)
    assert 1.8 < moved < 3.2, moved
