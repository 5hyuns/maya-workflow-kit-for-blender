"""#380 in a real UI: Ctrl+E on a face, drag the extrude manipulator's arrow out, then a plain click on another face
selects that face (and only it), also after many clicks in a row; the same after an edge extrusion (a click picks an
edge) and in the UV Editor (a click picks a face there)."""

import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras import view3d_utils
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, view3d, win  # noqa: E402

C = {}


def mod(name):
    return import_module(MODULE + name)


def cube():
    return bpy.data.objects["Cube"]


def v3d_ctx():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region, space_data=area.spaces.active)


def rec():
    return mod(".operators.extrude").active(bpy.context)[1]


def selected(kind):
    bm = bmesh.from_edit_mesh(cube().data)
    return sorted(el.index for el in getattr(bm, kind) if el.select)


def face_point(pick):
    """(index, window x, y) of the middle of the face ``pick(face)`` likes best."""
    _area, region = view3d()
    bm = bmesh.from_edit_mesh(cube().data)
    face = max(bm.faces, key=pick)
    p = view3d_utils.location_3d_to_region_2d(region, region.data, cube().matrix_world @ face.calc_center_median())
    return face.index, int(region.x + p.x), int(region.y + p.y)


def front(f):          # the side face that faces the view most: the cube's own front face (y = -1, low)
    return -f.normal.y - 0.01 * f.calc_center_median().z


def right(f):
    return f.normal.x - 0.01 * f.calc_center_median().z


def click(x, y, **mods):
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x + 1, y=y, **mods)
    ev('LEFTMOUSE', 'RELEASE', x=x + 1, y=y, **mods)


def park():
    ev('MOUSEMOVE', 'NOTHING', x=C["x"] - 300, y=C["y"] - 200)


def select_only(mode):
    """Face mode with the top face / edge mode with the top front edge selected."""
    with v3d_ctx():
        bpy.ops.mesh.select_all(action='DESELECT')
    bpy.context.scene.tool_settings.mesh_select_mode = (False, mode == 'EDGE', mode == 'FACE')
    bm = bmesh.from_edit_mesh(cube().data)
    if mode == 'FACE':
        max(bm.faces, key=lambda f: f.calc_center_median().z).select_set(True)
    else:
        max(bm.edges, key=lambda e: sum(v.co.z - v.co.y for v in e.verts)).select_set(True)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(cube().data)


def arrow_point(frac=0.35):
    """Window point on the extrude manipulator's Z arrow and the arrow's screen direction."""
    area, region = view3d()
    in_view = mod(".ui.in_view")
    with v3d_ctx():
        ob, r = in_view.record(bpy.context)
        c, axes, _k = in_view.manip_frame(ob, r)
        upx = in_view.unit_px(bpy.context)
    rv3d = area.spaces.active.region_3d
    p0 = view3d_utils.location_3d_to_region_2d(region, rv3d, c)
    w = view3d_utils.region_2d_to_location_3d(region, rv3d, p0 + Vector((1, 0)), c) - c
    p = view3d_utils.location_3d_to_region_2d(region, rv3d, c + axes.col[2] * upx * w.length * frac)
    return region.x + round(p.x), region.y + round(p.y), (p - p0).normalized()


def extrude_and_drag(tag):
    """Ctrl+E, then a real drag of the manipulator's Z arrow (four steps), like pulling the extrusion out."""
    @step
    def s_ctrl_e():
        park()
        ev('E', 'PRESS', ctrl=True)
        ev('E', 'RELEASE', ctrl=True)

    @step
    def s_hover():
        x, y, d = C[tag + "arrow"] = arrow_point()
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y + 1)

    @step
    def s_press():
        x, y, _d = C[tag + "arrow"]
        ev('LEFTMOUSE', 'PRESS', x=x, y=y + 1)

    @step
    def s_moves():
        x, y, d = C[tag + "arrow"]
        for i in range(1, 9):
            ev('MOUSEMOVE', 'NOTHING', x=x + round(d.x * 60 * i / 8), y=y + 1 + round(d.y * 60 * i / 8))

    @step
    def s_release():
        x, y, d = C[tag + "arrow"]
        ev('LEFTMOUSE', 'RELEASE', x=x + round(d.x * 60), y=y + 1 + round(d.y * 60))

    @step
    def s_dragged():
        r = rec()
        ltz = r.params.get("local_translate_z") if r else None
        check(f"{tag}: Ctrl+E + a drag on the arrow pulled the extrusion out ({r and r.name}, Local Translate Z {ltz})",
              r is not None and ltz is not None and ltz > 0.05)
        park()


