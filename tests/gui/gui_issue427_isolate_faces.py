"""#427 in a real UI: Isolate Select (Ctrl+1) with components selected shows only their faces, like Maya.

Two 4x4 grids pA / pB edited together, a face of pA hidden by the user first. Faces selected: Ctrl+1 shows only them
(pB, with nothing selected, leaves the view); vertices / edges selected: the faces using their vertices. Space to the
four view and back keeps it; Ctrl+1 again, the Show menu, turning the panel into another editor and Ctrl+1 from Object
Mode bring the faces back, the user's hidden face staying hidden (also one hidden while isolated; Reveal
while isolated leaves nothing behind). Show > Isolate Select > Add / Remove Selected
Objects add and take out faces. Undo back past Ctrl+1 keeps the isolation, and redo after it ended leaves no face
hidden by it. Isolate Select in Object Mode hides no face."""

import os
import sys
from importlib import import_module

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {"u": 1.0}
ATTR = "allset_isolate_hidden"


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def fv():
    return import_module(f"{MODULE}.ui.four_view")


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def persp():
    roles = fv().roles(win().screen)
    return roles["persp"] if roles else view3d()[0]


def region_of(area):
    return next(r for r in area.regions if r.type == 'WINDOW')


def override(area=None):
    area = area or persp()
    return bpy.context.temp_override(window=win(), screen=win().screen, area=area, region=region_of(area))


def key(k, **mods):
    ev(k, 'PRESS', **mods)
    ev(k, 'RELEASE', **mods)


def ctrl_one(area=None):
    r = region_of(area or persp())
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + int(r.height * 0.9))
    ev('LEFT_CTRL', 'PRESS')
    key('ONE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


def space_tap():
    def move():
        r = region_of(persp())
        C["xy"] = (r.x + r.width // 2, r.y + int(r.height * 0.9))
        ev('MOUSEMOVE', 'NOTHING', x=C["xy"][0], y=C["xy"][1])

    def tap():
        x, y = C["xy"]
        ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)
        ev('SPACE', 'PRESS', x=x, y=y)
        ev('SPACE', 'RELEASE', x=x, y=y)
    step(move)
    step(tap)
    wait(3)


def wait(n=4):
    for _ in range(n):
        step(redraw)


def A():
    return bpy.data.objects["pA"]


def bm_of(ob=None):
    ob = ob or A()
    bm = bmesh.from_edit_mesh(ob.data)
    bm.faces.index_update()
    bm.verts.index_update()
    bm.edges.index_update()
    return bm


def hidden(ob=None):
    ob = ob or A()
    if ob.mode == 'EDIT':
        return sorted(f.index for f in bm_of(ob).faces if f.hide)
    return sorted(p.index for p in ob.data.polygons if p.hide)


def marked(ob=None):
    ob = ob or A()
    if ob.mode == 'EDIT':
        layer = bm_of(ob).faces.layers.int.get(ATTR)
        return None if layer is None else sorted(f.index for f in bm_of(ob).faces if f[layer])
    a = ob.data.attributes.get(ATTR)
    return None if a is None else [i for i, d in enumerate(a.data) if d.value]


def everything_but(keep):
    return sorted(set(range(16)) - set(keep))


def face_at(x, y):
    """pA's face whose centre is nearest (x, y) in grid units (cells 1 wide, -2 .. 2)."""
    bm = bm_of()
    return min(bm.faces, key=lambda f: (f.calc_center_median() / C["u"] - Vector((x, y, 0))).length).index


def vert_at(x, y):
    bm = bm_of()
    return min(bm.verts, key=lambda v: (v.co / C["u"] - Vector((x, y, 0))).length).index


def select_only(mode, faces=(), verts=(), edges=()):
    """Select mode ``mode`` ('VERT' / 'EDGE' / 'FACE') with exactly these elements of pA (pB nothing)."""
    ts = bpy.context.scene.tool_settings
    ts.mesh_select_mode = (mode == 'VERT', mode == 'EDGE', mode == 'FACE')
    for ob in (A(), bpy.data.objects["pB"]):
        if ob.mode != 'EDIT':
            continue
        bm = bm_of(ob)
        for seq in (bm.verts, bm.edges, bm.faces):
            for el in seq:
                el.select_set(False)
        if ob == A():
            bm.faces.ensure_lookup_table()
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            for i in faces:
                bm.faces[i].select_set(True)
            for i in verts:
                bm.verts[i].select_set(True)
            for i in edges:
                bm.edges[i].select_set(True)
        bm.select_mode = {mode}
        bm.select_flush_mode()
        bmesh.update_edit_mesh(ob.data)


def faces_of_verts(vs):
    bm = bm_of()
    bm.verts.ensure_lookup_table()
    return sorted({f.index for i in vs for f in bm.verts[i].link_faces})


def in_view(name, area=None):
    sp = (area or persp()).spaces.active
    return sp.local_view is not None and bpy.data.objects[name].local_view_get(sp)


def isolating(area=None):
    return (area or persp()).spaces.active.local_view is not None


@step
def s_setup():
    setup()
    load_maya_layout()


wait(4)


@step
def s_scene():
    sc = bpy.context.scene
    C["u"] = u = import_module(MODULE + ".operators.units").maya_unit(sc)
    for ob in list(bpy.data.objects):
        if ob.type == 'MESH':
            bpy.data.objects.remove(ob)
    for name, x in (("pA", 0.0), ("pB", 6.0)):
        me = bpy.data.meshes.new(name)
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=4, y_segments=4, size=2.0 * u)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(name, me)
        ob.location.x = x * u
        sc.collection.objects.link(ob)
    for ob in sc.objects:
        ob.select_set(ob.name in ("pA", "pB"))
    bpy.context.view_layer.objects.active = A()
    rv3d = persp().spaces.active.region_3d
    rv3d.view_perspective = 'ORTHO'
    rv3d.view_rotation = (1, 0, 0, 0)
    rv3d.view_location = (3 * u, 0, 0)
    rv3d.view_distance = 14.0 * u
    with override():
        bpy.ops.ed.undo_push(message="scene")
    with override():
        bpy.ops.object.mode_set(mode='EDIT')
    C["user"] = face_at(-1.5, -1.5)            # a corner face the user hides
    bm = bm_of()
    bm.faces.ensure_lookup_table()
    bm.faces[C["user"]].hide_set(True)
    bmesh.update_edit_mesh(A().data)
    with override():
        bpy.ops.ed.undo_push(message="user hide")
    C["two"] = sorted({face_at(-0.5, 0.5), face_at(0.5, 0.5)})
    select_only('FACE', faces=C["two"])


