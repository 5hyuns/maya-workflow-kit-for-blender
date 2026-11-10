"""#325 (Graph Editor): with Alt held, the left and the middle button together zoom the Graph Editor like Alt+RMB,
whichever button comes first, like Maya; letting go of the left button carries on panning with the middle one,
letting go of the middle button holds the view still until the left one is let go or the middle one pressed again.
Alt+MMB pan, Alt+LMB pan and Alt+RMB zoom stay as they were. The same chord zooms the Dope Sheet."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {"refs": {}}
STEP_PX = 8        # one mouse move
MOVES = 5          # moves per drag leg (40 px)
NAV = {"VIEW2D_OT_pan", "VIEW2D_OT_zoom", "ALLSET_OT_nav_2d"}


def region():
    return next(r for r in C["area"].regions if r.type == 'WINDOW')


def rect():
    """View rectangle shown by the region (view coordinates of its corners)."""
    r = region()
    x0, y0 = r.view2d.region_to_view(0, 0)
    x1, y1 = r.view2d.region_to_view(r.width, r.height)
    return (x0, y0, x1, y1)


def modal_names():
    return [op.bl_idname for op in win().modal_operators]


def same_rect(a, b, tol=0.01):
    """Equal within ``tol`` of the view size on each axis."""
    w, h = abs(b[2] - b[0]) or 1.0, abs(b[3] - b[1]) or 1.0
    return (abs(a[0] - b[0]) < tol * w and abs(a[2] - b[2]) < tol * w
            and abs(a[1] - b[1]) < tol * h and abs(a[3] - b[3]) < tol * h)


def fmt(rc):
    return "(%.3f, %.3f, %.3f, %.3f)" % rc


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    area, reg = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=reg):
        bpy.ops.allset.create(kind='CUBE')
    ob = bpy.data.objects["pCube1"]
    for f, v in ((1, 0.0), (12, 10.0), (24, 4.0)):
        ob.location.x = v
        ob.keyframe_insert("location", index=0, frame=f)
    bpy.context.scene.frame_set(1)
    p = import_module(MODULE + ".preferences").get()
    p.graph_auto_frame = False
    p.graph_auto_frame_time = False
    C["area"] = area
    area.ui_type = 'FCURVES'


def frame_view():
    a = C["area"]
    with bpy.context.temp_override(window=win(), area=a, region=region()):
        if a.type == 'GRAPH_EDITOR':
            a.spaces.active.use_normalization = False
            bpy.ops.graph.view_all()
        else:
            bpy.ops.action.view_all()


def point(fx=0.5, fy=0.5):
    r = region()
    return r.x + int(r.width * fx), r.y + int(r.height * fy)


def add_case(name, script, at=(0.5, 0.5), verify=None):
    """``script``: ('press' | 'release', button) and ('move', dx, dy) per leg (split into MOVES moves), all with Alt
    held; ('snap', key) keeps the view rectangle at that point. The view is framed first; whatever is still held
    at the end is let go."""
    st = {"held": [], "snaps": {}}

    def start():
        frame_view()
        x, y = point(*at)
        st["xy"] = [x, y]
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)

    def alt_down():
        st["rect0"] = rect()
        ev('LEFT_ALT', 'PRESS', alt=True, x=st["xy"][0], y=st["xy"][1])

    step(start)
    step(alt_down)
    for item in script:
        if item[0] in ('press', 'release'):
            def button(item=item):
                kind, btn = item
                if kind == 'press':
                    st["held"].append(btn)
                    ev(btn, 'PRESS', alt=True, x=st["xy"][0], y=st["xy"][1])
                else:
                    st["held"].remove(btn)
                    ev(btn, 'RELEASE', alt=True, x=st["xy"][0], y=st["xy"][1])
            step(button)
        elif item[0] == 'move':
            for _ in range(MOVES):
                def move(item=item):
                    st["xy"][0] += item[1] // MOVES
                    st["xy"][1] += item[2] // MOVES
                    ev('MOUSEMOVE', 'NOTHING', alt=True, x=st["xy"][0], y=st["xy"][1])
                    st["modals"] = modal_names()
                step(move)
        elif item[0] == 'snap':
            step(lambda item=item: st["snaps"].__setitem__(item[1], rect()))

    def finish():
        st["rect1"] = rect()
        st["during"] = st.get("modals", [])
        for btn in list(reversed(st["held"])):
            ev(btn, 'RELEASE', alt=True, x=st["xy"][0], y=st["xy"][1])
        st["held"].clear()
        ev('LEFT_ALT', 'RELEASE', x=st["xy"][0], y=st["xy"][1])
    step(finish)
    step(lambda: None)

    def done():
        C["refs"][name] = st
        left = [n for n in modal_names() if n in NAV]
        check(f"{name}: nothing left running after letting go ({left})", not left)
        if verify:
            verify(st)
        if SHOTS:
            screenshot(os.path.join(SHOTS, f"issue325_graph_{name}.png"))
    step(done)


D = STEP_PX * MOVES


def like(ref, label):
    def verify(st):
        want = C["refs"][ref]["rect1"]
        check(f"{label}: the view {fmt(st['rect1'])} is the {ref} view {fmt(want)} "
              f"(start {fmt(st['rect0'])}, modals {st['during']})",
              same_rect(st["rect1"], want) and not same_rect(st["rect1"], st["rect0"]))
    return verify


def zoomed(label):
    def verify(st):
        w0, w1 = st["rect0"][2] - st["rect0"][0], st["rect1"][2] - st["rect1"][0]
        check(f"{label}: Alt+RMB zooms in ({w0:.3f} -> {w1:.3f} frames wide, modals {st['during']})",
              w1 < w0 * 0.9 and "VIEW2D_OT_zoom" in st["during"])
    return verify


def panned(label, ref_rect=None, px=D):
    def verify(st):
        a = st["snaps"].get(ref_rect, st["rect0"]) if ref_rect else st["rect0"]
        b = st["rect1"]
        per_px = (a[2] - a[0]) / region().width
        shift = a[0] - b[0]
        check(f"{label}: pans {shift:.3f} (~{px * per_px:.3f} for {px} px), size kept "
              f"({a[2] - a[0]:.3f} -> {b[2] - b[0]:.3f})",
              abs(shift - px * per_px) < 0.1 * px * per_px and abs((b[2] - b[0]) - (a[2] - a[0])) < 1e-3 * (a[2] - a[0]))
    return verify


def still(label, key):
    def verify(st):
        check(f"{label}: the view holds still after the middle button is let go "
              f"({fmt(st['snaps'][key])} -> {fmt(st['rect1'])})", same_rect(st["rect1"], st["snaps"][key], 1e-4))
    return verify


# references: Blender's Alt+RMB zoom, the kit's Alt+MMB / Alt+LMB pan
add_case("altR_h", [('press', 'RIGHTMOUSE'), ('move', D, 0)], verify=zoomed("Alt+RMB right"))
add_case("altR_v", [('press', 'RIGHTMOUSE'), ('move', 0, D)])
add_case("altR_d", [('press', 'RIGHTMOUSE'), ('move', D, D)])
add_case("altM_h", [('press', 'MIDDLEMOUSE'), ('move', D, 0)], verify=panned("Alt+MMB"))
add_case("altL_h", [('press', 'LEFTMOUSE'), ('move', D, 0)], verify=panned("Alt+LMB"))
add_case("zoom_pan", [('press', 'RIGHTMOUSE'), ('move', D, 0), ('release', 'RIGHTMOUSE'), ('press', 'MIDDLEMOUSE'),
                      ('move', D, 0)])
add_case("zoom_zoom", [('press', 'RIGHTMOUSE'), ('move', D, 0), ('release', 'RIGHTMOUSE'), ('press', 'RIGHTMOUSE'),
                       ('move', D, 0)])
# the chord
add_case("chordLM_h", [('press', 'LEFTMOUSE'), ('press', 'MIDDLEMOUSE'), ('move', D, 0)],
         verify=like("altR_h", "Alt+LMB then MMB, drag right"))
add_case("chordML_h", [('press', 'MIDDLEMOUSE'), ('press', 'LEFTMOUSE'), ('move', D, 0)],
         verify=like("altR_h", "Alt+MMB then LMB, drag right"))
add_case("chordLM_v", [('press', 'LEFTMOUSE'), ('press', 'MIDDLEMOUSE'), ('move', 0, D)],
         verify=like("altR_v", "Alt+LMB+MMB, drag up"))
add_case("chordML_d", [('press', 'MIDDLEMOUSE'), ('press', 'LEFTMOUSE'), ('move', D, D)],
         verify=like("altR_d", "Alt+MMB+LMB, drag diagonally"))
# a move before the second button: the first leg pans, then the chord zooms from there
add_case("pan_then_chord", [('press', 'MIDDLEMOUSE'), ('move', D, 0), ('snap', 'panned'), ('press', 'LEFTMOUSE'),
                            ('move', D, 0)],
         verify=lambda st: check(
             "Alt+MMB pan, then LMB: zooms from the panned view "
             f"({fmt(st['snaps']['panned'])} -> {fmt(st['rect1'])})",
             (st["rect1"][2] - st["rect1"][0]) < 0.9 * (st["snaps"]["panned"][2] - st["snaps"]["panned"][0])
             and not same_rect(st["snaps"]["panned"], st["rect0"])))
# letting go of one button (#343 for the 3D View)
add_case("chord_relL", [('press', 'MIDDLEMOUSE'), ('press', 'LEFTMOUSE'), ('move', D, 0), ('snap', 'zoomed'),
                        ('release', 'LEFTMOUSE'), ('move', D, 0)],
         verify=lambda st: (like("zoom_pan", "zoom, let go of LMB, drag: pans like Alt+MMB")(st),
                            panned("after letting go of LMB", "zoomed")(st)))
add_case("chord_relM", [('press', 'LEFTMOUSE'), ('press', 'MIDDLEMOUSE'), ('move', D, 0), ('snap', 'zoomed'),
                        ('release', 'MIDDLEMOUSE'), ('move', D, 0)],
         verify=still("zoom, let go of MMB, drag with LMB", "zoomed"))
add_case("chord_again", [('press', 'MIDDLEMOUSE'), ('press', 'LEFTMOUSE'), ('move', D, 0), ('release', 'LEFTMOUSE'),
                         ('press', 'LEFTMOUSE'), ('move', D, 0)],
         verify=like("zoom_zoom", "zoom, let go of LMB, press it again: zooms on"))
add_case("chord_relM_again", [('press', 'LEFTMOUSE'), ('press', 'MIDDLEMOUSE'), ('move', D, 0),
                              ('release', 'MIDDLEMOUSE'), ('press', 'MIDDLEMOUSE'), ('move', D, 0)],
         verify=like("zoom_zoom", "zoom, let go of MMB, press it again: zooms on"))


# Blender's Zoom to Mouse Position: the chord keeps the point under the mouse like Alt+RMB does then
@step
def s_zoom_to_mouse_on():
    bpy.context.preferences.inputs.use_zoom_to_mouse = True


add_case("altR_mouse", [('press', 'RIGHTMOUSE'), ('move', D, D)], at=(0.3, 0.65))
add_case("chord_mouse", [('press', 'LEFTMOUSE'), ('press', 'MIDDLEMOUSE'), ('move', D, D)], at=(0.3, 0.65),
         verify=like("altR_mouse", "Zoom to Mouse Position on: the chord"))


@step
def s_zoom_to_mouse_off():
    bpy.context.preferences.inputs.use_zoom_to_mouse = False


# the Dope Sheet: the same chord zooms its time axis like Alt+RMB
@step
def s_dope():
    C["area"].ui_type = 'DOPESHEET'


step(lambda: None)
add_case("dope_altR_h", [('press', 'RIGHTMOUSE'), ('move', D, 0)])
add_case("dope_zoom_pan", [('press', 'RIGHTMOUSE'), ('move', D, 0), ('release', 'RIGHTMOUSE'),
                           ('press', 'MIDDLEMOUSE'), ('move', D, 0)])
add_case("dope_chordLM_h", [('press', 'LEFTMOUSE'), ('press', 'MIDDLEMOUSE'), ('move', D, 0)],
         verify=like("dope_altR_h", "Dope Sheet: Alt+LMB+MMB"))
add_case("dope_chord_relL", [('press', 'MIDDLEMOUSE'), ('press', 'LEFTMOUSE'), ('move', D, 0),
                             ('release', 'LEFTMOUSE'), ('move', D, 0)],
         verify=like("dope_zoom_pan", "Dope Sheet: zoom, let go of LMB, drag: pans"))


@step
def s_back():
    C["area"].ui_type = 'FCURVES'


run()
