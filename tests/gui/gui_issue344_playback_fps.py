"""Issue #344 in a real UI: a heavy scene (two skinned 28k-triangle characters on 40-joint skeletons and 28 props:
about 88k triangles in 32 objects, keyed over 300 frames) plays in Solid / MatCap in Blender mode and in Maya mode
(the Maya layout), one after the other, twice, then once more with a character selected. Every frame is played, VSync
is off. At scene rate 30 both modes keep 30 frames/s; at scene rate 1000 (as fast as the PC draws) the rates are
printed and Maya mode keeps a loose 40 % of Blender mode's rate (other programs on the PC move the numbers). While
Maya mode plays, the Range Slider does not read its header row every frame, each skeleton's joint list is read once,
and the selected skinned character's wire keeps its edges (only its points are read again). Last, every bone becomes a
control with a circle shape and Maya mode plays in four views: the shape is read once, and each skeleton's lines are
built once a frame for all four views."""

import math
import os
import sys
import time
from importlib import import_module

import addon_utils
import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, check, tap, win  # noqa: E402

GUI_TIMEOUT = 420
GUI_ARGS = "--gpu-vsync off"
BONES = 40
WINDOW = 4.0
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
_frames = []


@bpy.app.handlers.persistent
def _count(_scene, *_a):
    _frames.append(time.perf_counter())


def _view():
    return max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)


def _override(**kw):
    area = _view()
    region = next(r for r in area.regions if r.type == 'WINDOW')
    return bpy.context.temp_override(window=win(), screen=win().screen, area=area, region=region, **kw)


def _mesh(name, build):
    bm = bmesh.new()
    build(bm)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def _tube(bm, rings=150, segs=96, height=2.0, radius=0.35):
    rows = [[bm.verts.new((radius * math.cos(2 * math.pi * s / segs), radius * math.sin(2 * math.pi * s / segs),
                           height * r / (rings - 1))) for s in range(segs)] for r in range(rings)]
    for r in range(rings - 1):
        for s in range(segs):
            bm.faces.new((rows[r][s], rows[r][(s + 1) % segs], rows[r + 1][(s + 1) % segs], rows[r + 1][s]))