wait(2)


@step
def s_faces_iso():
    ctrl_one()


wait(2)


@step
def s_faces_iso_on():
    check(f"Ctrl+1 with two faces selected isolates ({isolating()})", isolating())
    check(f"... pA shows only the two faces (hidden {hidden()})", hidden() == everything_but(C["two"]))
    check(f"... the kit marks only the faces it hid (marked {marked()})",
          marked() == sorted(set(everything_but(C["two"])) - {C["user"]}))
    check(f"... pA in the view, pB (nothing selected) not ({in_view('pA')}, {in_view('pB')})",
          in_view("pA") and not in_view("pB"))
    check(f"... the two faces stay selected ({[f.index for f in bm_of().faces if f.select]})",
          sorted(f.index for f in bm_of().faces if f.select) == C["two"])
    shot("gui_issue427_faces.png")


space_tap()


@step
def s_four():
    check(f"Space: the four view, persp still isolates pA's two faces ({isolating()}, {hidden()})",
          fv().is_four(win().screen) and isolating() and hidden() == everything_but(C["two"]))


space_tap()


@step
def s_single():
    check(f"Space: one panel again, still only the two faces ({isolating()}, {hidden()})",
          len(fv().panes(win().screen)) == 1 and isolating() and hidden() == everything_but(C["two"]))
    ctrl_one()


wait(2)


@step
def s_faces_off():
    check(f"Ctrl+1 again: Isolate Select ends ({isolating()})", not isolating())
    check(f"... every face is back but the user's hidden one ({hidden()})", hidden() == [C["user"]])
    check(f"... the kit's attribute is gone ({marked()})", marked() is None)
    C["vert"] = vert_at(0, 0)
    select_only('VERT', verts=[C["vert"]])


