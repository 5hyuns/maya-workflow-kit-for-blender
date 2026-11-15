"""Maya items that were greyed: Set Range to Sound Length, HUD Current Frame / Focal Length / Scene Timecode /
In-view Messages, Display > Animation submenu (Joint Labels), Mesh > Clipboard Actions, Edit > Transfer Attribute
Values, Edit > LOD (behaviour measured in Maya 2026, see operators/attr_clipboard.py and operators/lod.py)."""

import os
import struct
import tempfile
import wave
from importlib import import_module

import bmesh
import bpy

import kit

menu_map = import_module(kit.MODULE + ".ui.menu_map")
furniture = import_module(kit.MODULE + ".ui.view_furniture")
clip = import_module(kit.MODULE + ".operators.attr_clipboard")
lod = import_module(kit.MODULE + ".operators.lod")


def _clear():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _run(path):
    kind, target, props = menu_map.spec(path)
    mod, _, name = target.partition(".")
    try:
        return getattr(getattr(bpy.ops, mod), name)(**props)
    except RuntimeError:                # an ERROR report (Maya's error): nothing done
        return {'CANCELLED'}


def _mesh(name, faces=1, x=0.0):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    if faces == 6:
        bmesh.ops.create_cube(bm, size=2.0)
    else:
        bmesh.ops.create_grid(bm, x_segments=faces + 1, y_segments=1, size=1.0)
    bm.loops.layers.uv.new("map1")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location.x = x
    return ob


def _select(*obs, active=None):
    for o in bpy.context.scene.objects:
        o.select_set(o in obs)
    bpy.context.view_layer.objects.active = active or (obs[-1] if obs else None)


def test_menu_paths():
    assert menu_map.is_submenu("Display/Animation", [("x",)]) and "Display/Animation" in menu_map.MAP
    assert menu_map.spec("Display/Animation/Joint Labels")[1] == "allset.joint_label_toggle"
    assert menu_map.OBJECT_MODE["Display/Show/All Components"] == ('ALL', 'VERT')
    for p in ("Display/Heads Up Display/Current Frame", "Display/Heads Up Display/Focal Length",
              "Display/Heads Up Display/Scene Timecode", "Display/Heads Up Display/In-view Messages"):
        assert menu_map.spec(p) is not None, p


def test_hud_lines():
    assert furniture.timecode(1, 24) == "00:00:00:01"
    assert furniture.timecode(24 * 3661 + 5, 24) == "01:01:01:05"

    class P:
        maya_hud_current_frame = maya_hud_focal_length = maya_hud_scene_timecode = True
    scene = bpy.context.scene
    lines = furniture.hud_lines(P, scene, 7.0, 35.0)
    assert [a for a, _b in lines] == ["Frame:", "Focal Length:", "Scene Timecode:"]   # Maya blocks 10, 17, 18
    assert lines[0][1] == "7" and lines[1][1] == "35.000"
    P.maya_hud_focal_length = False
    assert [a for a, _b in furniture.hud_lines(P, scene, 7.0, 35.0)] == ["Frame:", "Scene Timecode:"]


def test_set_range_to_sound_length():
    scene = bpy.context.scene
    if scene.sequence_editor:
        scene.sequence_editor_clear()
    assert _run("Playback/Set Range to/Sound Length") == {'CANCELLED'}       # Maya: "No sound displayed..."
    path = os.path.join(tempfile.mkdtemp(), "beep.wav")
    rate = 8000
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(struct.pack("<h", 0) * rate * 2)       # 2 seconds
    scene.render.fps, scene.render.fps_base = 24, 1.0
    scene.sequence_editor_create()
    from importlib import import_module as im
    strips = im(kit.MODULE + ".compat").strips(scene.sequence_editor)
    strips.new_sound("beep", path, 1, 10)
    _run("Playback/Set Range to/Sound Length")
    assert scene.use_preview_range
    assert (scene.frame_preview_start, scene.frame_preview_end) == (10, 58)   # offset .. offset + 48 frames
    scene.sequence_editor_clear()


