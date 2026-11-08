"""A picked Channel Box INPUTS channel of a modeling node takes a middle drag in the view (edit mode)."""
import os
import sys
from importlib import import_module

import bpy
import bmesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, view3d, win, tap

C = {}


def mod(name):
    return import_module(MODULE+'.'+name)


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def node():
    return mod('ui.node_attributes').target(bpy.context)


def point():
    _area, region = view3d()
    return region.x+int(region.width*.2), region.y+int(region.height*.2)


def drag(dx, tag, cancel=False, ctrl=False):
    @step
    def begin():
        C[tag] = point()
        ev('MIDDLEMOUSE', 'PRESS', x=C[tag][0], y=C[tag][1], ctrl=ctrl)
    for i in range(1, 5):
        def move(i=i):
            x, y = C[tag]
            ev('MOUSEMOVE', 'NOTHING', x=x+round(dx*i/4), y=y, ctrl=ctrl)
        step(move)
    @step
    def end():
        x, y = C[tag]
        if cancel:
            tap('ESC')
        ev('MIDDLEMOUSE', 'RELEASE', x=x+dx, y=y, ctrl=ctrl)


@step
def start():
    setup()
    with override():
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.scene.tool_settings.mesh_select_mode = (False, True, False)
        bpy.ops.mesh.select_all(action='SELECT')
        # three segments: Depth then shapes the profile, so each Depth value is a different mesh
        bpy.ops.allset.bevel('EXEC_DEFAULT', True, segments=3)
    C['scale'] = bpy.context.preferences.system.ui_scale


@step
def pick_channel():
    C['segments_value'] = node().params['segments']
    with override():
        cb = mod('ui.channel_box')
        cb.select_channel(cb.model_key(node().record, 'depth'), context=bpy.context)


drag(-20, 'channel_drag')

@step
def channel_result():
    check('Channel Box history selection owns the next MMB drag', node().params['depth'] < 1)
    check('history slider leaves other parameters intact', node().params['segments'] == C['segments_value'])
    C['depth_value'] = node().params['depth']


@step
def undo_channel_drag():
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)


@step
def undone():
    check(f"one Undo restores the whole Channel Box drag ({node().params['depth']})", node().params['depth'] == 1)
    check('Undo preserves the previous Segments edit', node().params['segments'] == C['segments_value'])
    ev('Z', 'PRESS', ctrl=True, shift=True)
    ev('Z', 'RELEASE', ctrl=True, shift=True)


@step
def redone():
    check('Redo restores the final drag value', node().params['depth'] == C['depth_value'])


run()