wait(1)


@step
def s_vert_iso():
    ctrl_one()


wait(2)


@step
def s_vert_on():
    want = faces_of_verts([C["vert"]])
    check(f"Ctrl+1 with a vertex: the faces around it ({sorted(set(range(16)) - set(hidden()))} vs {want})",
          hidden() == everything_but(want))
    ctrl_one()


wait(2)


@step
def s_edge_sel():
    check(f"... Ctrl+1 again shows them all ({hidden()})", hidden() == [C["user"]])
    bm = bm_of()
    bm.faces.ensure_lookup_table()
    f1, f2 = (bm.faces[i] for i in C["two"])
    e = next(e for e in f1.edges if e in f2.edges)
    C["edge"] = e.index
    C["edge_verts"] = [v.index for v in e.verts]
    select_only('EDGE', edges=[C["edge"]])


wait(1)


@step
def s_edge_iso():
    ctrl_one()


wait(2)


@step
def s_edge_on():
    want = sorted(set(faces_of_verts(C["edge_verts"])) - {C["user"]})
    C["keep"] = want
    check(f"Ctrl+1 with an edge: the faces using its vertices ({len(want)} faces; hidden {hidden()})",
          hidden() == everything_but(want) and len(want) == 6)
    # Add Selected Objects with a vertex on the edge of what is shown: its faces join
    bm = bm_of()
    shown = {f for f in bm.faces if not f.hide}
    v = next(v for v in bm.verts if not v.hide and any(f.hide for f in v.link_faces)
             and any(f in shown for f in v.link_faces) and C["user"] not in {f.index for f in v.link_faces})
    C["add_v"] = v.index
    select_only('VERT', verts=[v.index])
    with override():
        bpy.ops.allset.isolate_edit(action='ADD')


wait(1)


@step
def s_added():
    want = sorted(set(C["keep"]) | set(faces_of_verts([C["add_v"]])))
    C["keep"] = want
    check(f"Add Selected Objects with a vertex: its faces are shown too ({len(want)}; hidden {hidden()})",
          hidden() == everything_but(want))
    C["rm"] = C["two"][0]
    select_only('FACE', faces=[C["rm"]])
    with override():
        bpy.ops.allset.isolate_edit(action='REMOVE')


wait(1)


@step
def s_removed():
    want = sorted(set(C["keep"]) - {C["rm"]})
    C["keep"] = want
    check(f"Remove Selected Objects with a face: it is hidden ({hidden()})", hidden() == everything_but(want))
    select_only('FACE', faces=[C["two"][1]])
    with override():
        bpy.ops.transform.translate('EXEC_DEFAULT', True, value=(0, 0, 0.2 * C["u"]))


wait(1)


@step
def s_undo():
    with override():
        bpy.ops.ed.undo()          # the move: back to the user's hide, before Ctrl+1


wait(2)


@step
def s_undone():
    check(f"Undo back past Ctrl+1: still isolated, the same faces shown ({isolating()}, {hidden()})",
          isolating() and hidden() == everything_but(C["keep"]))
    with override():
        bpy.ops.ed.redo()


wait(2)


@step
def s_redone():
    check(f"Redo: the same faces shown ({hidden()})", hidden() == everything_but(C["keep"]))
    ctrl_one()


wait(2)


@step
def s_off_then_redo():
    check(f"Ctrl+1: all back but the user's face ({hidden()})", hidden() == [C["user"]])
    with override():
        bpy.ops.ed.undo()


wait(2)


@step
def s_off_redo2():
    with override():
        bpy.ops.ed.redo()          # the step made while isolating


wait(2)


@step
def s_no_leftover():
    check(f"Undo / redo after Isolate Select ended leave no face it hid ({hidden()}, {marked()})",
          hidden() == [C["user"]] and marked() is None and not isolating())
    select_only('FACE', faces=C["two"])


wait(1)


@step
def s_menu_iso():
    ctrl_one()


wait(2)


@step
def s_menu_off():
    check(f"Ctrl+1 again with two faces ({hidden()})", hidden() == everything_but(C["two"]))
    with override():
        bpy.ops.allset.panel_set(key="ISOLATE")      # Show > Isolate Select > View Selected


