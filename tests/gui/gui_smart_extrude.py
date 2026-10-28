"""Modern Smart Extrude in the real viewport: handles, shared node, cancel, Undo and G."""
import math
import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, tap, view3d, win

C = {}


def mod(name):
    return import_module(MODULE+'.'+name)


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def bm():
    return bmesh.from_edit_mesh(bpy.context.edit_object.data)


def volume():
    return bm().calc_volume()


def typed(text):
    for char in text:
        ev('TEXTINPUT', 'PRESS', unicode=char)


@step
def s_setup():
    C['mouse'] = setup()
    with override():
        bpy.ops.object.select_all(action='DESELECT')
        ob = bpy.data.objects['Cube']
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.context.scene.unit_settings.system = 'NONE'
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
        top = max(bm().faces, key=lambda f: f.calc_center_median().z)
        top.select_set(True)
        bmesh.update_edit_mesh(ob.data)
        bpy.ops.allset.menu_item(item='Edit Mesh/Smart Extrude')
    ev('MOUSEMOVE', 'NOTHING', x=C['mouse'][0], y=C['mouse'][1])


@step
def s_hover():
    with override():
        check('menu activates modern Smart Extrude tool', mod('operators.smart_extrude').active(bpy.context))
        centre, axes = mod('ui.smart_extrude').widget_frame(bpy.context)
        area, region = view3d()
        p = location_3d_to_region_2d(region, region.data, centre)
        q = location_3d_to_region_2d(region, region.data, centre+axes.col[2]*.1)
        d = (q-p).normalized()
        point = p+d*mod('ui.in_view').unit_px(bpy.context)*.75
        C['start'] = round(region.x+point.x), round(region.y+point.y)
        C['end'] = round(C['start'][0]+d.x*70), round(C['start'][1]+d.y*70)
        C['before'] = mod('operators.smart_extrude').signature(bm())
    ev('MOUSEMOVE', 'NOTHING', x=C['start'][0], y=C['start'][1])


@step
def s_press():
    ev('LEFTMOUSE', 'PRESS', x=C['start'][0], y=C['start'][1])


@step
def s_move():
    for i in range(1, 9):
        ev('MOUSEMOVE', 'NOTHING', x=round(C['start'][0]+(C['end'][0]-C['start'][0])*i/8),
           y=round(C['start'][1]+(C['end'][1]-C['start'][1])*i/8))


@step
def s_preview():
    drag = mod('operators.smart_extrude').DRAG
    check('real arrow invokes Smart Extrude drag', drag is not None)
    check('outward preview grows a closed volume', volume() > 8.05 and all(e.is_manifold for e in bm().edges))
    ev('LEFTMOUSE', 'RELEASE', x=C['end'][0], y=C['end'][1])


@step
def s_committed():
    C['extruded_volume'] = volume()
    check('release commits and cleans up modal state', mod('operators.smart_extrude').DRAG is None and volume() > 8.05)
    C['after'] = mod('operators.smart_extrude').signature(bm())
    with override():
        bpy.ops.ed.undo()


@step
def s_undo():
    check('Undo restores the original cube topology and volume', len(bm().faces) == 6 and abs(volume()-8) < 1e-5)
    with override():
        bpy.ops.ed.redo()


@step
def s_redo():
    check('Redo restores the exact Smart Extrude result', abs(volume()-C['extruded_volume']) < 1e-5)
    with override():
        bpy.ops.allset.smart_extrude_drag('INVOKE_DEFAULT', kind='SCALE', axis=-1)


@step
def s_scale():
    check('scale continues the same source node after Undo/Redo', mod('operators.smart_extrude').DRAG._previous is not None)
    typed('.5')


@step
def s_scale_confirm():
    tap('RET')


@step
def s_scaled():
    check('Scale edits the extruded cap rather than doing nothing', volume() < C['extruded_volume']-.01 and volume() > 8)
    C['scaled'] = mod('operators.smart_extrude').signature(bm())
    with override():
        bpy.ops.allset.smart_extrude_drag('INVOKE_DEFAULT', kind='ROTATE', axis=0)


@step
def s_rotate():
    typed('20')


@step
def s_rotate_preview():
    drag = mod('operators.smart_extrude').DRAG
    check('numeric rotation changes the cap with a valid closed mesh', drag is not None and abs(drag.rotation[0]-math.radians(20)) < 1e-6
          and all(e.is_manifold for e in bm().edges))
    with override():
        centre, axes = mod('ui.smart_extrude').widget_frame(bpy.context)
        check('manipulator frame follows live rotation', axes.col[2].dot(Vector((0, 0, 1))) < .99)
    tap('ESC')


@step
def s_cancelled():
    check('Esc restores the previous full geometry and selection', mod('operators.smart_extrude').signature(bm()) == C['scaled'])
    with override():
        bpy.ops.allset.smart_extrude_drag('INVOKE_DEFAULT', kind='TRANSLATE', axis=2)


@step
def s_snap_move():
    ev('MOUSEMOVE', 'NOTHING', x=C['end'][0]+19, y=C['end'][1]+15)
    ev('J', 'PRESS')


@step
def s_snap_check():
    drag = mod('operators.smart_extrude').DRAG
    amount = drag.translation[2]-drag._start['translation'][2]
    check('J pressed during a drag snaps translation to a unit', abs(amount-round(amount)) < 1e-5)
    ev('J', 'RELEASE')
    tap('ESC')


@step
def s_repeat():
    with override():
        bpy.ops.mesh.select_all(action='DESELECT')
        max(bm().faces, key=lambda f: f.calc_center_median().x).select_set(True)
        bmesh.update_edit_mesh(bpy.context.edit_object.data)
        C['repeat_volume'] = volume()
    tap('G')


@step
def s_final():
    check('G repeats Smart Extrude on the new selected face', volume() > C['repeat_volume']+.01)
    check('temporary geometry is cleaned after previews and cancellation', not any(o.name.startswith('.allset_smart') for o in bpy.data.objects)
          and not any(m.name.startswith('.allset_smart') for m in bpy.data.meshes))
    shots = os.environ.get('ALLSET_GUI_SHOTS', '')
    if shots:
        screenshot(os.path.join(shots, 'smart_extrude.png'))


run()
