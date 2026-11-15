"""Grid Behind Surfaces (ui/maya_grid.py depth pass) in a real viewport: on by default, like Maya (a Material Preview
view builds one batch per visible mesh); turned off and on again, a frame change keeps the static meshes' batches and
makes only the deforming one again, a move keeps the batch, and a frame step costs about what it costs with the pass
off."""

import os
import sys
import time
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, setup, step, view3d, win  # noqa: E402

GUI_TIMEOUT = 240
SPHERES = 150
C = {}


def grid():
    return import_module(MODULE + ".ui.maya_grid")


def prefs():
    return import_module(MODULE + ".preferences").get()


def redraw(n=1):
    for _ in range(n):
        bpy.ops.wm.redraw_timer(type='DRAW_WIN', iterations=1)


def frame_steps(n=8):
    scene = bpy.context.scene
    t0 = time.perf_counter()
    for i in range(n):
        scene.frame_set(scene.frame_current + 1)
        redraw()
    return (time.perf_counter() - t0) / n * 1000.0


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        for i in range(SPHERES):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.4,
                                                 location=((i % 15) - 7, (i // 15) - 5, 0))
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 3))
        cube = bpy.context.active_object
        cube.name = "bend"
        md = cube.modifiers.new("twist", 'SIMPLE_DEFORM')
        md.deform_method = 'TWIST'
        cube.keyframe_insert("rotation_euler", frame=1)           # object animation: a transform only
        md.angle = 0.0
        md.keyframe_insert("angle", frame=1)
        md.angle = 3.0
        md.keyframe_insert("angle", frame=40)                     # a deforming mesh
    area.spaces.active.shading.type = 'MATERIAL'
    bpy.context.scene.frame_set(1)
    redraw(2)


@step
def s_on_by_default():
    check("Grid Behind Surfaces is on after install", prefs().grid_depth_pass is True)
    n = len(grid()._depth_batches)
    check(f"on by default: one batch per visible mesh ({n}, {SPHERES + 1} meshes)", n == SPHERES + 1)
    prefs().grid_depth_pass = False
    grid()._depth_batches.clear()
    redraw(2)


@step
def s_off():
    check(f"off: no depth batches built ({len(grid()._depth_batches)})", not grid()._depth_batches)
    C["off_ms"] = frame_steps()


@step
def s_on():
    prefs().grid_depth_pass = True
    redraw(2)
    n = len(grid()._depth_batches)
    check(f"on: one batch per visible mesh ({n}, {SPHERES + 1} meshes)", n == SPHERES + 1)
    C["kept"] = {uid: hit[1] for uid, hit in grid()._depth_batches.items()}
    C["bend"] = bpy.data.objects["bend"].session_uid


@step
def s_frame():
    bpy.context.scene.frame_set(bpy.context.scene.frame_current + 3)
    redraw()
    now = grid()._depth_batches
    same = sum(1 for uid, b in C["kept"].items() if uid in now and now[uid][1] is b)
    check(f"a frame change keeps every static mesh's batch ({same} of {SPHERES})", same == SPHERES)
    check("the deforming mesh's batch is made again", now[C["bend"]][1] is not C["kept"][C["bend"]])
    sphere = next(o for o in bpy.data.objects if o.name.startswith("Sphere"))
    C["moved"] = sphere.session_uid
    C["moved_batch"] = now[sphere.session_uid][1]
    sphere.location.z += 1.0
    redraw()


@step
def s_moved():
    now = grid()._depth_batches
    check("a move keeps the batch (drawn with the live matrix)", now[C["moved"]][1] is C["moved_batch"])
    on_ms = frame_steps()
    print(f"GRID_DEPTH frame step: off {C['off_ms']:.1f} ms, on {on_ms:.1f} ms", flush=True)
    check(f"on: a frame step costs about the same as off ({on_ms:.1f} vs {C['off_ms']:.1f} ms)",
          on_ms < C["off_ms"] * 1.5 + 5.0)


run()
