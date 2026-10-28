"""Preserve the inset loops in the screenshot reference and rebuild the interior hole frames."""
import os
import sys

import bmesh
import bpy
from mathutils import Euler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim import check, run, screenshot, setup, step, view3d, win
import smart_reference as reference

C = {}


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def bm():
    return bmesh.from_edit_mesh(bpy.context.edit_object.data)


def select_patch(axis, sign):
    bpy.ops.mesh.select_all(action='DESELECT')
    bm().faces.ensure_lookup_table()
    bm().faces[reference.patch(bm(), axis, sign)].select_set(True)
    bmesh.update_edit_mesh(bpy.context.edit_object.data)


@step
def s_setup():
    setup()
    with override():
        bpy.ops.object.select_all(action='DESELECT')
        ob = bpy.data.objects['Cube']
        for other in list(bpy.context.scene.objects):
            if other is not ob:
                other.hide_set(True)
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.context.scene.unit_settings.system = 'NONE'
        pre = reference.mesh()
        C['edges'] = [(tuple(e.verts[0].co), tuple(e.verts[1].co)) for e in pre.edges]
        pre.to_mesh(ob.data)
        pre.free()
        initial = ob.copy()
        initial.data = ob.data.copy()
        initial.name = 'Reference Input'
        bpy.context.scene.collection.objects.link(initial)
        initial.select_set(False)
        bpy.context.view_layer.objects.active = ob
        initial.location.x = -2
        initial.show_wire = initial.show_all_edges = True
        ob.location.x = 2
        ob.show_wire = ob.show_all_edges = True
        bpy.context.view_layer.update()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        select_patch(2, 1)
        bpy.ops.allset.smart_extrude('EXEC_DEFAULT', True, translation=(0, 0, -3))


@step
def s_second_cut():
    with override():
        check('vertical cut keeps the expected volume', abs(bm().calc_volume()-6) < 1e-5)
        frame = [f for f in bm().faces if f.normal.z > .99 and f.calc_center_median().z > .99]
        check('vertical cut preserves the four original top inset panels', len(frame) == 4)
        intermediate = bpy.data.meshes.new('After Vertical Cut')
        snapshot = bm().copy()
        try:
            snapshot.to_mesh(intermediate)
        finally:
            snapshot.free()
        stage = bpy.data.objects.new('Reference After Vertical', intermediate)
        bpy.context.scene.collection.objects.link(stage)
        stage.hide_set(True)
        stage.hide_render = True
        select_patch(1, -1)
        bpy.ops.allset.smart_extrude('EXEC_DEFAULT', True, translation=(0, 0, -3))
        _area, region = view3d()
        region.data.view_rotation = Euler((1.15, 0, .3)).to_quaternion()
        region.data.view_location = (0, 0, 0)
        region.data.view_distance = 7.5
        region.data.view_perspective = 'ORTHO'
        bpy.ops.mesh.select_all(action='DESELECT')


@step
def s_result():
    check('two cuts have the analytically expected volume', abs(bm().calc_volume()-2.48) < 1e-4)
    check('result is manifold with consistent winding', all(e.is_manifold and e.is_contiguous for e in bm().edges))
    check('all starting inset and outer edges survive', all(reference.covered(bm(), p, q) for p, q in C['edges']))
    for z in (-.8, .8):
        bands = [f for f in bm().faces if all(abs(v.co.z-z) < 1e-5 for v in f.verts)]
        check(f'interior frame at z={z} has four panels', len(bands) == 4)
        check(f'interior frame at z={z} joins matching corners', all(reference.covered(bm(), (.8*x, y, z), (.5*x, .5*y, z))
              for x in (-1, 1) for y in (-1, 1)))
    check('reference has no solver triangles', not any(len(f.verts) == 3 for f in bm().faces))
    with override():
        bpy.ops.ed.undo()


@step
def s_undo():
    check('Undo of the second cut restores the vertical tunnel', abs(bm().calc_volume()-6) < 1e-5)
    top = [f for f in bm().faces if f.normal.z > .99 and f.calc_center_median().z > .99]
    check('Undo preserves the original inset panels', len(top) == 4)
    with override():
        bpy.ops.ed.redo()


@step
def s_redo():
    check('Redo restores the intersecting cuts', abs(bm().calc_volume()-2.48) < 1e-4)
    check('Redo keeps source edge lineage', all(reference.covered(bm(), p, q) for p, q in C['edges']))
    with override():
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.object.name = 'Reference Result'
    shots = os.environ.get('ALLSET_GUI_SHOTS', '')
    if shots:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(shots, 'smart_extrude_reference.blend'))


@step
def s_screenshot():
    shots = os.environ.get('ALLSET_GUI_SHOTS', '')
    if shots:
        screenshot(os.path.join(shots, 'smart_extrude_reference.png'))


run()
