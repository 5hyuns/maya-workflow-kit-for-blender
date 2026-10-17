"""Step 68 in a real UI, MayaKit layout (1 unit = 1 cm;  fx_01-02): F5 -> nParticles >
Create Emitter -> Alt+V plays -> after one second the oldest particles fell ~4.9 units like in Maya -> ground plane
Create Passive Collider + a 1 unit plane two units up nCloth > Create nCloth -> two seconds -> the cloth lies on the
ground (Blender's 0.015 m collision distance would keep it 1.5 units up) -> AE nucleus1 tab (screenshots)."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("MAYA_KIT_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(MODULE + name)


def shot(name):
    if SHOTS:
        with bpy.context.temp_override(window=win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, name))


def run_menu(path):
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return mod(".marking.modal").run_action(bpy.context, mod(".ui.menu_map").MAP[path])


def in_view(fn):
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return fn()


def k():
    return mod(".operators.units").maya_unit()


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_setup():
    setup()
    check("install layout", bpy.ops.maya_kit.layout_install() == {'FINISHED'})
    bpy.ops.wm.read_homefile(app_template="MayaKit")


@step
def s_loaded():
    bpy.ops.maya_kit.keymap_activate()
    check(f"MayaKit layout: 1 unit = 0.01 BU ({k():.4f})", abs(k() - 0.01) < 1e-6)
    _a, r = view3d()
    C["mid"] = (r.x + r.width // 2, r.y + r.height // 2)
    ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0], y=C["mid"][1])
    ev('F5', 'PRESS', x=C["mid"][0], y=C["mid"][1])
    ev('F5', 'RELEASE', x=C["mid"][0], y=C["mid"][1])


@step
def s_fx_menus():
    prefs = bpy.context.preferences.addons[MODULE].preferences
    check(f"F5 = FX menu set (got {prefs.menu_set})", prefs.menu_set == 'dynamicsMenuSet')
    sc = bpy.context.scene
    sc.frame_set(sc.frame_start)
    C["emit"] = run_menu("nParticles/Create Emitter")
    ob = bpy.data.objects.get("emitter1")
    nuc = sc.maya_kit_nucleus
    check(f"nParticles > Create Emitter: emitter1 + nParticle1 at the origin, nucleus gravity 9.8 x 0.01 "
          f"(got {C['emit']}, {ob is not None}, {sc.gravity.z:.4f})",
          ob is not None and ob.particle_systems[0].name == "nParticle1" and nuc.exists
          and abs(sc.gravity.z + 0.098) < 1e-5)
    ev('V', 'PRESS', alt=True, x=C["mid"][0], y=C["mid"][1])        # Maya Alt+V = play
    ev('V', 'RELEASE', alt=True, x=C["mid"][0], y=C["mid"][1])


@step
def s_playing():
    sc = bpy.context.scene
    playing = bpy.context.screen.is_animation_playing
    if sc.frame_current < sc.frame_start + 24 and C.setdefault("waits", 0) < 60:
        C["waits"] += 1
        sys.modules["sim"]._steps.insert(0, s_playing)
        return
    if playing:
        in_view(lambda: bpy.ops.screen.animation_cancel(restore_frame=False))
    sc.frame_set(sc.frame_start + 24)           # exactly one second (playback may have run past it)
    ob = bpy.data.objects["emitter1"]
    psys = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).particle_systems[0]
    zs = [p.location.z / k() for p in psys.particles if p.alive_state == 'ALIVE']
    low = min(zs) if zs else 0.0
    check(f"Alt+V plays; after one second the oldest particles fell like in Maya (~4.9 units; got {low:.2f} units, "
          f"{len(zs)} particles, was playing {playing})", zs and -6.5 < low < -3.5)
    redraw()


@step
def s_shot_particles():
    shot("gui_step68_particles.png")
    sc = bpy.context.scene
    sc.frame_set(sc.frame_start)
    in_view(lambda: bpy.ops.maya_kit.create(kind='PLANE'))
    ground = bpy.context.active_object
    ground.scale = (10, 10, 10)
    C["passive"] = run_menu("nCloth/Create Passive Collider")
    in_view(lambda: bpy.ops.maya_kit.create(kind='PLANE'))
    cloth = bpy.context.active_object
    cloth.location.z = 2 * k()
    C["cloth"] = cloth.name
    C["ncloth"] = run_menu("nCloth/Create nCloth")
    md = next((m for m in cloth.modifiers if m.type == 'CLOTH'), None)
    check(f"Create Passive Collider on {ground.name} + Create nCloth on {cloth.name} "
          f"(got {C['passive']}, {C['ncloth']}, {md.name if md else None})",
          any(m.type == 'COLLISION' for m in ground.modifiers) and md is not None)


@step
def s_cloth():
    sc = bpy.context.scene
    for f in range(sc.frame_start, sc.frame_start + 49):
        sc.frame_set(f)
    cloth = bpy.data.objects[C["cloth"]]
    me = cloth.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    zs = [(cloth.matrix_world @ v.co).z / k() for v in me.vertices]
    cloth.to_mesh_clear()
    check(f"two seconds: the 1 unit nCloth lies on the ground, not 1.5 units above (z {min(zs):.2f} .. {max(zs):.2f})",
          -0.3 < min(zs) and max(zs) < 0.5)
    bpy.context.window_manager.maya_kit_dock = 'ATTRIBUTE_EDITOR'
    mod(".ui.attribute_editor").set_tab(bpy.context, "NUC")
    area, _r = view3d()
    area.spaces.active.show_region_ui = True
    redraw()


@step
def s_shot_cloth():
    shot("gui_step68_ncloth.png")
    tabs = mod(".ui.attribute_editor").tabs(bpy.data.objects[C["cloth"]])
    check("AE has the nucleus1 tab for the nCloth", ("NUC", "nucleus1", "nucleus") in tabs)


run()