@step
def s_setup():
    C["x"], C["y"] = setup()
    bpy.context.view_layer.objects.active = cube()
    cube().select_set(True)
    with v3d_ctx():
        bpy.ops.object.mode_set('EXEC_DEFAULT', True, mode='EDIT')
        bpy.ops.wm.tool_set_by_id(name="builtin.move")
    select_only('FACE')
    park()


extrude_and_drag("face")


@step
def s_click_front():
    C["front"], x, y = face_point(front)
    click(x, y)


@step
def s_front_check():
    sel = selected("faces")
    check(f"after the extrusion a click selects the clicked face ({sel} = [{C['front']}])", sel == [C["front"]])
    C["right"], x, y = face_point(right)
    click(x, y)


@step
def s_right_check():
    sel = selected("faces")
    check(f"and a click on another face selects that one ({sel} = [{C['right']}])", sel == [C["right"]])
    # many clicks in a row (plain / Shift / Ctrl / Ctrl+Shift, some double), over faces and empty space
    pts = [face_point(front)[1:], face_point(right)[1:], (C["x"] - 300, C["y"] - 200)]
    mods = ({}, {"shift": True}, {"ctrl": True}, {"shift": True, "ctrl": True})
    for i in range(40):
        x, y = pts[i % 3]
        click(x, y, **mods[i % 4])
        if i % 7 == 0:
            click(x, y)


@step
def s_many_clicks():
    C["front"], x, y = face_point(front)
    click(x, y)


@step
def s_many_check():
    sel = selected("faces")
    check(f"after 40 more clicks a plain click still selects the clicked face ({sel} = [{C['front']}])",
          sel == [C["front"]])
    select_only('EDGE')
    park()


extrude_and_drag("edge")


@step
def s_click_edge():
    _area, region = view3d()
    bm = bmesh.from_edit_mesh(cube().data)
    # the cube's front right vertical edge (seen from the front right)
    edge = max(bm.edges, key=lambda e: (abs(e.verts[0].co.z - e.verts[1].co.z) > 1.0,
                                        sum(v.co.x - v.co.y for v in e.verts)))
    mid = cube().matrix_world @ ((edge.verts[0].co + edge.verts[1].co) / 2)
    p = view3d_utils.location_3d_to_region_2d(region, region.data, mid)
    C["edge"] = edge.index
    click(int(region.x + p.x), int(region.y + p.y))


@step
def s_edge_check():
    sel = selected("edges")
    check(f"after an edge extrusion a click selects the clicked edge ({sel} = [{C['edge']}])", sel == [C["edge"]])
    select_only('FACE')
    # the Properties editor on the right becomes a UV Editor
    area = max((a for a in win().screen.areas if a.type == 'PROPERTIES'), key=lambda a: a.height)
    area.type = 'IMAGE_EDITOR'
    area.ui_type = 'UV'
    C["uv_area"] = area
    park()


extrude_and_drag("uv")


@step
def s_uv_frame():
    area = C["uv_area"]
    region = next(r for r in area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.image.view_all(fit_view=True)
    bpy.context.scene.tool_settings.use_uv_select_sync = True


@step
def s_uv_click():
    area = C["uv_area"]
    region = next(r for r in area.regions if r.type == 'WINDOW')
    bm = bmesh.from_edit_mesh(cube().data)
    uv = bm.loops.layers.uv.active
    face = max(bm.faces, key=front)
    centre = sum((loop[uv].uv for loop in face.loops), Vector((0, 0))) / len(face.loops)
    x, y = region.view2d.view_to_region(centre.x, centre.y, clip=False)
    C["uv_face"] = face.index
    click(region.x + x, region.y + y)


@step
def s_uv_check():
    sel = selected("faces")
    check(f"in the UV Editor (UV Sync Selection) a click selects the clicked face ({sel} = [{C['uv_face']}])",
          sel == [C["uv_face"]])


run()
