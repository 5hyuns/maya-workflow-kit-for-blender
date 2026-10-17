"""Step 67 in a real UI ( render_01-05): sphere -> Windows > Rendering Editors >
Hypershade -> a Shader Editor window on its "Hypershade" sidebar tab -> Create Standard Surface -> Assign Material To
Selection -> AE Base Color map button > File -> Render > Render Current Frame -> Keep Image -> render again -> two
slots used; Windows > Rendering Editors > Light Editor -> a window on its "Light Editor" tab (screenshots)."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, run, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("MAYA_KIT_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(sys.modules["sim"].MODULE + name)


def shot(name, window=None):
    if SHOTS:
        with bpy.context.temp_override(window=window or win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, name))


def redraw_all():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def window_with(ui_type):
    for w in bpy.context.window_manager.windows[1:]:
        for a in w.screen.areas:
            if a.ui_type == ui_type:
                return w, a
    return None, None


def run_menu(path):
    area, region = view3d()
    modal = mod(".marking.modal")
    menu_map = mod(".ui.menu_map")
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return modal.run_action(bpy.context, menu_map.MAP[path])


def wait(fn, cond, limit=40):
    """Run ``fn`` again next tick until ``cond()`` or ``limit`` ticks."""
    C.setdefault(fn.__name__, 0)
    if not cond() and C[fn.__name__] < limit:
        C[fn.__name__] += 1
        sys.modules["sim"]._steps.insert(0, fn)
        return True
    return False


@step
def s_setup():
    C["x"], C["y"] = setup()
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'          # fast: the render path, not the look, is checked
    sc.render.resolution_percentage = 50
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.maya_kit.create(kind='SPHERE')
    C["sphere"] = bpy.context.active_object.name
    C["open"] = run_menu("Windows/Rendering Editors/Hypershade")


@step
def s_hypershade_open():
    w, a = window_with('ShaderNodeTree')
    if w is None and wait(s_hypershade_open, lambda: window_with('ShaderNodeTree')[0] is not None):
        return
    ui = next((r for r in a.regions if r.type == 'UI'), None) if a else None
    if ui is not None and wait(s_hypershade_open, lambda: ui.active_panel_category == "Hypershade"):
        redraw_all()
        return
    check(f"Windows > Rendering Editors > Hypershade: a Shader Editor window, sidebar on the Hypershade tab "
          f"(got {C['open']}, {a is not None}, {ui.active_panel_category if ui else None})",
          a is not None and ui.active_panel_category == "Hypershade" and a.spaces.active.show_region_ui)
    C["hs"] = (w, a)
    # Create > Standard Surface, then Assign Material To Selection (the panel buttons' operators)
    with bpy.context.temp_override(window=w, area=a, region=ui, space_data=a.spaces.active):
        bpy.ops.maya_kit.hs_create(kind='STANDARD_SURFACE')
    mat = bpy.data.materials.get("standardSurface1")
    sphere = bpy.data.objects[C["sphere"]]
    check(f"Create > Standard Surface: standardSurface1, not assigned yet, graph pinned to it "
          f"({mat is not None}, {len(sphere.material_slots)}, {a.spaces.active.pin})",
          mat is not None and not sphere.material_slots and a.spaces.active.pin
          and a.spaces.active.node_tree == mat.node_tree)
    with bpy.context.temp_override(window=w, area=a, region=ui):
        bpy.ops.maya_kit.assign_material(material="standardSurface1")
    redraw_all()


@step
def s_assigned():
    sphere = bpy.data.objects[C["sphere"]]
    check(f"Assign Material To Selection: {sphere.name} slot 0 = standardSurface1",
          sphere.material_slots and sphere.material_slots[0].material.name == "standardSurface1")
    w, a = C["hs"]
    # pick it in the browser: the graph follows the object again (unpinned)
    ui = next(r for r in a.regions if r.type == 'UI')
    with bpy.context.temp_override(window=w, area=a, region=ui, space_data=a.spaces.active):
        bpy.ops.maya_kit.hs_pick(material="standardSurface1")
    # AE Base Color map button > File
    bpy.ops.maya_kit.ae_map_connect(material="standardSurface1", socket="Base Color", kind='FILE')
    redraw_all()


@step
def s_mapped():
    w, a = C["hs"]
    mat = bpy.data.materials["standardSurface1"]
    inp = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs["Base Color"]
    check(f"AE Base Color map > File: Image Texture linked to Base Color, graph unpinned "
          f"({inp.is_linked and inp.links[0].from_node.type}, pin {a.spaces.active.pin})",
          inp.is_linked and inp.links[0].from_node.type == 'TEX_IMAGE' and not a.spaces.active.pin)
    redraw_all()


@step
def s_shot_hypershade():
    w, _a = C["hs"]
    shot("gui_step67_hypershade.png", w)
    C["render"] = run_menu("Render/Render Current Frame")


@step
def s_rendered():
    if wait(s_rendered, lambda: not bpy.app.is_job_running('RENDER') and window_with('IMAGE_EDITOR')[0] is not None):
        return
    rv = mod(".ui.render_view")
    image = rv.render_result()
    w, a = window_with('IMAGE_EDITOR')
    check(f"Render > Render Current Frame: Render Result in a Render View window (got {C['render']}, "
          f"{image is not None}, {a is not None})", image is not None and a is not None)
    C["rv"] = (w, a)
    image[rv.KEPT_PROP] = []
    image.render_slots.active_index = 0
    redraw_all()


@step
def s_keep():
    w, a = C["rv"]
    shot("gui_step67_render_view.png", w)
    header = next(r for r in a.regions if r.type == 'HEADER')
    with bpy.context.temp_override(window=w, area=a, region=header, space_data=a.spaces.active):
        bpy.ops.maya_kit.render_keep_image()
    C["slot_after_keep"] = mod(".ui.render_view").render_result().render_slots.active_index
    C["render2"] = run_menu("Render/Render Current Frame")


@step
def s_rendered_again():
    if wait(s_rendered_again, lambda: not bpy.app.is_job_running('RENDER')):
        return
    rv = mod(".ui.render_view")
    image = rv.render_result()
    slots = image.render_slots
    check(f"Keep Image -> render again: slot 1 kept, the new render in slot 2 "
          f"(kept {sorted(rv.kept(image))}, active {slots.active_index}, after keep {C['slot_after_keep']})",
          rv.kept(image) == {0} and slots.active_index == 1 and C["slot_after_keep"] == 1)
    redraw_all()


@step
def s_light():
    w, _a = C["rv"]
    shot("gui_step67_keep_image.png", w)
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.maya_kit.create(kind='POINT_LIGHT')
        bpy.ops.maya_kit.create(kind='DIRECTIONAL_LIGHT')
    C["le"] = run_menu("Windows/Rendering Editors/Light Editor")
    C["nwin"] = len(bpy.context.window_manager.windows)


@step
def s_light_open():
    w = bpy.context.window_manager.windows[-1]
    a = w.screen.areas[0]
    ui = next((r for r in a.regions if r.type == 'UI'), None)
    if wait(s_light_open, lambda: ui is not None and ui.active_panel_category == "Light Editor"):
        redraw_all()
        return
    le = mod(".ui.light_editor")
    with bpy.context.temp_override(window=w, area=a, region=ui):
        marked = le.is_light_editor(bpy.context)
    check(f"Windows > Rendering Editors > Light Editor: a 3D View window on the Light Editor tab "
          f"(got {C['le']}, {a.type}, {ui.active_panel_category if ui else None}, marked {marked})",
          a.type == 'VIEW_3D' and ui is not None and ui.active_panel_category == "Light Editor" and marked)
    C["lew"] = w
    with bpy.context.temp_override(window=w, area=a, region=ui):
        bpy.ops.maya_kit.light_select(light="pointLight1")
        bpy.ops.maya_kit.light_isolate(light="pointLight1")
    sun = bpy.context.scene.objects["directionalLight1"]
    check(f"Light Editor: pick pointLight1 + Isolate -> directionalLight1 off ({sun.hide_render})",
          sun.hide_render and bpy.context.active_object.name == "pointLight1")
    redraw_all()


@step
def s_end():
    shot("gui_step67_light_editor.png", C["lew"])
    with bpy.context.temp_override(window=C["lew"]):
        bpy.ops.maya_kit.light_isolate(light="pointLight1")
    check("Isolate again: directionalLight1 back on", not bpy.context.scene.objects["directionalLight1"].hide_render)


run()
