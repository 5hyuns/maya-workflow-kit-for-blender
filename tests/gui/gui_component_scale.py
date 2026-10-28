"""Real Scale handles: flatten, recover, typing, MMB, the option off and undo (Prevent Negative Scale)."""
import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, setup, step, tap, view3d, win, MODULE, screenshot

C = {}


def mod(name):
    return import_module(MODULE+'.'+name)


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def bm():
    return bmesh.from_edit_mesh(bpy.context.edit_object.data)


def coords():
    return [v.co.copy() for v in bm().verts]


def same(a, b):
    return len(a) == len(b) and all((x-y).length < 2e-5 for x, y in zip(a, b))


def move(p, **kwargs):
    ev('MOUSEMOVE', 'NOTHING', x=round(p[0]), y=round(p[1]), **kwargs)


def drag():
    """The typed / scripted guarded scale (``allset.component_scale``) while it runs."""
    return mod('operators.component_scale').DRAG


def handle_drag():
    """The Maya Scale handle drag while it runs (LMB / MMB on an axis handle)."""
    return any(op.bl_idname == 'ALLSET_OT_manip_scale' for op in win().modal_operators)


def factor():
    return mod('operators.manip_scale').LAST.get('factor')


def typed(text):
    for char in text:
        ev('MINUS' if char == '-' else 'PERIOD' if char == '.' else
           {'0':'ZERO', '1':'ONE', '2':'TWO', '5':'FIVE'}[char], 'PRESS', unicode=char)


@step
def s_setup():
    mouse = setup()
    ui = mod('ui.manipulator')
    original = ui.ALLSET_GGT_xform.draw_prepare
    def spy(self, context):
        original(self, context)
        C['group'] = self
    ui.ALLSET_GGT_xform.draw_prepare = spy
    with override():
        ob = bpy.data.objects['Cube']
        bpy.ops.object.select_all(action='DESELECT')
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.context.scene.cursor.location = (0, 0, 0)
        ts = bpy.context.tool_settings
        ts.transform_pivot_point = 'CURSOR'
        ts.use_snap = False
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.mesh.select_all(action='SELECT')
        for v in bm().verts:
            v.co.x += v.co.z*.3
        bmesh.update_edit_mesh(ob.data)
        bpy.context.scene.transform_orientation_slots[3].type = 'GLOBAL'
        bpy.ops.wm.tool_set_by_id(name='builtin.scale')
        region = view3d()[1]
        region.data.view_rotation = Quaternion((1, 0, 0, 0))
        region.data.view_location = (0, 0, 0)
        region.data.view_distance = 9
        C['before'] = coords()
        C['snap'] = mod('operators.hold').GROUPS['snap'].capture(ts)
        bpy.ops.ed.undo_push(message='Scale fixture')
    move(mouse)


@step
def s_wait_tool():
    mod('ui.manipulator').ensure_tools(patched=True)
    view3d()[0].tag_redraw()


@step
def s_wait_draw():
    view3d()[0].tag_redraw()


@step
def s_hover():
    gz = next(g for g, role, axis in C['group'].handles if role == 'AXIS' and axis == 'X')
    area, region = view3d()
    point = gz.matrix_world @ Vector((0, 0, mod('ui.manipulator').CUBE_AT))
    xy = location_3d_to_region_2d(region, region.data, point)
    C['start'] = Vector((round(region.x+xy.x), round(region.y+xy.y)))
    move(C['start'])


@step
def s_press():
    ev('LEFTMOUSE', 'PRESS', x=round(C['start'].x), y=round(C['start'].y))


@step
def s_cross_zero():
    move(C['start']-Vector((8, 0)))


@step
def s_flatten():
    check('real X handle starts the Maya scale drag', handle_drag())
    C['end'] = C['start']-Vector((200, 0))
    move(C['end'])


@step
def s_flat_result():
    check('dragging past zero makes an exact plane', all(abs(v.co.x) < 1e-6 for v in bm().verts))
    check('flatten preserves the other coordinates and topology',
          all(abs(a.y-b.y) < 1e-6 and abs(a.z-b.z) < 1e-6 for a, b in zip(C['before'], coords()))
          and len(bm().verts) == 8 and len(bm().edges) == 12 and len(bm().faces) == 6)
    C['end'].x -= 30
    move(C['end'])


