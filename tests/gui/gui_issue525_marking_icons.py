"""In a real UI (#525): marking menu items show their command's picture left of the label, on the radial boxes and in
the list (Shift+RMB with an edge selected, its Soften/Harden Edges submenu, Shift+RMB on the object, Ctrl+RMB which
shows none); the menu draws as fast with the pictures (screenshots)."""

import os
import sys
import time
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, setup, screenshot, step, tap, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {"times": []}


def mod(name):
    return import_module(sys.modules["sim"].MODULE + name)


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def session():
    return mod(".marking.draw").ACTIVE.get("session")


def _timed_draws():
    """Time each drawing of the open menu (every region of the window draws it)."""
    draw = mod(".marking.draw")
    plain = draw.draw_session

    def timed(*a, **kw):
        t0 = time.perf_counter()
        try:
            return plain(*a, **kw)
        finally:
            C["times"].append(time.perf_counter() - t0)
    draw.draw_session = timed
    C["plain"] = plain


def _times(label):
    t = C["times"][:]
    C["times"].clear()
    return t


@step
def s_setup():
    C["x"], C["y"] = setup()
    area, region = view3d()
    cube = bpy.data.objects["Cube"]
    bpy.context.view_layer.objects.active = cube
    cube.select_set(True)
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.mesh_select_mode = (False, True, False)
    b = bmesh.from_edit_mesh(cube.data)
    for el in (*b.verts, *b.edges, *b.faces):
        el.select = False
    b.edges.ensure_lookup_table()
    b.edges[0].select_set(True)
    bmesh.update_edit_mesh(cube.data)
    _timed_draws()
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])


@step
def s_wait_pictures():
    """The pictures are made ahead from a timer after Maya mode turns on."""
    import sim
    icons = mod(".marking.icons")
    want = len(set(mod(".marking.icon_data").ICONS.values()))
    made = sum(1 for k in icons._pixels if k[1] == icons.size())
    C["wait"] = C.get("wait", 0) + 1
    if made < want and C["wait"] < 25:
        sim._steps.insert(0, s_wait_pictures)
        return
    check(f"every marking picture made ahead ({made} / {want})", made >= want)


def _press():
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('LEFT_SHIFT', 'PRESS', x=C["x"], y=C["y"])
    ev('RIGHTMOUSE', 'PRESS', x=C["x"], y=C["y"], shift=True)


def _close():
    tap('ESC')
    ev('RIGHTMOUSE', 'RELEASE', x=C["x"], y=C["y"], shift=True)
    ev('LEFT_SHIFT', 'RELEASE', x=C["x"], y=C["y"])


@step
def s_base_press():
    # the same menu without pictures: how long its drawing takes
    data = mod(".marking.icon_data")
    C["icons"] = data.ICONS
    data.ICONS = {}
    _press()


@step
def s_base_shown():
    C["base_first"] = _times("base open")
    mod(".marking.draw").redraw()


@step
def s_base_steady():
    s = session()
    check("the menu without pictures is open", s is not None and not any(it.icon for it in s.layout.items))
    C["base"] = _times("base")
    _close()
    mod(".marking.icon_data").ICONS = C["icons"]


@step
def s_press():
    check("menu closed", not mod(".marking.draw").ACTIVE)
    _times("closed")
    _press()


@step
def s_edge_menu():
    s = session()
    name = getattr(s.stack[0][0].sub, "name", None) if s else None
    check(f"Shift+RMB with an edge selected opens the edge menu ({name})", name == "SHIFT_EDGE")
    if s is None:
        return
    with_pic = sorted(it.label for it in s.layout.items if it.icon)
    check(f"items with a picture: Bevel Edge, Bridge, Multi-Cut ... ({with_pic})",
          {"Bevel Edge", "Bridge", "Multi-Cut"} <= set(with_pic))
    shot("gui_issue525_edge_menu.png")
    C["first"] = _times("edge")
    check(f"the menu was drawn ({len(C['first'])} draws)", bool(C["first"]))
    mod(".marking.draw").redraw()


