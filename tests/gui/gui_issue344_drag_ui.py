"""Issue #344 in a real UI: the Maya UI around a drag. A 200-joint skeleton in Pose Mode, Maya layout with the Channel
Box in the dock, a Move drag of one joint with the mouse: on every step the dock redraws and the Channel Box shows the
joint's current Translate values; the dock reads its drawn pixels (the Layer Editor list it leaves untinted) once per
drag, the Status Line's workspace list looks each workspace up once per redraw, and the picked bones aren't asked one
by one. After Enter the Channel Box shows the final values and the next redraw reads the pixels again."""

import math
import os
import sys
from importlib import import_module

import addon_utils
import bpy
from bpy_extras import view3d_utils

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, check, tap, win  # noqa: E402

GUI_TIMEOUT = 240
STEPS = 30
BONES = 200
KEYS = ("tx", "ty", "tz")


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
        for i in range(BONES):
            eb = arm.data.edit_bones.new(f"j{i}")
            x = 0.3 * math.sin(i * 0.2)
            eb.head, eb.tail = (x, 0, 0.012 * i), (x, 0, 0.012 * i + 0.012)
            eb.parent, eb.use_connect = prev, False
            prev = eb
        bpy.ops.object.mode_set(mode='OBJECT')
    return arm


def flow():
    tap('ESC')
    yield 1.0
    addon_utils.enable(MODULE, default_set=True)
    yield 1.0
    sw = import_module(MODULE + ".switch")
    mj = import_module(MODULE + ".ui.maya_joints")
    md = import_module(MODULE + ".ui.maya_dock")
    cb = import_module(MODULE + ".ui.channel_box")
    wsm = import_module(MODULE + ".ui.workspaces")
    sw.set_mode(True, layout=True)
    yield 2.5
    arm = build()
    with _override():
        bpy.ops.view3d.view_all()
    with _override(active_object=arm, object=arm):
        bpy.ops.object.mode_set(mode='POSE')
    name = "j100"
    for pb in arm.pose.bones:
        pb.select = pb.name == name
    arm.data.bones.active = arm.data.bones[name]
    dock = sim.dock_area('CHANNEL_BOX')
    yield 1.5
    dock = md.find_stack(win().screen)
    check("the Channel Box shows in the dock", dock is not None and md.current_tab() == 'CHANNEL_BOX')
    dock_ptr = dock.as_pointer()
    pb = arm.pose.bones[name]

    drawn, counts = {}, {"dock": 0, "hole": 0, "template": 0, "entries": 0, "bone": 0}
    real = {"get": cb.get_value, "hole": md._list_hole, "template": sw.template_of, "entries": wsm.entries,
            "bone": cb.bone_selected}

    def get_value(ob, key):
        v = real["get"](ob, key)
        area = bpy.context.area
        if key in KEYS and area is not None and area.as_pointer() == dock_ptr and ob == pb:
            drawn[key] = v
        return v

    def hole(*a):
        counts["hole"] += 1
        return real["hole"](*a)

    def template_of(ws):
        counts["template"] += 1
        return real["template"](ws)

    def entries():
        counts["entries"] += 1
        return real["entries"]()

    def bone_selected(p):
        counts["bone"] += 1
        return real["bone"](p)

    def dock_drawn():
        area = bpy.context.area
        if area is not None and area.as_pointer() == dock_ptr:
            counts["dock"] += 1

    cb.get_value, md._list_hole, sw.template_of, wsm.entries, cb.bone_selected = (
        get_value, hole, template_of, entries, bone_selected)
    handle = bpy.types.SpaceProperties.draw_handler_add(dock_drawn, (), 'WINDOW', 'POST_PIXEL')
    try:
        area = _view()
        region = next(r for r in area.regions if r.type == 'WINDOW')
        p = view3d_utils.location_3d_to_region_2d(region, region.data, arm.matrix_world @ pb.head)
        x0, y0 = int(region.x + p.x), int(region.y + p.y)
        sim.ev('MOUSEMOVE', 'NOTHING', x=x0, y=y0)
        yield 0.3
        counts["hole"] = 0
        with _override():
            bpy.ops.transform.translate('INVOKE_DEFAULT')
        yield 0.3
        check("a Move drag runs", mj.transforming())
        for k in counts:
            if k != "hole":
                counts[k] = 0
        start = tuple(pb.location)
        seen = []
        for i in range(STEPS):
            sim.ev('MOUSEMOVE', 'NOTHING', x=x0 + 4 * i, y=y0 + 2 * i)
            yield 0.03
            if len(drawn) == 3:
                seen.append(tuple(round(drawn[k], 6) for k in KEYS))
        yield 0.4                                       # the mouse rests, the drag still runs
        live = tuple(round(cb.get_value(pb, k), 6) for k in KEYS)
        last = tuple(round(drawn.get(k, float("nan")), 6) for k in KEYS)
        moved = max(abs(a - b) for a, b in zip(pb.location, start))
        check(f"the joint follows the mouse ({moved:.3f})", moved > 0.05)
        check(f"the dock redraws on the drag's steps ({counts['dock']} redraws in {STEPS} steps)",
              counts["dock"] >= STEPS // 2)
        check(f"the Channel Box shows new Translate values while dragging ({len(set(seen))} different in "
              f"{len(seen)} steps)", len(set(seen)) >= STEPS // 3)
        check(f"the Channel Box shows the current values during the drag ({last} = {live})", last == live)
        check(f"the dock reads its drawn pixels once per drag ({counts['hole']} reads in {counts['dock']} redraws)",
              counts["hole"] <= 1)
        n_ws = len(bpy.data.workspaces)
        check(f"the Status Line looks each workspace up once per list ({counts['template']} lookups, "
              f"{counts['entries']} lists, {n_ws} workspaces)", counts["template"] <= counts["entries"] * n_ws)
        per = counts["bone"] / max(1, counts["dock"])
        check(f"the picked bones aren't asked one by one ({per:.1f} asks per dock redraw, {BONES} bones)",
              per < BONES / 2)
        sim.ev('RET', 'PRESS')
        sim.ev('RET', 'RELEASE')
        yield 0.8
        check("Enter ends the drag", not mj.transforming())
        final = tuple(round(cb.get_value(pb, k), 6) for k in KEYS)
        after = tuple(round(drawn.get(k, float("nan")), 6) for k in KEYS)
        check(f"after the drag the Channel Box shows the final values ({after} = {final}), moved from {start}",
              after == final and max(abs(a - b) for a, b in zip(final, start)) > 0.05)
        holes = counts["hole"]
        md.redraw()
        yield 0.5
        check(f"a redraw after the drag reads the pixels again ({counts['hole'] - holes} reads) and keeps nothing "
              f"of the drag", counts["hole"] > holes and not md._hole_kept)
    finally:
        cb.get_value, md._list_hole, sw.template_of, wsm.entries, cb.bone_selected = (
            real["get"], real["hole"], real["template"], real["entries"], real["bone"])
        bpy.types.SpaceProperties.draw_handler_remove(handle, 'WINDOW')
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
