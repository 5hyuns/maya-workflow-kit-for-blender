"""The Channel Box dock in a big scene: a 300-joint skeleton in Pose Mode with 299 joints picked and the active joint
not picked, among 3,000 other objects. Blender reads every value field again after the Channel Box's draw returns;
those reads use the lead the draw found, so a dock redraw asks for the lead a few times (not once per field read) and
never lists every picked joint. The fields still show the lead's current values: after the picks change, after the
active joint changes and after the joint moves."""

import math
import os
import sys
from importlib import import_module

import addon_utils
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, check, tap, win  # noqa: E402

GUI_TIMEOUT = 240
BONES = 300
PLAIN = 3000
KEYS = ("tx", "ty", "tz", "rx")


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
    me = bpy.data.meshes.new("plain")
    for i in range(PLAIN):
        o = bpy.data.objects.new(f"plain{i}", me)
        bpy.context.scene.collection.objects.link(o)
        o.location = (10 + i % 50, 10 + i // 50, 0)
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
    md = import_module(MODULE + ".ui.maya_dock")
    cb = import_module(MODULE + ".ui.channel_box")
    sw.set_mode(True, layout=True)
    yield 2.5
    arm = build()
    with _override(active_object=arm, object=arm):
        bpy.ops.object.mode_set(mode='POSE')
    for pb in arm.pose.bones:
        pb.select = pb.name != "j0"
    arm.data.bones.active = arm.data.bones["j0"]          # the active joint is not picked
    sim.dock_area('CHANNEL_BOX')
    yield 1.5
    dock = md.find_stack(win().screen)
    check("the Channel Box shows in the dock", dock is not None and md.current_tab() == 'CHANNEL_BOX')
    dock_ptr = dock.as_pointer()

    drawn = {}
    counts = {"dock": 0, "lead": 0, "listed": 0}
    real = {"get": cb.get_value, "lead": cb.lead, "listed": cb.selected_bones}

    def get_value(ob, key):
        v = real["get"](ob, key)
        area = bpy.context.area
        if key in KEYS and area is not None and area.as_pointer() == dock_ptr:
            drawn[key] = (getattr(ob, "name", ""), round(v, 6))
        return v

    def lead(context=None):
        area = bpy.context.area
        if area is not None and area.as_pointer() == dock_ptr:
            counts["lead"] += 1
        return real["lead"](context)

    def selected_bones(context=None):
        area = bpy.context.area
        if area is not None and area.as_pointer() == dock_ptr:
            counts["listed"] += 1
        return real["listed"](context)

    def dock_drawn():
        area = bpy.context.area
        if area is not None and area.as_pointer() == dock_ptr:
            counts["dock"] += 1

    def want(pb):
        return {k: (pb.name, round(real["get"](pb, k), 6)) for k in KEYS}

    cb.get_value, cb.lead, cb.selected_bones = get_value, lead, selected_bones
    handle = bpy.types.SpaceProperties.draw_handler_add(dock_drawn, (), 'WINDOW', 'POST_PIXEL')
    try:
        for k in counts:
            counts[k] = 0
        for _ in range(6):
            drawn.clear()
            md.redraw()
            yield 0.15
        per_lead = counts["lead"] / max(1, counts["dock"])
        check(f"the dock redraws ({counts['dock']} redraws)", counts["dock"] >= 4)
        check(f"a dock redraw asks for the lead a few times ({per_lead:.1f} per redraw, {len(KEYS)}+ fields)",
              per_lead <= 6)
        check(f"a dock redraw never lists every picked joint ({counts['listed']} lists)", counts["listed"] == 0)
        first = arm.pose.bones["j1"]
        check(f"the fields show the first picked joint ({drawn} = {want(first)})", drawn == want(first))
        # other picks: the next draw finds the new lead
        for pb in arm.pose.bones:
            pb.select = pb.name in {"j40", "j41"}
        drawn.clear()
        md.redraw()
        yield 0.4
        pb40 = arm.pose.bones["j40"]
        check(f"after new picks the fields show the new first picked joint ({drawn} = {want(pb40)})",
              drawn == want(pb40))
        # the active joint picked: it leads
        arm.pose.bones["j41"].select = True
        arm.data.bones.active = arm.data.bones["j41"]
        drawn.clear()
        md.redraw()
        yield 0.4
        pb41 = arm.pose.bones["j41"]
        check(f"the picked active joint leads ({drawn} = {want(pb41)})", drawn == want(pb41))
        # the lead moves (no selection change): the fields show its new values
        pb41.location = (0.25, -0.5, 0.75)
        pb41.rotation_mode = 'XYZ'
        pb41.rotation_euler = (0.3, 0.0, 0.0)
        drawn.clear()
        md.redraw()
        yield 0.4
        check(f"the fields follow the lead's new values ({drawn} = {want(pb41)})", drawn == want(pb41))
        check("no draw-time lead is left after the dock drew", not cb._field_lead if hasattr(cb, "_field_lead")
              else True)
    finally:
        cb.get_value, cb.lead, cb.selected_bones = real["get"], real["lead"], real["listed"]
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
