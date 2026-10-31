"""Single-axis guard in custom/normal frames, near-axial views, and MMB dispatch."""
import math
import os
import sys
from importlib import import_module

import bmesh
import bpy
from mathutils import Euler, Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, tap, view3d, win

C = {}


def mod(name):
    return import_module(MODULE+'.'+name)


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def bm():
    return bmesh.from_edit_mesh(bpy.context.edit_object.data)


def drag():
    return mod('operators.component_scale').DRAG


@step
def s_setup():
    mouse = setup()
    with override():
        bpy.ops.object.select_all(action='DESELECT')
        ob = bpy.data.objects['Cube']
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.context.tool_settings.use_snap = False
        bpy.context.tool_settings.transform_pivot_point = 'CURSOR'
        bpy.context.scene.cursor.location = (.3, -.1, .2)
        bpy.ops.wm.tool_set_by_id(name='builtin.scale')
        region = view3d()[1]
        region.data.view_location = (0, 0, 0)
        region.data.view_distance = 9
        C['before'] = [v.co.copy() for v in bm().verts]
    ev('MOUSEMOVE', 'NOTHING', x=mouse[0], y=mouse[1])


for axis, orientation, near in ((1, 'GLOBAL', False), (2, 'GLOBAL', False), (0, 'NORMAL', False),
                                (1, 'CUSTOM', False), (0, 'GLOBAL', True)):
    name = f'{"XYZ"[axis]} {orientation}' + (' near-axial' if near else '')

    @step
    def start(axis=axis, orientation=orientation, near=near, name=name):
        with override():
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.mesh.select_all(action='SELECT')
            if orientation == 'NORMAL':
                bpy.ops.mesh.select_mode(type='FACE')
                bpy.ops.mesh.select_all(action='DESELECT')
                max(bm().faces, key=lambda f: f.normal.z).select_set(True)
                bmesh.update_edit_mesh(bpy.context.edit_object.data)
            region = view3d()[1]
            region.data.view_rotation = (Quaternion((0, 1, 0), math.pi/2-.001) if near
                                         else Euler((.6, .2, .4)).to_quaternion())
            frame = None
            if orientation == 'CUSTOM':
                bpy.ops.transform.create_orientation(name='Scale reference', use=True, use_view=True, overwrite=True)
                slot = bpy.context.scene.transform_orientation_slots[3]
                slot.type = 'Scale reference'
                frame = Euler((.2, .4, .8)).to_matrix()
                slot.custom_orientation.matrix = frame
                otype = 'Scale reference'
            else:
                otype = orientation
                bpy.context.scene.transform_orientation_slots[3].type = otype
            C['frame'] = (frame or mod('ui.manipulator').axes_of(bpy.context, otype, region.data)).copy()
            C['centre'] = bpy.context.scene.cursor.location.copy()
            bpy.ops.allset.component_scale('INVOKE_DEFAULT',
                                          constraint_axis=tuple(i == axis for i in range(3)), orient_type=otype)
        check(name+' starts in the requested frame', drag() is not None and
              all((drag()._frame.col[i]-C['frame'].col[i]).length < 1e-5 for i in range(3)))
        kind, remembered = mod('operators.manip').handle_from_op('ALLSET_OT_component_scale', drag())
        check(name+' serializes the effective frame for the next MMB drag', kind == 'RESIZE' and
              all((remembered['orient_matrix'].col[i]-C['frame'].col[i]).length < 1e-5 for i in range(3)))
        C['mouse'] = drag()._mouse.copy()

    @step
    def collapse(axis=axis):
        region = view3d()[1]
        C['end'] = Vector((region.x, region.y))+C['mouse']-drag()._direction*(3/drag()._sensitivity)
        ev('MOUSEMOVE', 'NOTHING', x=round(C['end'].x), y=round(C['end'].y))

    @step
    def flat(axis=axis, name=name):
        check(name+' stops on the pivot plane', all(abs((v.co-C['centre']).dot(C['frame'].col[axis])) < 2e-5 for v in bm().verts if v.select))
        check(name+' retains the captured frame at zero', all((drag()._frame.col[i]-C['frame'].col[i]).length < 1e-5 for i in range(3)))
        tap('ESC')

    @step
    def restored(name=name):
        check(name+' cancellation restores all vertices',
              drag() is None and all((v.co-p).length < 1e-6 for v, p in zip(bm().verts, C['before'])))


@step
def s_auto_start():
    with override():
        region = view3d()[1]
        region.data.view_rotation = Quaternion((1, 0, 0, 0))
        bpy.context.scene.transform_orientation_slots[3].type = 'GLOBAL'
        bpy.ops.allset.manip_mmb_auto('INVOKE_DEFAULT', mode='RESIZE')
    C['start'] = Vector((region.x+region.width//2, region.y+region.height//2))
    ev('MOUSEMOVE', 'NOTHING', x=round(C['start'].x+40), y=round(C['start'].y))


@step
def s_auto_active():
    check('automatic MMB direction starts guarded X scale', drag() is not None and drag()._axis == 0)
    tap('ESC')


for axes, label in (((True, True, False), 'plane'), ((False, False, False), 'uniform')):
    @step
    def native_start(axes=axes, label=label):
        with override():
            mod('operators.component_scale').start(bpy.context, dict(constraint_axis=axes, release_confirm=True))

    @step
    def native_active(label=label):
        check(label+' scale keeps Blender native behavior', drag() is None and
              any(op.bl_idname == 'TRANSFORM_OT_resize' for op in win().modal_operators))
        tap('ESC')


@step
def s_j_before():
    C['snap'] = mod('operators.hold').GROUPS['snap'].capture(bpy.context.tool_settings)
    ev('J', 'PRESS')


@step
def s_j_invoke():
    with override():
        bpy.ops.allset.component_scale('INVOKE_DEFAULT', constraint_axis=(True, False, False))
    check('J held before the gesture is recognized', drag()._step_held)
    ev('J', 'RELEASE')


@step
def s_j_released():
    check('releasing pre-held J switches to free scaling while modal stays active',
          drag() is not None and not drag()._step_held)
    tap('ESC')


@step
def s_j_restored():
    check('pre-held J restores snap preferences after cancellation', drag() is None and
          mod('operators.hold').GROUPS['snap'].capture(bpy.context.tool_settings) == C['snap'])


run()
