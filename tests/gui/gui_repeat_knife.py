"""G reopens a modal shelf tool after a cut, rather than replaying the older command."""
import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, tap, view3d, win

rep = import_module(MODULE + '.operators.repeat_maya')
shelf = import_module(MODULE + '.ui.shelf')


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def knife_running():
    return any(op.bl_idname == 'MESH_OT_knife_tool' for op in win().modal_operators)


def point(x, y):
    area, region = view3d()
    p = location_3d_to_region_2d(region, area.spaces.active.region_3d, Vector((x, y, 0)))
    ev('MOUSEMOVE', 'NOTHING', x=region.x + round(p.x), y=region.y + round(p.y))


def counts():
    with override():
        bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
        return len(bm.verts), len(bm.faces)


def undo_key(redo=False):
    ev('LEFT_CTRL', 'PRESS')
    if redo:
        ev('LEFT_SHIFT', 'PRESS', ctrl=True)
    ev('Z', 'PRESS', ctrl=True, shift=redo)
    ev('Z', 'RELEASE', ctrl=True, shift=redo)
    if redo:
        ev('LEFT_SHIFT', 'RELEASE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


@step
def prepare():
    setup()
    load_maya_layout()


@step
def launch_shelf_knife():
    bpy.ops.allset.keymap_activate()
    shelf.user_data()['shelves'].append({'name': 'KnifeRepeat', 'buttons': [{
        'label': 'Split Polygon (Knife)', 'type': 'action', 'action': {
            'type': 'operator', 'id': 'mesh.knife_tool', 'properties': {},
            'space_type': 'VIEW_3D', 'required_mode': 'EDIT_MESH'}}]})
    with override():
        bpy.ops.mesh.primitive_plane_add(size=2)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.view3d.view_axis(type='TOP')
        area, _region = view3d()
        area.spaces.active.region_3d.view_location = (0, 0, 0)
        area.spaces.active.region_3d.view_distance = 5
        rep.record('Older command', 'allset.merge')
    point(0, 0)
    row = next(a for a in win().screen.areas if a.type == 'IMAGE_EDITOR')
    region = next(r for r in row.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=win(), area=row, region=region):
        res = bpy.ops.allset.shelf_button(shelf='USER:KnifeRepeat', index=0)
    check('shelf Knife starts its modal handler', res == {'RUNNING_MODAL'} and knife_running())


@step
def first_cut_start():
    point(-1, 0)
    tap('LEFTMOUSE')


@step
def first_cut_end():
    point(1, 0)
    tap('LEFTMOUSE')
    tap('RET')


@step
def repeat_after_cut():
    check(f'first Knife cut completed ({counts()})', counts() == (6, 2) and not knife_running())
    check('Repeat remembers the Knife shelf command', rep.HISTORY[-1]['action'][0] == 'mesh.knife_tool')
    rows = rep.recent(bpy.context)
    check('Recent Commands offers the invokable Knife command once',
          rows[0][0] == 'kit' and not any(row[0] == 'blender' and row[2] == 'Knife Topology Tool' for row in rows))
    point(0, 0)
    tap('G')


@step
def second_cut_start():
    check('G reopens Knife', knife_running())
    if knife_running():
        point(0, -1)
        tap('LEFTMOUSE')


@step
def second_cut_end():
    if knife_running():
        point(0, 1)
        tap('LEFTMOUSE')
        tap('RET')


@step
def undo_second_cut():
    check(f'repeated Knife makes a fresh cut ({counts()})', counts() == (9, 4))
    undo_key()


@step
def redo_second_cut():
    check(f'one Undo removes only the repeated cut ({counts()})', counts() == (6, 2))
    undo_key(redo=True)


@step
def repeat_again():
    check(f'Redo restores the repeated cut ({counts()})', counts() == (9, 4))
    point(0, 0)
    tap('G')


@step
def cancel_repeat():
    check('G can reopen Knife again', knife_running())
    tap('ESC')


@step
def cancelled():
    check('cancelled repeat leaves the mesh intact', not knife_running() and counts() == (9, 4))
    check('repeated/cancelled Knife keeps one invokable recent command',
          not any(row[0] == 'blender' and row[2] == 'Knife Topology Tool' for row in rep.recent(bpy.context)))
    with override():
        # A genuinely newer command must still win over the saved modal invocation.
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.subdivide('EXEC_DEFAULT', True, number_cuts=1)
        what = rep.last(bpy.context)
        check('a newer registered command replaces Knife', what[0] == 'blender' and
              bpy.context.window_manager.operators[what[1]].bl_idname == 'MESH_OT_subdivide')


run()
