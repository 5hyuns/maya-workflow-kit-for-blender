"""Issue #344 in a real UI: dragging a rig control in Maya mode. A 40-joint skeleton whose joints are controls with a
circle shape, Pose Mode, a Move drag of one control with the mouse: while the drag runs the joint lines follow the
pose, but the skeleton's joint list is read only on the drag's first redraw, the controls' shapes are not read again
and the Range Slider does not read its header row; Esc puts the control back."""

import math
import os
import sys
import time
from importlib import import_module

import addon_utils
import bpy
from bpy_extras import view3d_utils

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, check, tap, win  # noqa: E402

GUI_TIMEOUT = 240
STEPS = 40


def _view():
    tb = import_module(MODULE + ".ui.toolbox")
    return max((a for a in win().screen.areas if a.type == 'VIEW_3D' and not tb.is_toolbox(a.spaces.active)),
               key=lambda a: a.width * a.height)


def _override(**kw):
    area = _view()
    region = next(r for r in area.regions if r.type == 'WINDOW')
    return bpy.context.temp_override(window=win(), screen=win().screen, area=area, region=region, **kw)


def build():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    arm = bpy.data.objects.new("rig", bpy.data.armatures.new("rig"))
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    with _override(active_object=arm, object=arm):
        bpy.ops.object.mode_set(mode='EDIT')
        prev = None
        for i in range(40):
            eb = arm.data.edit_bones.new(f"c{i}")
            eb.head, eb.tail = (0.3 * math.sin(i * 0.3), 0, 0.05 * i), (0.3 * math.sin(i * 0.3), 0, 0.05 * i + 0.05)
            eb.parent, eb.use_connect = prev, False
            prev = eb
        bpy.ops.object.mode_set(mode='OBJECT')
    me = bpy.data.meshes.new("WGT")
    me.from_pydata([(0.08 * math.cos(2 * math.pi * i / 24), 0, 0.08 * math.sin(2 * math.pi * i / 24))
                    for i in range(24)], [(i, (i + 1) % 24) for i in range(24)], [])
    wgt = bpy.data.objects.new("WGT", me)
    bpy.context.scene.collection.objects.link(wgt)
    wgt.hide_viewport = True
    for pb in arm.pose.bones:
        pb.custom_shape = wgt
    return arm


def flow():
    tap('ESC')
    yield 1.0
    addon_utils.enable(MODULE, default_set=True)
    yield 1.0
    sw = import_module(MODULE + ".switch")
    mj = import_module(MODULE + ".ui.maya_joints")
    rb = import_module(MODULE + ".ui.range_bar")
    sw.set_mode(True, layout=True)
    yield 2.5
    arm = build()
    with _override():
        bpy.ops.view3d.view_all()
    with _override(active_object=arm, object=arm):
        bpy.ops.object.mode_set(mode='POSE')
    name = "c20"
    for pb in arm.pose.bones:
        pb.select = pb.name == name
    arm.data.bones.active = arm.data.bones[name]
    yield 1.0
    area = _view()
    region = next(r for r in area.regions if r.type == 'WINDOW')
    p = view3d_utils.location_3d_to_region_2d(region, region.data, arm.matrix_world @ arm.pose.bones[name].head)
    x0, y0 = int(region.x + p.x), int(region.y + p.y)
    sim.ev('MOUSEMOVE', 'NOTHING', x=x0, y=y0)
    yield 0.3
    lists, reads, draws, lines = [], [], [], []
    real_list, real_read, real_draw = mj._joint_list, mj._read_widget, mj._draw
    mj._joint_list = lambda ob: lists.append(ob.name) or real_list(ob)
    mj._read_widget = lambda shape, dg: reads.append(shape.name) or real_read(shape, dg)
    with _override():
        bpy.ops.transform.translate('INVOKE_DEFAULT')
    yield 0.3
    check("a Move drag runs", mj.transforming())
    lists.clear()
    reads.clear()
    rows = rb.row_reads[0]
    head0 = (arm.matrix_world @ arm.pose.bones[name].head).copy()
    t0 = time.perf_counter()
    for i in range(STEPS):
        sim.ev('MOUSEMOVE', 'NOTHING', x=x0 + 3 * i, y=y0 + i)
        yield 0.02
        hit = mj._JOINED and next(iter(mj._JOINED.values()))
        if hit:
            lines.append(hit[0])
    secs = time.perf_counter() - t0
    moved = (arm.matrix_world @ arm.pose.bones[name].head - head0).length
    check(f"the control follows the mouse ({moved:.3f})", moved > 0.05)
    distinct = len({ln.tobytes() for ln in lines})
    check(f"the joint lines follow the drag ({distinct} different line sets in {len(lines)} steps)", distinct > STEPS // 3)
    check(f"while dragging the joint list is read once, on the drag's first redraw ({len(lists)} reads), the "
          f"control shapes not again ({len(reads)} reads), and the Range Slider reads no header row "
          f"({rb.row_reads[0] - rows})", len(lists) <= 1 and len(reads) == 0 and rb.row_reads[0] - rows == 0)
    print(f"DRAG {STEPS} steps in {secs:.2f} s", flush=True)
    sim.ev('ESC', 'PRESS')
    sim.ev('ESC', 'RELEASE')
    yield 0.5
    back = (arm.matrix_world @ arm.pose.bones[name].head - head0).length
    check(f"Esc puts the control back ({back:.4f}) and the drag has ended", back < 1e-4 and not mj.transforming())
    mj.changed()
    lists.clear()
    with _override():
        area.tag_redraw()
    yield 0.5
    check(f"after the drag a redraw reads the joints again ({len(lists)} reads)", len(lists) >= 1)
    mj._joint_list, mj._read_widget = real_list, real_read
    with _override(active_object=arm, object=arm):
        bpy.ops.object.mode_set(mode='OBJECT')


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
