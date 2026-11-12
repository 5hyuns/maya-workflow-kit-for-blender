"""#359: in the Maya layout, Outliner > Display > Blender Collections shows the scene's collections with Blender's own
rows and header; Maya Outliner in that header brings the Maya Outliner (kit rows, Maya menus) back."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, screenshot, setup, step, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mo():
    return import_module(MODULE + ".ui.maya_outliner")


def tree():
    return import_module(MODULE + ".ui.outliner_tree")


def outliner():
    area = next(a for a in win().screen.areas if a.type == 'OUTLINER')
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, f"gui_issue359_{name}.png"))


def idle():
    pass


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    sc = bpy.context.scene
    props = bpy.data.collections.new("Props")
    sc.collection.children.link(props)
    for name in ("chair", "table"):
        ob = bpy.data.objects.new(name, bpy.data.meshes.new(name))
        props.objects.link(ob)
    area, region = outliner()
    sp = area.spaces.active
    check("the Maya layout's Outliner is a Maya Outliner (kit rows)", mo().is_maya_outliner(sp) and tree().is_tree(sp))
    with bpy.context.temp_override(window=win(), area=area, region=region, space_data=sp):
        C["on"] = bpy.ops.allset.outliner_collections(show=True)
    area.tag_redraw()


step(idle)


@step
def s_on():
    area, _r = outliner()
    sp = area.spaces.active
    check(f"Blender Collections: Blender's rows with the collections ({C['on']})",
          C["on"] == {'FINISHED'} and sp.use_filter_collection and sp.use_filter_object
          and not mo().is_maya_outliner(sp) and mo().is_collection_view(sp))
    shot("collections")
    area2, region = outliner()
    with bpy.context.temp_override(window=win(), area=area2, region=region, space_data=sp):
        C["off"] = bpy.ops.allset.outliner_collections(show=False)
    area2.tag_redraw()


step(idle)


@step
def s_off():
    area, _r = outliner()
    sp = area.spaces.active
    check(f"Maya Outliner brings the kit rows back ({C['off']})",
          C["off"] == {'FINISHED'} and mo().is_maya_outliner(sp) and tree().is_tree(sp))
    shot("maya_outliner")


run()
