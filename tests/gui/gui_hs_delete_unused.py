"""Hypershade Edit > Delete Unused Nodes (#251): a Shader Editor pinned to an unassigned material, then Delete Unused
Nodes / Delete All Materials -> the editors keep drawing (no crash), the pinned editors let go of the deleted trees,
assigned materials and lambert1 stay, a material held only by a deleted object's leftover data is unused too."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, run, setup, step, win  # noqa: E402

C = {}


def mod(name):
    return import_module(MODULE + name)


def redraw():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def node_area():
    return next(a for a in win().screen.areas if a.type == 'NODE_EDITOR')


@step
def s_setup():
    setup()
    # two Shader Editors: one pinned to the unassigned material, one following the active object
    areas = sorted((a for a in win().screen.areas if a.type not in {'VIEW_3D', 'TOPBAR', 'STATUSBAR'}),
                   key=lambda a: -a.width * a.height)
    areas[0].ui_type = 'ShaderNodeTree'
    if len(areas) > 1:
        areas[1].ui_type = 'ShaderNodeTree'


@step
def s_scene():
    m = mod(".operators.material")
    m.default_material()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    used = bpy.data.materials.new("usedBlinn")
    used.use_nodes = True
    used.use_fake_user = True
    cube.data.materials.append(used)
    free = bpy.data.materials.new("anisotropic1")
    free.use_nodes = True
    free.use_fake_user = True
    # a deleted object's mesh data lingers with its material until a purge: still unused for Maya
    bpy.ops.mesh.primitive_plane_add()
    gone = bpy.context.active_object
    left = bpy.data.materials.new("leftover1")
    left.use_nodes = True
    gone.data.materials.append(left)
    bpy.data.objects.remove(gone)
    cube.select_set(True)
    bpy.context.view_layer.objects.active = cube
    hs = mod(".ui.hypershade")
    spaces = [a.spaces.active for a in win().screen.areas if a.type == 'NODE_EDITOR']
    with bpy.context.temp_override(window=win()):
        hs.show(bpy.context, free, spaces[0])
    C["spaces"] = len(spaces)
    check("the first Shader Editor is pinned to the unassigned material",
          spaces[0].pin and spaces[0].node_tree == free.node_tree)
    redraw()


@step
def s_delete_unused():
    area = node_area()
    region = next(r for r in area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.hs_edit(action='DELETE_UNUSED')
    redraw()


@step
def s_after_unused():
    names = {m.name for m in bpy.data.materials}
    check("the unassigned material is gone", "anisotropic1" not in names)
    check("a material only a deleted object's data held is gone", "leftover1" not in names)
    check("the assigned material stays", "usedBlinn" in names)
    check("lambert1 stays", "lambert1" in names)
    space = node_area().spaces.active
    check("the pinned editor no longer shows a deleted tree",
          space.node_tree is None or space.node_tree.users >= 0 and space.node_tree.name not in ("anisotropic1",))
    hs = mod(".ui.hypershade")
    with bpy.context.temp_override(window=win()):
        hs.show(bpy.context, bpy.data.materials["usedBlinn"], node_area().spaces.active)
    redraw()


@step
def s_delete_all():
    area = node_area()
    region = next(r for r in area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.hs_edit(action='DELETE_MATERIALS')
    redraw()


@step
def s_after_all():
    names = {m.name for m in bpy.data.materials if not m.is_grease_pencil}
    check("Delete All Materials leaves lambert1 only", names == {"lambert1"})
    redraw()


@step
def s_draw_more():
    # a few more redraws: the crash came while the editors drew after the delete
    redraw()


@step
def s_alive():
    check("Blender still draws after the deletes", True)


run()