wait(2)


@step
def s_menu_back():
    check(f"Show > Isolate Select > View Selected ends it, faces back ({isolating()}, {hidden()})",
          not isolating() and hidden() == [C["user"]])
    select_only('FACE', faces=C["two"])


wait(1)


@step
def s_panel_iso():
    ctrl_one()


wait(2)


@step
def s_panel_close():
    check(f"Ctrl+1 once more ({hidden()})", hidden() == everything_but(C["two"]))
    C["area"] = persp().as_pointer()
    persp().ui_type = 'OUTLINER'


wait(4)


@step
def s_panel_gone():
    check(f"The panel turned into the Outliner: the faces come back ({hidden()})", hidden() == [C["user"]])
    area = next(a for a in win().screen.areas if a.as_pointer() == C["area"])
    area.ui_type = 'VIEW_3D'


wait(2)


@step
def s_panel_restored():
    sp = persp().spaces.active
    if sp.local_view is not None:
        with override():
            bpy.ops.view3d.localview(frame_selected=False)
    select_only('FACE', faces=C["two"])


wait(1)


@step
def s_obj_iso():
    ctrl_one()


wait(2)


@step
def s_to_object():
    check(f"Ctrl+1 with two faces again ({hidden()})", hidden() == everything_but(C["two"]))
    with override():
        bpy.ops.object.mode_set(mode='OBJECT')


wait(1)


@step
def s_object_mode():
    check(f"Object Mode: Isolate Select stays ({isolating()})", isolating())
    ctrl_one()


wait(2)


@step
def s_object_off():
    check(f"Ctrl+1 in Object Mode ends it, faces back in the mesh ({hidden()}, {marked()})",
          not isolating() and hidden() == [C["user"]] and marked() is None)
    for ob in bpy.context.scene.objects:
        ob.select_set(ob.name == "pB")
    bpy.context.view_layer.objects.active = bpy.data.objects["pB"]
    ctrl_one()


wait(2)


@step
def s_object_iso():
    check(f"Object Mode Ctrl+1 isolates pB whole ({in_view('pB')}, {in_view('pA')})",
          in_view("pB") and not in_view("pA"))
    pb = bpy.data.objects["pB"]
    check(f"... no face of it hidden ({hidden(pb)}, {marked(pb)})", hidden(pb) == [] and marked(pb) is None)
    ctrl_one()


wait(2)


@step
def s_end():
    check(f"... Ctrl+1 again ends it ({isolating()})", not isolating())
    for ob in bpy.context.scene.objects:
        ob.select_set(ob.name == "pA")
    bpy.context.view_layer.objects.active = A()
    with override():
        bpy.ops.object.mode_set(mode='EDIT')
    select_only('FACE', faces=C["two"])


wait(1)


@step
def s_hide_iso():
    ctrl_one()


wait(2)


@step
def s_hide_in_iso():
    check(f"Ctrl+1 with two faces ({hidden()})", hidden() == everything_but(C["two"]))
    select_only('FACE', faces=[C["two"][0]])
    with override():
        bpy.ops.mesh.hide(unselected=False)          # the user hides one of the isolated faces
    ctrl_one()


wait(2)


@step
def s_hide_kept():
    check(f"A face hidden while isolated stays hidden after Ctrl+1 ({hidden()})",
          hidden() == sorted({C["user"], C["two"][0]}))
    with override():
        bpy.ops.mesh.reveal()
    select_only('FACE', faces=C["two"])


wait(1)


@step
def s_reveal_iso():
    check(f"Reveal shows every face ({hidden()})", hidden() == [])
    ctrl_one()


wait(2)


@step
def s_reveal_in_iso():
    check(f"Ctrl+1 with two faces ({hidden()})", hidden() == everything_but(C["two"]))
    with override():
        bpy.ops.mesh.reveal()                         # Show All while isolated
    ctrl_one()


wait(2)


@step
def s_reveal_done():
    check(f"Reveal while isolated, then Ctrl+1: every face shown, no mark left ({hidden()}, {marked()})",
          hidden() == [] and marked() is None and not isolating())


run()