def build_scene():
    sc = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    sc.frame_start, sc.frame_end, sc.frame_current = 1, 300, 1
    height = 2.0
    for c in range(2):
        arm = bpy.data.objects.new(f"rig{c}", bpy.data.armatures.new(f"rig{c}"))
        arm.location.x = -1.5 + 3 * c
        sc.collection.objects.link(arm)
        bpy.context.view_layer.objects.active = arm
        with _override(active_object=arm, object=arm):
            bpy.ops.object.mode_set(mode='EDIT')
            prev = None
            for i in range(BONES):
                eb = arm.data.edit_bones.new(f"b{i}")
                eb.head, eb.tail = (0, 0, height * i / BONES), (0, 0, height * (i + 1) / BONES)
                eb.parent, eb.use_connect = prev, prev is not None
                prev = eb
            bpy.ops.object.mode_set(mode='OBJECT')
        body = bpy.data.objects.new(f"body{c}", _mesh(f"body{c}", _tube))
        sc.collection.objects.link(body)
        body.parent = arm
        groups = [body.vertex_groups.new(name=f"b{i}") for i in range(BONES)]
        for v in body.data.vertices:
            t = max(0.0, min(BONES - 1e-6, v.co.z / height * BONES - 0.5))
            i, f = int(t), t - int(t)
            groups[i].add([v.index], 1 - f, 'REPLACE')
            if i + 1 < BONES:
                groups[i + 1].add([v.index], f, 'REPLACE')
        body.modifiers.new("Armature", 'ARMATURE').object = arm
        for f in range(1, 301, 10):
            for i, pb in enumerate(arm.pose.bones):
                pb.rotation_mode = 'XYZ'
                pb.rotation_euler = (0.25 * math.sin(f * 0.05 + i * 0.4 + c), 0.15 * math.cos(f * 0.07 + i * 0.3), 0)
                pb.keyframe_insert("rotation_euler", frame=f)
            arm.location.y = math.sin(f * 0.03 + c)
            arm.keyframe_insert("location", frame=f)
    for k in range(28):
        ob = bpy.data.objects.new(f"prop{k}", _mesh(f"prop{k}", lambda bm: bmesh.ops.create_uvsphere(
            bm, u_segments=24, v_segments=24, radius=0.25)))
        ob.location = (-4 + (k % 7) * 1.3, 3 + (k // 7) * 1.3, 0.3)
        sc.collection.objects.link(ob)
        if k % 3 == 0:
            for f in range(1, 301, 30):
                ob.location.z = 0.3 + 0.5 * abs(math.sin(f * 0.1 + k))
                ob.keyframe_insert("location", frame=f)
        ob.select_set(False)
    sc.frame_set(1)
    dg = bpy.context.evaluated_depsgraph_get()
    return sum(len(o.evaluated_get(dg).data.loop_triangles) for o in sc.objects if o.type == 'MESH')


def ready_views(fps):
    for a in win().screen.areas:
        if a.type == 'VIEW_3D':
            a.spaces.active.shading.type = 'SOLID'
            a.spaces.active.shading.light = 'MATCAP'
    with _override():
        bpy.ops.view3d.view_all()
    sc = bpy.context.scene
    sc.sync_mode = 'NONE'           # every frame is played: the rate is what the PC draws
    sc.render.fps = fps
    for ob in sc.objects:
        ob.select_set(False)


def flow():
    tap('ESC')
    yield 1.0
    addon_utils.enable(MODULE, default_set=True)
    yield 1.0
    tris = build_scene()
    check(f"a heavy scene: {len(bpy.context.scene.objects)} objects, {tris} triangles",
          len(bpy.context.scene.objects) == 32 and 80000 < tris < 95000)
    bpy.app.handlers.frame_change_post.append(_count)
    sw = import_module(MODULE + ".switch")
    rb = import_module(MODULE + ".ui.range_bar")
    mj = import_module(MODULE + ".ui.maya_joints")
    wire = import_module(MODULE + ".ui.selection_wire")
    lists, drawn, reads = [], [], []
    real_list, real_parts, real_read = mj._joint_list, mj._parts, mj._read_widget
    mj._joint_list = lambda ob: lists.append(ob.name) or real_list(ob)     # counts the joint list reads
    mj._parts = lambda ob, *a, **k: drawn.append(ob.name) or real_parts(ob, *a, **k)   # skeleton lines built
    mj._read_widget = lambda shape, dg: reads.append(shape.name) or real_read(shape, dg)   # control shapes read
    rates = {}

    def play(fps, mode, select=None):
        sw.set_mode(mode == "maya", layout=True)
        yield 2.5
        ready_views(fps)
        if select is not None:
            bpy.data.objects[select].select_set(True)
            bpy.context.view_layer.objects.active = bpy.data.objects[select]
        yield 1.0
        with _override():
            bpy.ops.screen.animation_play()
        yield 1.0
        _frames.clear()
        lists.clear()
        drawn.clear()
        reads.clear()
        play.reads = rb.row_reads[0]
        t0 = time.perf_counter()
        yield WINDOW
        play.rate = len(_frames) / (time.perf_counter() - t0)
        play.reads = rb.row_reads[0] - play.reads
        play.frames = len(_frames)
        if win().screen.is_animation_playing:
            with _override():
                bpy.ops.screen.animation_cancel(restore_frame=False)
        play.bars = len(rb._bars)
        print(f"PLAYBACK fps {fps} {mode}{' ' + select + ' selected' if select else ''}: {play.rate:.1f} frames/s, "
              f"Range Slider row reads {play.reads}, joint list reads {len(lists)}, skeletons drawn {len(drawn)}",
              flush=True)

    for fps in (30, 1000):
        for _rep in range(2):
            for mode in ("blender", "maya"):
                yield from play(fps, mode)
                rates.setdefault((fps, mode), []).append(play.rate)
                if mode == "maya":
                    check(f"Maya mode at {fps} fps: the Range Slider bar is drawn ({play.bars}) and reads its header "
                          f"row a few times, not every frame ({play.reads} reads in {play.frames} frames)",
                          play.bars >= 1 and play.reads <= 3 and play.frames > 20)
                    check(f"... both skeletons are built every frame ({len(drawn)} builds) and their joint lists are "
                          f"read once, not every frame ({len(lists)} reads)",
                          len(drawn) >= 2 * play.frames and len(lists) <= 4)
                if SHOTS and fps == 30 and _rep == 0:
                    sim.screenshot(os.path.join(SHOTS, f"issue344_{mode}.png"))
                yield 0.5
    for mode in ("blender", "maya"):
        yield from play(1000, mode, select="body0")
        rates[(1000, mode, "body0")] = [play.rate]
        if mode == "maya":
            got = wire._edges.get(bpy.data.objects["body0"].session_uid)
            check(f"a selected skinned character: its wire keeps its edges while playing "
                  f"({'kept' if got is not None else 'not kept'})", got is not None)
            if SHOTS:
                sim.screenshot(os.path.join(SHOTS, "issue344_maya_selected.png"))
        yield 0.5
    # every bone a control with a 32-point circle shape (kept in an excluded collection, like rig generators do),
    # Maya mode in four views
    widgets = bpy.data.collections.new("widgets")
    bpy.context.scene.collection.children.link(widgets)
    bpy.context.view_layer.layer_collection.children["widgets"].exclude = True
    me = bpy.data.meshes.new("WGT_circle")
    me.from_pydata([(0.1 * math.cos(2 * math.pi * i / 32), 0.0, 0.1 * math.sin(2 * math.pi * i / 32))
                    for i in range(32)], [(i, (i + 1) % 32) for i in range(32)], [])
    wgt = bpy.data.objects.new("WGT_circle", me)
    widgets.objects.link(wgt)
    for c in range(2):
        for pb in bpy.data.objects[f"rig{c}"].pose.bones:
            pb.custom_shape = wgt
    sw.set_mode(True, layout=True)
    yield 2.5
    with _override():
        bpy.ops.screen.region_quadview()
    yield 0.5
    yield from play(1000, "maya")
    rates[(1000, "maya", "quad")] = [play.rate]
    check(f"controls in four views: the circle shape is read once ({len(reads)} reads), each skeleton is built once a "
          f"frame for all four views ({len(drawn)} builds in {play.frames} frames)",
          len(reads) <= 2 and play.frames > 20 and 2 * play.frames - 4 <= len(drawn) <= 2 * play.frames + 4)
    if SHOTS:
        sim.screenshot(os.path.join(SHOTS, "issue344_maya_controls_quad.png"))
    with _override():
        bpy.ops.screen.region_quadview()
    yield 0.5
    mj._joint_list, mj._parts, mj._read_widget = real_list, real_parts, real_read
    best ={k: max(v) for k, v in rates.items()}
    check(f"scene rate 30: Blender mode {best[(30, 'blender')]:.1f}, Maya mode {best[(30, 'maya')]:.1f} frames/s "
          f"(both keep 30)", best[(30, 'blender')] >= 28.5 and best[(30, 'maya')] >= 28.5)
    b, m = best[(1000, 'blender')], best[(1000, 'maya')]
    bs, ms = best[(1000, 'blender', 'body0')], best[(1000, 'maya', 'body0')]
    check(f"as fast as it draws: Blender mode {b:.0f}, Maya mode {m:.0f} frames/s ({m / b:.0%}); a character "
          f"selected: {bs:.0f}, {ms:.0f} ({ms / bs:.0%}); Maya mode keeps at least 40 %", m >= 0.4 * b and ms >= 0.4 * bs)
    print(f"PLAYBACK controls in four views: {best[(1000, 'maya', 'quad')]:.0f} frames/s", flush=True)
    bpy.app.handlers.frame_change_post.remove(_count)


_gen = flow()


def _tick():
    try:
        return next(_gen)
    except StopIteration:
        sim._finish()
    except Exception as ex:
        import traceback
        traceback.print_exc()
        check(f"step raised {ex!r}", False)
        sim._finish()
    return None


bpy.app.timers.register(_tick, first_interval=2.0, persistent=True)
