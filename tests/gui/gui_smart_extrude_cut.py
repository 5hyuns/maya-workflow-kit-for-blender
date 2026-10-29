"""Long near-axial cut drags, clean exit topology and retaining the last valid preview."""
import os
import sys
from importlib import import_module

import bmesh
import bpy
from mathutils import Euler

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


@step
def s_setup():
    setup()
    with override():
        bpy.ops.object.select_all(action='DESELECT')
        ob = bpy.data.objects['Cube']
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.context.scene.unit_settings.system = 'NONE'
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        bmesh.ops.subdivide_edges(bm(), edges=list(bm().edges), cuts=2, use_grid_fill=True)
        bpy.ops.mesh.select_all(action='DESELECT')
        bm().normal_update()
        face = min((f for f in bm().faces if f.normal.z > .9), key=lambda f: f.calc_center_median().xy.length)
        face.select_set(True)
        bmesh.update_edit_mesh(ob.data)
        bpy.ops.wm.tool_set_by_id(name=mod('operators.smart_extrude').TOOL)
        _area, region = view3d()
        region.data.view_rotation = Euler((.06, 0, 0)).to_quaternion()
        region.data.view_location = (0, 0, 0)
        region.data.view_distance = 4
        C['start'] = (region.x+region.width//2+30, region.y+region.height//2+20)
    ev('MOUSEMOVE', 'NOTHING', x=C['start'][0], y=C['start'][1])


@step
def s_begin():
    with override():
        bpy.ops.allset.smart_extrude_drag('INVOKE_DEFAULT', kind='TRANSLATE', axis=2)


for depth in (.25, .75, 1.5, 1.99, 2.01, 2.5, 3.5):
    @step
    def move(depth=depth):
        drag = mod('operators.smart_extrude').DRAG
        pixels = depth*drag._session.unit/drag._world_per_pixel
        direction = drag._screen_axis
        C['end'] = (round(C['start'][0]-direction.x*pixels), round(C['start'][1]-direction.y*pixels))
        ev('MOUSEMOVE', 'NOTHING', x=C['end'][0], y=C['end'][1])

    @step
    def inspect(depth=depth):
        drag = mod('operators.smart_extrude').DRAG
        actual = -drag.translation[2]
        tolerance = drag._world_per_pixel/drag._session.unit*1.5
        check(f'depth {depth}: near-axial drag stays continuous', abs(actual-depth) < tolerance and actual >= C.get('depth', 0)-1e-6)
        C['depth'] = actual
        check(f'depth {depth}: valid preview cuts without jumping to the source', drag._error is None
              and abs(bm().calc_volume()-(8-4/9*min(actual, 2))) < 1e-4)
        with override():
            centre, _axes = mod('ui.smart_extrude').widget_frame(bpy.context)
            check(f'depth {depth}: handle follows the accepted cap position', abs(centre.z-(1-actual)) < 1e-5)

    if depth == 1.5:
        @step
        def precision_press():
            C['precision_depth'] = mod('operators.smart_extrude').DRAG.translation[2]
            ev('LEFT_SHIFT', 'PRESS', shift=True)

        @step
        def precision_check():
            check('pressing Shift mid-drag does not jump back towards the source',
                  abs(mod('operators.smart_extrude').DRAG.translation[2]-C['precision_depth']) < 1e-6)
            ev('LEFT_SHIFT', 'RELEASE')

        @step
        def precision_released():
            check('releasing precision keeps the current depth',
                  abs(mod('operators.smart_extrude').DRAG.translation[2]-C['precision_depth']) < 1e-6)


@step
def s_release():
    ev('LEFTMOUSE', 'RELEASE', x=C['end'][0], y=C['end'][1])


@step
def s_cut_done():
    check('release keeps the cut-through result', abs(bm().calc_volume()-64/9) < 1e-4)
    check('cut walls have no Boolean triangles', not any(len(f.verts) == 3 for f in bm().faces))
    with override():
        _area, region = view3d()
        region.data.view_rotation = Euler((.7, 0, .4)).to_quaternion()
    shots = os.environ.get('ALLSET_GUI_SHOTS', '')
    if shots:
        screenshot(os.path.join(shots, 'smart_extrude_clean_cut.png'))


@step
def s_invalid_setup():
    with override():
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.mesh.primitive_cube_add(size=2)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
        max(bm().faces, key=lambda f: f.calc_center_median().z).select_set(True)
        bmesh.update_edit_mesh(bpy.context.edit_object.data)
        bpy.ops.allset.smart_extrude_drag('INVOKE_DEFAULT', kind='TRANSLATE', axis=2)


@step
def s_valid_preview():
    drag = mod('operators.smart_extrude').DRAG
    pixels = .5*drag._session.unit/drag._world_per_pixel
    _area, region = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=region.x+round(drag._mouse[0]-drag._screen_axis.x*pixels),
       y=region.y+round(drag._mouse[1]-drag._screen_axis.y*pixels))


@step
def s_invalid_preview():
    C['accepted_volume'] = bm().calc_volume()
    C['accepted_depth'] = mod('operators.smart_extrude').DRAG.translation[2]
    check(f"valid inward preview is visible before rejection test (volume {C['accepted_volume']:.4f}, depth {C['accepted_depth']:.4f})",
          5.5 < C['accepted_volume'] < 6.5)
    drag = mod('operators.smart_extrude').DRAG
    pixels = 3*drag._session.unit/drag._world_per_pixel
    _area, region = view3d()
    # Entire cube would disappear: deliberately invalid output.
    ev('MOUSEMOVE', 'NOTHING', x=region.x+round(drag._mouse[0]-drag._screen_axis.x*pixels),
       y=region.y+round(drag._mouse[1]-drag._screen_axis.y*pixels))


@step
def s_kept_preview():
    drag = mod('operators.smart_extrude').DRAG
    check('invalid depth keeps the last valid mesh', drag._error is not None and abs(bm().calc_volume()-C['accepted_volume']) < 1e-5)
    with override():
        centre, _axes = mod('ui.smart_extrude').widget_frame(bpy.context)
        check('invalid depth keeps the gizmo on the same preview', abs(centre.z-(1+C['accepted_depth'])) < 1e-5)
    tap('RET')


@step
def s_invalid_done():
    check('release after rejection keeps the valid cut instead of restoring the original cube', abs(bm().calc_volume()-C['accepted_volume']) < 1e-5)
    with override():
        _rec, params = mod('operators.smart_extrude').current(bpy.context)
        check('committed parameters match the accepted mesh', abs(params['translation'][2]-C['accepted_depth']) < 1e-5)


run()
