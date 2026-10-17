"""Generate the Maya layout app template's startup.blend (headless).

    python tools/make_startup.py          # re-runs itself in `blender -b --factory-startup`

Writes src/maya_kit/app_template/MayaKit/startup.blend. Layout and reasons:
docs/steps/step_5.md 「계획」 (research/maya/ui_layout.md §2 General layout).
Areas are split with screen operators under a window/screen override; in
background mode new areas report width 0 until the file is loaded in a UI,
where Blender lays them out from the saved split proportions.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "maya_kit" / "app_template" / "MayaKit" / "startup.blend"

# Maya Outliner 259 px of 2556 (ui_layout.md:121) ~ 10%; Blender rows need more (icons, larger font):
# 0.16 cut "pCube1" to "pCube" (step 23 audit), 0.2 ~ 264 px at 1600x900 (step 31, delegated).
OUTLINER_FACTOR = 0.2
MAYA_LENS = 35.0          # persp focal length 35 (concepts.md §15)
MAYA_FRAME_END = 120      # playback 1-120 (concepts.md §12, PREF:469-470)
MAYA_RANGE_END = 200      # animation range 1-200 (PREF:471-472; step 20: Range Slider outer fields)
STRIP_FACTOR = 0.91       # top 9% of the factory 3D View ~ 67 px at 1600x900 = header + tool header
                          # (measured, docs/steps/step_12.md 「계획」 1)
STRIP_MARKER = ".MayaKitStrip"  # = ui/shelf.py MARKER
# Maya lengths are cm (decision 8): 1 Maya unit = 0.01 BU with decision 1's m + cm display.
MAYA_UNIT = 0.01
MAYA_CLIP = (0.1, 10000.0)        # cm, research/maya/defaults.json:45-46 (= operators/units.py CLIP)
MAYA_PERSP_EYE = (28.0, -28.0, 21.0)  # cm, Maya persp (28, 21, 28) Y-up [K] (= units.PERSP_EYE)


def run_outside_blender():
    import subprocess
    sys.path.insert(0, str(ROOT / "tools"))
    import build
    r = subprocess.run([os.environ.get("BLENDER", build.DEFAULT_BLENDER), "-b", "--factory-startup",
                        "--python-exit-code", "1", "--python", __file__],
                       env=build.sandbox_env(), stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in r.stdout.splitlines():
        if line.startswith("make_startup"):
            print(line)
    if r.returncode:
        sys.stderr.write(r.stdout[-3000:] + r.stderr[-3000:])
    return r.returncode


def build_layout():
    import bpy

    ctx = bpy.context
    win = ctx.window_manager.windows[0]
    ws = bpy.data.workspaces["Layout"]
    scr = ws.screens[0]
    assert win.screen == scr, "factory startup should open the Layout workspace"

    def window_region(area):
        return next(r for r in area.regions if r.type == 'WINDOW')

    def split(area, direction, factor):
        before = {a.as_pointer() for a in scr.areas}
        with ctx.temp_override(window=win, screen=scr, area=area, region=window_region(area)):
            assert bpy.ops.screen.area_split(direction=direction, factor=factor) == {'FINISHED'}
        return next(a for a in scr.areas if a.as_pointer() not in before)

    def only(area_type):
        found = [a for a in scr.areas if a.type == area_type]
        assert len(found) == 1, (area_type, len(found))
        return found[0]

    view3d = only('VIEW_3D')
    # Maya strip (step 12): Status Line + Shelf under the menu bar, over Outliner and
    # viewport. Split before the Outliner so it spans both; the new area is the top part.
    strip = split(view3d, 'HORIZONTAL', STRIP_FACTOR)
    strip.type = 'IMAGE_EDITOR'
    # Right column = factory split: Outliner on top (~32%), Properties below (~68%).
    # Top becomes the Layer Editor, bottom stays Properties (Attribute Editor,
    # Object tab). Rearranging it is not possible headless: screen.area_close
    # hangs in background mode, area_move has no effect there, and a
    # Properties space converted from another editor has no tab list.
    layer_editor = only('OUTLINER')
    attribute_editor = only('PROPERTIES')
    attribute_editor.spaces.active.context = 'OBJECT'

    # Left: Outliner next to the viewport (the new area takes the left part).
    outliner = split(view3d, 'VERTICAL', OUTLINER_FACTOR)
    outliner.type = 'OUTLINER'

    # --- editor settings ---
    so = outliner.spaces.active
    so.display_mode = 'VIEW_LAYER'
    so.use_filter_object_content = False   # Maya: DAG only, no shapes (ui_layout.md:259-262)
    so.use_filter_children = True
    # Maya's Outliner lists the DAG from the world: no collection rows (they are the Layer
    # Editor's display layers here) and no per-row render toggle (step 31, delegated).
    so.use_filter_collection = False
    so.show_restrict_column_render = False

    le = layer_editor.spaces.active
    le.display_mode = 'VIEW_LAYER'
    le.use_filter_object = False           # collections only = display layers

    sp = strip.spaces.active               # = ui/shelf.py make_strip
    marker = bpy.data.masks.new(STRIP_MARKER)
    marker.use_fake_user = True
    sp.mask = marker
    sp.mode = 'VIEW'
    sp.show_region_tool_header = True
    sp.show_region_ui = False
    sp.show_region_toolbar = False

    v3d = view3d.spaces.active
    v3d.show_region_ui = True              # sidebar = Channel Box host (step 6)
    v3d.show_region_toolbar = True         # = Maya Toolbox
    v3d.show_region_tool_header = True     # row for the Maya Status Line (step 7)
    v3d.lens = MAYA_LENS
    v3d.region_3d.view_perspective = 'PERSP'
    maya_views()

    ws.name = "General"                    # Maya workspace name (ui_layout.md:78)
    return {"outliner": outliner, "view3d": view3d, "strip": strip, "attribute_editor": attribute_editor,
            "layer_editor": layer_editor}


def maya_views():
    """Every 3D view of every workspace sees Maya's new-scene persp view in cm: a default
    pCube1 (1 cm, decision 8) looks the size it does in Maya (docs/steps/step_21.md)."""
    import bpy
    from mathutils import Vector
    eye = Vector(MAYA_PERSP_EYE) * MAYA_UNIT
    for screen in bpy.data.screens:
        for area in screen.areas:
            for space in area.spaces:
                if space.type != 'VIEW_3D':
                    continue
                space.clip_start, space.clip_end = (c * MAYA_UNIT for c in MAYA_CLIP)
                # Finest perspective grid step = 1 cm (= units.grid_scale; docs/steps/step_25.md):
                # Maya grid lines every 1 cm (research/maya/defaults.json:29-31).
                space.overlay.grid_scale = MAYA_UNIT
                # Maya's grid axes are grey (displayColor gridAxis = grid); Blender colours them with
                # the theme axis colours, which now are Maya's manipulator red/green (step 43).
                space.overlay.show_axis_x = space.overlay.show_axis_y = False
                # Maya's finite 12-unit grid instead of Blender's floor, also in ortho side views
                # (src/maya_kit/ui/maya_grid.py: show_floor / show_ortho_grid off, grid_lines 0; step 45).
                space.overlay.show_floor = space.overlay.show_ortho_grid = False
                space.overlay.grid_lines = 0
                # Maya view furniture (ViewCube, axis triad, camera name; ui/view_furniture.py, step 46)
                # replaces Blender's navigation gizmo and text info.
                space.show_gizmo_navigate = False
                space.overlay.show_text = False
                rv3d = space.region_3d
                rv3d.view_location = (0.0, 0.0, 0.0)
                rv3d.view_rotation = eye.normalized().to_track_quat('Z', 'Y')
                rv3d.view_distance = eye.length


def setup_scene():
    import bpy
    scene = bpy.context.scene
    us = scene.unit_settings
    us.system = 'METRIC'
    us.length_unit = 'CENTIMETERS'         # decision 1: display cm, keep 1 BU = 1 m
    us.scale_length = 1.0
    # Maya animation range = frame range, playback range = preview range (docs/steps/step_20.md 3).
    scene.frame_start, scene.frame_end = 1, MAYA_RANGE_END
    scene.use_preview_range = True
    scene.frame_preview_start, scene.frame_preview_end = 1, MAYA_FRAME_END
    scene.render.fps, scene.render.fps_base = 24, 1.0
    # Maya's new scene is empty (concepts.md §15).
    for ob in list(bpy.data.objects):
        data = ob.data
        bpy.data.objects.remove(ob)
        if data is not None and data.users == 0:
            for coll in (bpy.data.meshes, bpy.data.cameras, bpy.data.lights):
                if data.name in coll and coll[data.name] == data:
                    coll.remove(data)
                    break
    for mat in list(bpy.data.materials):
        if mat.users == 0:
            bpy.data.materials.remove(mat)


def main():
    import bpy
    build_layout()
    setup_scene()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT), compress=True, check_existing=False)
    OUT.with_suffix(".blend1").unlink(missing_ok=True)  # Blender's backup of the previous file
    print(f"make_startup: wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    try:
        import bpy  # noqa: F401
    except ImportError:
        sys.exit(run_outside_blender())
    main()