@step
def s_edge_steady():
    t = _times("steady")
    base, base_first, first = C["base"], C["base_first"], C["first"]

    def ms(v):
        return sorted(round(x * 1000, 2) for x in v)[-5:]
    print(f"marking draw ms (largest): without pictures first {ms(base_first)}, later {ms(base)}; with pictures "
          f"first {ms(first)}, later {ms(t)}")
    # the pictures are made ahead: opening the menu only uploads them (drawing them there took 40+ ms)
    first_limit = max(base_first, default=0.008) * 1.5 + 0.01
    limit = max(base, default=0.004) * 1.5 + 0.0015
    top_first, top = max(first, default=1.0), max(t, default=1.0)
    check(f"the first drawing with pictures stays quick ({top_first:.4f} <= {first_limit:.4f} s)",
          top_first <= first_limit)
    check(f"later drawings with pictures as quick as without ({top:.4f} <= {limit:.4f} s)", top <= limit)
    s = session()
    item = next((it for it in s.layout.radial.values() if it.label == "Soften/Harden Edges"), None) if s else None
    check("Soften/Harden Edges in the ring", item is not None)
    if item is None:
        return
    r = item.rect
    x = C["x"] + int(s.center[0] - s.press[0] + (r[0] + r[2]) / 2)
    y = C["y"] + int(s.center[1] - s.press[1] + (r[1] + r[3]) / 2)
    C["sub_at"] = (x, y)
    ev('MOUSEMOVE', 'NOTHING', x=(C["x"] + x) // 2, y=(C["y"] + y) // 2, shift=True)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y, shift=True)


@step
def s_rest():
    pass        # resting on the radial submenu item opens it


@step
def s_submenu():
    s = session()
    path = s.layout.path if s else None
    check(f"the Soften/Harden Edges submenu opened ({path})", path == "SHIFT_EDGE/Soften/Harden Edges")
    labels = sorted(it.label for it in s.layout.items if it.icon) if s else []
    check(f"its items show pictures ({labels})", {"Harden Edge", "Soften Edge"} <= set(labels))
    shot("gui_issue525_edge_submenu.png")
    x, y = C["sub_at"]
    tap('ESC')
    ev('RIGHTMOUSE', 'RELEASE', x=x, y=y, shift=True)
    ev('LEFT_SHIFT', 'RELEASE', x=x, y=y)


@step
def s_object_mode():
    check("menu closed", not mod(".marking.draw").ACTIVE)
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set(mode='OBJECT')
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('LEFT_SHIFT', 'PRESS', x=C["x"], y=C["y"])
    ev('RIGHTMOUSE', 'PRESS', x=C["x"], y=C["y"], shift=True)


@step
def s_object_menu():
    s = session()
    name = getattr(s.stack[0][0].sub, "name", None) if s else None
    check(f"Shift+RMB on the object opens the object menu ({name})", name == "SHIFT_OBJECT")
    if s is not None:
        rows = [it for it in s.layout.items if it.kind == "list"]
        check("the list keeps one label column", len({round(it.text_x, 3) for it in rows}) == 1)
        greyed = [it.label for it in rows if it.icon and not it.enabled]
        print("greyed items with a picture:", greyed)
    shot("gui_issue525_object_menu.png")
    tap('ESC')
    ev('RIGHTMOUSE', 'RELEASE', x=C["x"], y=C["y"], shift=True)
    ev('LEFT_SHIFT', 'RELEASE', x=C["x"], y=C["y"])


@step
def s_ctrl():
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('LEFT_CTRL', 'PRESS', x=C["x"], y=C["y"])
    ev('RIGHTMOUSE', 'PRESS', x=C["x"], y=C["y"], ctrl=True)


@step
def s_ctrl_menu():
    s = session()
    check("Ctrl+RMB menu: no pictures", s is not None and not any(it.icon for it in s.layout.items))
    shot("gui_issue525_convert_menu.png")
    tap('ESC')
    ev('RIGHTMOUSE', 'RELEASE', x=C["x"], y=C["y"], ctrl=True)
    ev('LEFT_CTRL', 'RELEASE', x=C["x"], y=C["y"])


@step
def s_end():
    check("menu closed at the end", not mod(".marking.draw").ACTIVE)
    mod(".marking.draw").draw_session = C["plain"]


run()