def test_clipboard_copy_paste_clear():
    _clear()
    red, blue = bpy.data.materials.new("red"), bpy.data.materials.new("blue")
    src = _mesh("src", faces=6)
    src.data.materials.append(blue)
    src.data.materials.append(red)
    src.data.polygons[0].material_index = 1
    for i, loop in enumerate(src.data.polygons[0].loop_indices):
        src.data.uv_layers.active.data[loop].uv = (0.83 + 0.1 * i, 0.25)
    want = [tuple(src.data.uv_layers.active.data[li].uv) for li in src.data.polygons[0].loop_indices]
    dst = _mesh("dst", faces=2, x=5)
    _select(src)
    assert _run("Mesh/Clipboard Actions/Copy Attributes") == {'CANCELLED'}   # object selection: refused
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(src.data)
    bm.faces.ensure_lookup_table()
    for f in bm.faces:
        f.select_set(f.index in (0, 1))
    bm.faces.active = bm.faces[0]
    bmesh.update_edit_mesh(src.data)
    _run("Mesh/Clipboard Actions/Copy Attributes")
    bpy.ops.object.mode_set(mode='OBJECT')
    assert clip.CLIPBOARD["material"] == "red"
    _select(dst)
    _run("Mesh/Clipboard Actions/Paste Attributes")       # an object = all its faces
    for p in dst.data.polygons:
        assert dst.material_slots[p.material_index].material == red
        assert [tuple(dst.data.uv_layers.active.data[li].uv) for li in p.loop_indices] == want
    _select()
    assert _run("Mesh/Clipboard Actions/Paste Attributes") == {'CANCELLED'}   # nothing selected
    _run("Mesh/Clipboard Actions/Clear Clipboard")
    _select(dst)
    assert _run("Mesh/Clipboard Actions/Paste Attributes") == {'CANCELLED'}   # empty clipboard


def test_transfer_attribute_values():
    _clear()
    a, b, c = _mesh("pCube1"), _mesh("pSphere1"), _mesh("locator1")
    a.location, a.rotation_euler, a.scale = (3, 4, 5), (0.1, 0.2, 0.3), (2, 2, 2)
    a.rotation_mode = 'YZX'
    a["foo"], a["bar"], b["foo"] = 5.0, 7.0, 0.0
    _select(a, b, c)
    assert _run("Edit/Transfer Attribute Values") == {'CANCELLED'}        # Maya: Too many objects selected
    _select(a)
    assert _run("Edit/Transfer Attribute Values") == {'CANCELLED'}        # Maya: Select a source and a target
    _select(a, b, active=b)                                                 # b picked second = target
    _run("Edit/Transfer Attribute Values")
    assert tuple(b.location) == (3, 4, 5) and tuple(b.scale) == (2, 2, 2) and b.rotation_mode == 'YZX'
    assert b["foo"] == 5.0 and "bar" not in b            # Maya: foo copied, bar not added


def test_lod_create_generate_ungroup():
    _clear()
    s, c = _mesh("pSphere1", faces=6), _mesh("pCube1", x=3)
    _select(s, c)
    _run("Edit/LOD (Level of Detail)/Create LOD Group")
    group = lod.lod_group_of(s)
    assert group is not None and group.name.startswith("LOD_Group_")
    assert s.parent.name == "LOD_0" and c.parent.name.startswith("LOD_1")    # one level per object
    _select(s)
    _run("Edit/LOD (Level of Detail)/Ungroup LOD Group")
    assert lod.lod_group_of(s) is None and not any(o.get(lod.GROUP) for o in bpy.data.objects)
    assert s.parent is not None and s.parent.parent is None                 # LOD_0 kept at the top, like Maya
    _clear()
    s = _mesh("pSphere1", faces=6)
    _select(s)
    _run("Edit/LOD (Level of Detail)/Generate LOD Meshes")
    group = lod.lod_group_of(s)
    one = lod.level(group, 1)
    assert s.parent == lod.level(group, 0) and len(one.children) == 1
    dup = one.children[0]
    assert dup.type == 'MESH' and dup.data is not s.data and dup.modifiers[0].type == 'DECIMATE'
    assert abs(dup.modifiers[0].ratio - 2 / 3) < 1e-6                     # Maya removes 33.3% (of vertices)
