"""Move handles and Quad Draw project only to live meshes, with a nearer distractor present."""
import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, tap, view3d, win, screenshot

C = {}


def mod(name):
    return import_module(MODULE+'.'+name)


def override():
    a, r = view3d()
    return bpy.context.temp_override(window=win(), area=a, region=r)


def screen(point):
    a, r = view3d()
    p = location_3d_to_region_2d(r, r.data, Vector(point))
    return Vector((r.x+round(p.x), r.y+round(p.y)))


def move(p):
    ev('MOUSEMOVE', 'NOTHING', x=round(p.x), y=round(p.y))


def drag():
    return mod('operators.live_translate').DRAG


def source():
    return bpy.data.objects['Mover']


@step
def s_setup():
    setup()
    with override():
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        refs = []
        for x, z in ((-3, 0), (3, 1)):
            bpy.ops.mesh.primitive_plane_add(size=4, location=(x, 0, z))
            refs.append(bpy.context.object)
        C['refs'] = [o.name for o in refs]
        mod('operators.live').set_objects(bpy.context.scene, refs)
        bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 2))
        bpy.context.object.name = 'Distractor'
        bpy.ops.mesh.primitive_cube_add(size=.4, location=(-3, 0, 4))
        bpy.context.object.name = 'Mover'
        bpy.context.scene.unit_settings.system = 'NONE'
        bpy.context.tool_settings.use_snap = False
        bpy.context.tool_settings.transform_pivot_point = 'MEDIAN_POINT'
        bpy.context.scene.transform_orientation_slots[1].type = 'GLOBAL'
        bpy.ops.wm.tool_set_by_id(name='builtin.move')
        a, r = view3d()
        r.data.view_rotation = Quaternion((1, 0, 0, 0))
        r.data.view_location = (0, 0, 0)
        r.data.view_distance = 16
        bpy.ops.ed.undo_push(message='Before live move')
        C['start'] = screen(source().location)
    move(C['start'])


@step
def s_wait():
    mod('ui.manipulator').ensure_tools(patched=True)
    view3d()[0].tag_redraw()


@step
def s_hover_after_redraw():
    C['start'] = screen(source().location)
    move(C['start'])


@step
def s_press():
    ev('LEFTMOUSE', 'PRESS', x=round(C['start'].x), y=round(C['start'].y))


@step
def s_begin():
    move(C['start']+Vector((8, 0)))


@step
def s_drag():
    check('real Move centre starts the Live surface operator', drag() is not None)
    C['end'] = C['start']+Vector((30, 10))
    move(C['end'])


@step
def s_preview():
    check('Move preview snaps to the live plane, not the nearer distractor', abs(source().location.z) < 1e-5)
    C['after'] = source().location.copy()
    ev('LEFTMOUSE', 'RELEASE', x=round(C['end'].x), y=round(C['end'].y))


@step
def s_commit():
    check('release commits Live movement and clears the modal', drag() is None and (source().location-C['after']).length < 1e-5)
    with override():
        bpy.ops.ed.undo()


@step
def s_undo():
    check('one Undo restores the original position', (source().location-Vector((-3, 0, 4))).length < 1e-5)
    with override():
        bpy.ops.ed.redo()


@step
def s_redo():
    check('Redo restores the accepted surface position', (source().location-C['after']).length < 1e-5)
    with override():
        bpy.ops.allset.live_translate('INVOKE_DEFAULT', constraint_axis=(True, True, False))
    C['cancel'] = source().location.copy()
    move(C['end']+Vector((20, 15)))


@step
def s_plane():
    check('plane handle route also stays on the live surface', abs(source().location.z) < 1e-5)
    tap('ESC')


@step
def s_cancel():
    check('Escape restores the complete pre-drag position', drag() is None and (source().location-C['cancel']).length < 1e-5)
    with override():
        source().hide_set(True)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = None
        bpy.ops.allset.quad_draw_start()
    check('Quad Draw creates a separate mesh for the live list',
          bpy.context.edit_object.name not in C['refs'] and bpy.context.edit_object.name != 'Distractor')
    C['dot'] = screen((3, 0, 1))
    move(C['dot'])


@step
def s_dot_click():
    ev('LEFTMOUSE', 'PRESS', x=round(C['dot'].x), y=round(C['dot'].y))
    ev('LEFTMOUSE', 'RELEASE', x=round(C['dot'].x), y=round(C['dot'].y))


@step
def s_quad_draw():
    bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
    dots = mod('operators.quad_draw').dots(bm)
    check('Quad Draw places a dot on the second live mesh', len(dots) == 1 and abs(dots[0].co.z-1) < 1e-5)
    check('Quad Draw never selects or edits either live reference',
          all(bpy.data.objects[n].mode == 'OBJECT' and bpy.data.objects[n].hide_select for n in C['refs']))
    if os.environ.get('ALLSET_GUI_SHOTS'):
        screenshot(os.path.join(os.environ['ALLSET_GUI_SHOTS'], 'live_quad_draw.png'))


run()
