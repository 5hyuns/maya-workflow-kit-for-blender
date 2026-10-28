"""Vertical then horizontal tunnel: one concave ngon per joined interior wall."""
import os
import sys
from importlib import import_module

import bmesh
import bpy
from mathutils import Euler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, run, screenshot, setup, step, view3d, win


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def bm():
    return bmesh.from_edit_mesh(bpy.context.edit_object.data)


def patch(normal):
    bpy.ops.mesh.select_all(action='DESELECT')
    face = max(bm().faces, key=lambda f: f.calc_center_median()[normal])
    bmesh.ops.inset_region(bm(), faces=[face], thickness=.5, depth=0, use_even_offset=True)
    bm().normal_update()
    faces = [f for f in bm().faces if f.normal[normal] > .99 and f.calc_center_median()[normal] > .99]
    face = min(faces, key=lambda f: sum(f.calc_center_median()[i]**2 for i in range(3) if i != normal))
    face.select_set(True)
    bmesh.update_edit_mesh(bpy.context.edit_object.data)


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
        patch(2)
        bpy.ops.allset.smart_extrude(translation=(0, 0, -3))


@step
def s_second_cut():
    with override():
        check('first tunnel removes the expected volume', abs(bm().calc_volume()-6) < 1e-5)
        patch(0)
        bpy.ops.allset.smart_extrude(translation=(0, 0, -3))
        area, region = view3d()
        region.data.view_rotation = Euler((.95, 0, .7)).to_quaternion()
        region.data.view_location = (0, 0, 0)
        region.data.view_distance = 6
        bpy.ops.mesh.select_all(action='DESELECT')


@step
def s_result():
    check('intersecting tunnels retain the exact solid volume', abs(bm().calc_volume()-5) < 1e-5)
    check('intersecting tunnels remain closed and consistently wound', all(e.is_manifold and e.is_contiguous for e in bm().edges))
    for y in (-.5, .5):
        faces = [f for f in bm().faces if abs(abs(f.normal.y)-1) < 1e-5
                 and all(abs(v.co.y-y) < 1e-5 for v in f.verts)]
        check(f'joined wall at y={y} is one 12-corner ngon', len(faces) == 1 and len(faces[0].verts) >= 12)
    check('no triangles remain in the intersecting cut fixture', not any(len(f.verts) == 3 for f in bm().faces))
    shots = os.environ.get('ALLSET_GUI_SHOTS', '')
    if shots:
        screenshot(os.path.join(shots, 'smart_extrude_cross_clean.png'))


run()
