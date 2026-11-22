"""Issue #344: in Maya mode, the kit's 3D View draws and frame handlers that have nothing to do on a played frame
return after the cheapest check, before reading the view or the scene.

Each of them runs once per drawn frame, so what it reads before it finds there is nothing to draw is paid on every
frame of playback: a scene without camera rigs, bend handles, distance dimensions, a polygon being placed, kit IK
chains, Simple Deform bends, ghosts or vertex keys reads only the kit's own caches. The Range Slider row and the
Range Slider bar's colours are worked out once and used again while nothing they depend on changed. Last, a loose
time budget for every kit frame handler together on a frame."""

import time
from importlib import import_module
from types import SimpleNamespace

import bpy

import kit


def _m(name):
    return import_module(kit.MODULE + "." + name)


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _scene(props=20):
    """A skeleton and some keyed props: nothing any of the checked hooks draws or works on."""
    _clear()
    joints = _m("operators.joints")
    from mathutils import Vector
    arm = joints.new_skeleton(bpy.context)
    made = [joints.add_joint(arm, Vector((0, 0, 0)), None, length=0.5)]
    for i in range(1, 6):
        made.append(joints.add_joint(arm, Vector((0, 0, 0.3 * i)), made[-1], length=0.3))
    joints.finish(bpy.context, arm, made)
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    sc = bpy.context.scene
    for i in range(props):
        ob = bpy.data.objects.new(f"prop{i}", None)
        sc.collection.objects.link(ob)
        for f in (1, 20):
            ob.location.z = f * 0.1 + i
            ob.keyframe_insert("location", index=2, frame=f)
    for ob in bpy.context.view_layer.objects:
        ob.select_set(False)
    bpy.context.view_layer.objects.active = None      # nothing selected: the scene is in Object Mode
    bpy.context.view_layer.update()
    return arm