@step
def s_no_flip():
    check('further inward drag stays at zero without reversing', factor() == 0.0
          and all(abs(v.co.x) < 1e-6 for v in bm().verts))
    C['end'] = C['start']-Vector((50, 0))      # back between the zero point and the press: a positive scale again
    move(C['end'])


@step
def s_recover():
    C['free'] = factor()
    check('moving back above zero recovers a positive scale', .01 < C['free'] < .9)
    check('recover uses the original unflattened coordinates',
          same(coords(), [Vector((v.x*C['free'], v.y, v.z)) for v in C['before']]))
    C['after'] = coords()
    ev('LEFTMOUSE', 'RELEASE', x=round(C['end'].x), y=round(C['end'].y))


@step
def s_commit():
    check('release ends the modal and retains the recovered result', not handle_drag() and same(coords(), C['after']))
    check('step snapping preferences are unchanged',
          mod('operators.hold').GROUPS['snap'].capture(bpy.context.tool_settings) == C['snap'])
    with override():
        bpy.ops.ed.undo()


@step
def s_undo():
    check('one Undo restores the mesh before the complete drag', same(coords(), C['before']))
    with override():
        bpy.ops.ed.redo()


@step
def s_redo():
    check('Redo restores the final scale', same(coords(), C['after']))
    with override():
        bpy.ops.allset.component_scale('INVOKE_DEFAULT', constraint_axis=(True, False, False))
    typed('-1')


@step
def s_negative_text():
    check('typed negative value stops at zero', drag().value[0] == 0 and all(abs(v.co.x) < 1e-6 for v in bm().verts))
    tap('ESC')


@step
def s_cancel():
    check('Escape restores the exact pre-drag mesh', drag() is None and same(coords(), C['after']))
    with override():
        bpy.ops.allset.component_scale('INVOKE_DEFAULT', constraint_axis=(True, False, False))
    typed('0')
    tap('RET')


@step
def s_zero_text():
    check('typed zero and Enter commit an exact plane', drag() is None and all(abs(v.co.x) < 1e-6 for v in bm().verts))
    with override():
        bpy.ops.ed.undo()


@step
def s_mmb():
    check('Undo restores the mesh before typed zero', same(coords(), C['after']))
    with override():
        bpy.ops.allset.manip_mmb('INVOKE_DEFAULT', mode='RESIZE')


@step
def s_mmb_move():
    check('MMB remembered axis uses the Maya scale drag', handle_drag())
    area, region = view3d()
    press = mod('operators.manip_scale').LAST['press']
    C['mmb_end'] = Vector((region.x, region.y))+Vector(press)+Vector((-600, 0))
    move(C['mmb_end'])


@step
def s_mmb_release():
    check('MMB also stops exactly at zero', factor() == 0.0)
    ev('MIDDLEMOUSE', 'RELEASE', x=round(C['mmb_end'].x), y=round(C['mmb_end'].y))


@step
def s_mmb_done():
    check('MMB release confirms and clears the modal', not handle_drag())
    with override():
        bpy.ops.ed.undo()
        bpy.ops.allset.prevent_negative_scale()
    check('marking menu state uses the same disabled option',
          mod('marking.draw').checked(('allset.prevent_negative_scale', {})) is False)


@step
def s_disabled_hover():
    s_hover()


@step
def s_disabled_press():
    s_press()


@step
def s_disabled_drag():
    move(C['start']-Vector((200, 0)))


@step
def s_native():
    check('with the option off the drag goes past zero (flips)', handle_drag() and factor() < 0.0)
    tap('ESC')
    ev('LEFTMOUSE', 'RELEASE')


@step
def s_done():
    check('native cancellation keeps the previous result', same(coords(), C['after']))
    with override():
        bpy.ops.allset.prevent_negative_scale()
        bpy.ops.allset.editor_toggle(editor='TOOL_SETTINGS')


@step
def s_screenshot():
    if os.environ.get('ALLSET_GUI_SHOTS'):
        screenshot(os.path.join(os.environ['ALLSET_GUI_SHOTS'], 'component_scale_settings.png'))


run()