def _view():
    screen = next(s for s in bpy.data.screens if any(a.type == 'VIEW_3D' for a in s.areas))
    area = next(a for a in screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    return screen, area, region


class _Spy:
    """Replace module attributes by counting stand-ins that call the real ones."""

    def __init__(self, *targets):
        self.targets = targets            # (module, attribute name, label)
        self.calls = []

    def __enter__(self):
        self.real = [getattr(m, a) for m, a, _l in self.targets]
        for (m, a, label), real in zip(self.targets, self.real):
            setattr(m, a, (lambda real, label: lambda *x, **k: self.calls.append(label) or real(*x, **k))(real, label))
        return self

    def __exit__(self, *_exc):
        for (m, a, _l), real in zip(self.targets, self.real):
            setattr(m, a, real)


def test_idle_view_draws_read_no_view():
    """No camera rig, no bend handle, no distance dimension and no polygon being placed: those draws don't read the
    view; with a camera (a plain one) the camera aim lines look at the view again, and a polygon being placed looks
    for the tool."""
    cam_lines, bends, dims, poly = (_m("ui.camera_aim_lines"), _m("ui.bend_handles"), _m("ui.distance_dimensions"),
                                    _m("operators.poly_draw"))
    _scene()
    screen, area, region = _view()
    with _Spy((cam_lines, "is_maya_view", "camera lines"), (bends, "is_maya_view", "bend handles"),
              (dims, "shown", "dimensions"), (poly, "tool_active", "polygon tool")) as spy:
        with bpy.context.temp_override(screen=screen, area=area, region=region):
            assert bpy.context.region_data is not None and bpy.context.mode == 'OBJECT'
            for _f in range(3):
                cam_lines._draw()
                bends._draw()
                dims._draw()
                poly._draw_view()
            assert spy.calls == [], f"nothing to draw: the view is not read ({spy.calls})"
            cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
            bpy.context.scene.collection.objects.link(cam)
            bpy.context.view_layer.update()
            cam_lines._draw()
            assert spy.calls == ["camera lines"], f"a camera: the camera aim lines read the view ({spy.calls})"
            spy.calls.clear()
            state = poly.STATE
            state["kind"] = 'CREATE'
            try:
                poly._draw_view()
            finally:
                poly.STATE.update(kind=None, ob=None, items=[], hover=None)
            assert "polygon tool" in spy.calls, f"a polygon being placed looks for the tool ({spy.calls})"


def test_idle_frame_handlers_return_early():
    """A played frame without kit IK chains looks no further than the chain cache; without Simple Deform bends, ghosts
    or Edit Mode meshes the bend, ghost and vertex key handlers do nothing more."""
    ikc, bend, ghost, pk = (_m("operators.ik_fk_control"), _m("operators.bend_deformer"), _m("ui.ghosting"),
                            _m("operators.point_keys"))
    deformers = _m("operators.deformers")
    _scene()
    sc = bpy.context.scene
    with _Spy((ikc, "_playing", "IK playing check"), (ikc, "_release_on_frame", "IK release"),
              (deformers, "sd_bend_apply", "bend apply"), (ghost, "_schedule", "ghost sampling"),
              (pk, "apply_frame", "vertex keys")) as spy:
        for f in range(2, 12):
            sc.frame_set(f)
        assert spy.calls == [], f"nothing to do on a frame: {sorted(set(spy.calls))}"
    sc.frame_set(1)


def test_range_slider_row_and_colours_are_kept():
    """The Range Slider row is worked out once for a header size, UI scale, button place and longest frame number
    (the header draws it twice per redraw, on every played frame), again when the longest number gets longer; the
    bar's colours once per Timeline theme colours."""
    th, rb = _m("ui.time_slider_header"), _m("ui.range_bar")
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end, sc.frame_current = 1, 120, 7
    prefs = SimpleNamespace(system=SimpleNamespace(ui_scale=1.0), view=SimpleNamespace(font_path_ui=""))
    ctx = SimpleNamespace(region=SimpleNamespace(type='HEADER', width=1500), preferences=prefs, space_data=None,
                          area=None, scene=sc)
    th._plans.clear()
    with _Spy((th, "row_layout", "row")) as spy:
        first = th._row_plan(ctx)
        for f in (8, 9, 99):
            sc.frame_current = f
            assert th._row_plan(ctx) == first
        assert spy.calls == ["row"], f"one row plan for one size ({spy.calls})"
        sc.frame_end = 12000
        th._row_plan(ctx)
        ctx.region.width = 900
        th._row_plan(ctx)
        assert spy.calls == ["row"] * 3, f"a longer frame number, another width: worked out again ({spy.calls})"
    sc.frame_end, sc.frame_current = 250, 1
    rb._theme_colours.clear()
    with _Spy((rb, "_themed", "colour")) as spy:
        theme = ((48 / 255,) * 3, (166 / 255,) * 3)
        a = rb._colours(theme)
        assert rb._colours(theme) == a and len(spy.calls) == 4, f"four colours once ({len(spy.calls)})"
        b = rb._colours(((0.8,) * 3, (0.1,) * 3))
        assert len(spy.calls) == 8 and b != a, "another theme: worked out again"
    assert abs(a[0][0] - rb.TRACK_RGB[0]) < 1e-6 and abs(a[3][0] - rb.TEXT_RGB[0]) < 1e-6, "Blender's own theme: the Range Slider greys"


def test_kit_frame_handlers_cost_little_per_frame():
    """Every kit frame handler together, on a played frame of a scene with a skeleton and keyed props: a loose
    budget (they used to read the scene's objects, the windows and their imports again on every frame)."""
    _scene(props=40)
    sc = bpy.context.scene
    hs = bpy.app.handlers.frame_change_post
    kit_handlers = [f for f in hs if kit.MODULE.split(".")[-1] in (getattr(f, "__module__", "") or "")]
    assert len(kit_handlers) >= 5, f"the kit's frame handlers ({len(kit_handlers)})"
    spent = [0.0]
    real = list(hs)

    def timed(fn):
        def w(*a):
            t = time.perf_counter()
            try:
                return fn(*a)
            finally:
                spent[0] += time.perf_counter() - t
        return w
    hs.clear()
    hs.extend(timed(f) if f in kit_handlers else f for f in real)
    try:
        sc.frame_set(1)
        spent[0] = 0.0
        frames = 0
        for _rep in range(3):
            for f in range(1, 21):
                sc.frame_set(f)
                frames += 1
        per = spent[0] / frames * 1000
    finally:
        hs.clear()
        hs.extend(real)
    print(f"kit frame handlers: {per:.3f} ms per frame ({len(kit_handlers)} handlers)")
    assert per < 0.25, f"kit frame handlers {per:.3f} ms per frame (budget 0.25)"
    sc.frame_set(1)
