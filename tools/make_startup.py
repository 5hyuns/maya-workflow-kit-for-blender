"""Generate the Maya layout app template's startup.blend (in a GUI Blender).

    python tools/make_startup.py          # re-runs itself in `blender --factory-startup` (a window opens briefly)

Writes src/maya_kit/app_template/MayaKit/startup.blend. Layout and reasons: ,
 「계획」 ( General layout, widget sizes from
). It runs in a GUI Blender because the factory right column
(Outliner + Properties) can only be removed there: in `-b` screen.area_close hangs and area_join crashes
or adds empty areas (checked, step 49). The window is 1600x900 at the Maya density (effective UI scale
1.0, like the look_compare shots), so area sizes are Maya pixels; the sidebar width is set by dragging
its edge with simulated events (no API). User dirs point into tmp/build_env (tools/build.sandbox_env).
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "maya_kit" / "app_template" / "MayaKit" / "startup.blend"

# Maya widget sizes at effective scale 1.0 (, ui_layout.md:122-127):
# Outliner 260, Channel Box / Layer Editor dock 260 (+ tab strip), Time Slider 36 (the timeline WINDOW region); the
# Range Slider is the timeline header, flipped under it.
OUTLINER_PX = 260
# Sidebar = Maya's dock column: Channel Box / Layer Editor 260 + the vertical dock tab strip right of it
# (Maya: dock [1323, 260] then tabs to 1598). Blender draws its tab strip inside the sidebar.
DOCK_PX = 260 + 17
DOCK_CATEGORY = "Channel Box"   # = ui/channel_box.py CATEGORY
TIME_SLIDER_PX = 36
WINDOW_SIZE = (1600, 900)
EDGE = 3                  # px the area edges take from a split (checked)
MAYA_LENS = 35.0          # persp focal length 35 (concepts.md)
MAYA_FRAME_END = 120      # playback 1-120 (concepts.md, PREF:469-470)
MAYA_RANGE_END = 200      # animation range 1-200 (PREF:471-472; step 20: Range Slider outer fields)
STRIP_MARKER = ".MayaKitStrip"  # = ui/shelf.py MARKER (Status Line row)
SHELF_MARKER = ".MayaKitShelf"  # = ui/shelf.py SHELF_MARKER (Shelf row)
# Maya lengths are cm (): 1 Maya unit = 0.01 BU with 's m + cm display.
MAYA_UNIT = 0.01
MAYA_CLIP = (0.1, 10000.0)        # cm,  (= operators/units.py CLIP)
MAYA_PERSP_EYE = (28.0, -28.0, 21.0)  # cm, Maya persp (28, 21, 28) Y-up  (= units.PERSP_EYE)


def run_outside_blender():
    import subprocess
    sys.path.insert(0, str(ROOT / "tools"))
    import build
    w, h = WINDOW_SIZE
    r = subprocess.run([os.environ.get("BLENDER", build.DEFAULT_BLENDER), "--factory-startup",
                        "--enable-event-simulate", "--window-geometry", "0", "0", str(w), str(h),
                        "--python-exit-code", "1", "--python", __file__],
                       env=build.sandbox_env(), stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    ok = False
    for line in r.stdout.splitlines():
        if line.startswith("make_startup"):
            print(line)
            ok = ok or line.startswith("make_startup: wrote")
    if r.returncode or not ok:
        sys.stderr.write(r.stdout[-4000:] + r.stderr[-3000:])
        return r.returncode or 1
    return 0


def log(*args):
    print("make_startup:", *args)
    sys.stdout.flush()


def _region(area, kind):
    return next((r for r in area.regions if r.type == kind), None)


def is_toolbox_space(space):
    """= src/maya_kit/ui/toolbox.py is_toolbox (kept in sync by tests/test_step49_layout.py)."""
    return (space.type == 'VIEW_3D' and space.show_region_toolbar and not space.show_region_header
            and not space.show_region_ui and not space.overlay.show_overlays)


class Builder:
    """Layout edits, one per timer tick (screen operators and simulated events need a redraw in between)."""

    def __init__(self):
        import bpy
        self.bpy = bpy
        self.win = bpy.context.window_manager.windows[0]
        self.areas = {}

    @property
    def scr(self):
        return self.win.screen

    def ov(self, area, region_type='WINDOW'):
        return self.bpy.context.temp_override(window=self.win, screen=self.scr, area=area,
                                              region=_region(area, region_type))

    def only(self, area_type):
        found = [a for a in self.scr.areas if a.type == area_type]
        assert len(found) == 1, (area_type, len(found))
        return found[0]

    def biggest_view(self):
        return max((a for a in self.scr.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)

    def split(self, area, direction, px, side):
        """Split ``area`` so the part on ``side`` ('TOP'/'BOTTOM'/'LEFT'/'RIGHT') is ``px`` pixels; return it
        (a generator: ``part = yield from self.split(...)``)."""
        bpy = self.bpy
        size = area.height if direction == 'HORIZONTAL' else area.width
        frac = px / size
        factor = {'TOP': 1 - frac, 'BOTTOM': frac, 'LEFT': frac, 'RIGHT': 1 - frac}[side]
        before = {a.as_pointer() for a in self.scr.areas}
        with self.ov(area):
            assert bpy.ops.screen.area_split(direction=direction, factor=factor) == {'FINISHED'}
        new = next((a for a in self.scr.areas if a.as_pointer() not in before), None)
        assert new is not None, ("split made no area", direction, px, side, size, factor,
                                 [(a.type, a.x, a.y, a.width, a.height) for a in self.scr.areas])
        pair = (new, area)
        yield   # area rectangles update on the next redraw
        if direction == 'HORIZONTAL':
            top, bottom = sorted(pair, key=lambda a: -a.y)
            return top if side == 'TOP' else bottom
        left, right = sorted(pair, key=lambda a: a.x)
        return left if side == 'LEFT' else right

    def steps(self):
        bpy = self.bpy
        prefs = bpy.context.preferences
        # Maya density: effective scale 1.0 (= tests/gui --ui-scale 0.8 on a 125 % display)
        prefs.view.ui_scale = prefs.view.ui_scale / prefs.system.ui_scale
        for value in ('PRESS', 'RELEASE'):  # close the splash (it eats simulated events)
            self.win.event_simulate(type='ESC', value=value, x=800, y=450)
        yield
        ws = bpy.data.workspaces["Layout"]
        assert self.win.workspace == ws, "factory startup should open the Layout workspace"
        # 1. Remove the factory timeline and the right column: one 3D View is left.
        for kind in ('DOPESHEET_EDITOR', 'OUTLINER', 'PROPERTIES'):
            with self.ov(self.only(kind)):
                assert bpy.ops.screen.area_close() == {'FINISHED'}, kind
            yield
        assert [a.type for a in self.scr.areas] == ['VIEW_3D'], [a.type for a in self.scr.areas]
        view = self.scr.areas[0]
        hdr = _region(view, 'HEADER').height
        # 2. Maya strip (step 12): Status Line row, then the Shelf row, over everything, full width. Two
        #    header-only areas: Blender keeps each at least one header high, so they follow the UI scale.
        strip = yield from self.split(view, 'HORIZONTAL', 2 * hdr + 2 + EDGE, 'TOP')
        strip.type = 'IMAGE_EDITOR'
        yield
        shelf = yield from self.split(strip, 'HORIZONTAL', hdr + 1, 'BOTTOM')
        yield
        # 3. Time Slider (timeline WINDOW) + Range Slider (its header, flipped under it), full width.
        timeline = yield from self.split(self.biggest_view(), 'HORIZONTAL', TIME_SLIDER_PX + hdr + EDGE, 'BOTTOM')
        timeline.type = 'DOPESHEET_EDITOR'
        timeline.ui_type = 'TIMELINE'
        yield
        with self.ov(timeline, 'HEADER'):
            assert bpy.ops.screen.region_flip() == {'FINISHED'}
        yield
        # 4. Tool Box column (a 3D View showing only its toolbar, ui/toolbox.py), then the Outliner.
        view = self.biggest_view()
        toolbox = yield from self.split(view, 'VERTICAL', _region(view, 'TOOLS').width + 1, 'LEFT')
        yield
        outliner = yield from self.split(self.biggest_view(), 'VERTICAL', OUTLINER_PX + EDGE, 'LEFT')
        outliner.type = 'OUTLINER'
        yield
        view = self.biggest_view()
        self.areas = {"strip": strip, "shelf": shelf, "timeline": timeline, "toolbox": toolbox, "outliner": outliner, "view3d": view}
        self.configure()
        yield
        # 5. Sidebar = Channel Box dock, 260 px: drag its left edge (region size has no API).
        ui = _region(view, 'UI')
        x0, y = ui.x, ui.y + ui.height // 2
        target = view.x + view.width - DOCK_PX
        self.win.event_simulate(type='MOUSEMOVE', value='NOTHING', x=x0 + 1, y=y)
        yield
        self.win.event_simulate(type='LEFTMOUSE', value='PRESS', x=x0 + 1, y=y)
        yield
        for i in range(1, 6):
            self.win.event_simulate(type='MOUSEMOVE', value='NOTHING', x=x0 + 1 + (target - x0) * i // 5, y=y)
            yield
        self.win.event_simulate(type='LEFTMOUSE', value='RELEASE', x=target + 1, y=y)
        yield
        yield
        # 6. The sidebar opens on the Channel Box tab: the region saves its active category, but there is
        #    no API to set it and the kit is not installed here, so a stand-in panel gives the category and
        #    Ctrl+wheel over the tab strip selects it. Blender's Item tab (C panels, step 49) stays possible.
        yield from self.select_dock_tab(view)
        self.report()
        shot = os.environ.get("MAKE_STARTUP_SHOT")
        if shot:
            with bpy.context.temp_override(window=self.win):
                bpy.ops.screen.screenshot(filepath=shot)
        self.save()

    def select_dock_tab(self, view):
        bpy = self.bpy

        class MAYAKIT_PT_dock_stand_in(bpy.types.Panel):
            bl_space_type = 'VIEW_3D'
            bl_region_type = 'UI'
            bl_category = DOCK_CATEGORY
            bl_label = "Channel Box"

            def draw(self, context):
                self.layout.label(text="Channel Box")

        bpy.utils.register_class(MAYAKIT_PT_dock_stand_in)
        ui = _region(view, 'UI')
        for _i in range(12):
            view.tag_redraw()
            yield
            if ui.active_panel_category == DOCK_CATEGORY:
                break
            self.win.event_simulate(type='MOUSEMOVE', value='NOTHING', x=ui.x + ui.width - 8, y=ui.y + ui.height - 60)
            self.win.event_simulate(type='WHEELDOWNMOUSE', value='PRESS', x=ui.x + ui.width - 8,
                                    y=ui.y + ui.height - 60, ctrl=True)
        log("sidebar tab", ui.active_panel_category)
        assert ui.active_panel_category == DOCK_CATEGORY, ui.active_panel_category
        bpy.utils.unregister_class(MAYAKIT_PT_dock_stand_in)

    def configure(self):
        a = self.areas
        so = a["outliner"].spaces.active
        so.display_mode = 'VIEW_LAYER'
        so.use_filter_object_content = False   # Maya: DAG only, no shapes (ui_layout.md:259-262)
        so.use_filter_children = True
        # Maya's Outliner lists the DAG from the world: no collection rows (display layers are the
        # Layer Editor's) and no per-row render toggle (step 31, delegated).
        so.use_filter_collection = False
        so.show_restrict_column_render = False

        st = a["timeline"].spaces.active       # Time Slider: no channel list, no sidebar
        st.show_region_channels = False
        st.show_region_ui = False

        for key, name in (("strip", STRIP_MARKER), ("shelf", SHELF_MARKER)):   # = ui/shelf.py markers
            sp = a[key].spaces.active
            marker = self.bpy.data.masks.new(name)
            marker.use_fake_user = True
            sp.mask = marker
            sp.mode = 'VIEW'
            sp.show_region_header = True
            sp.show_region_tool_header = False
            sp.show_region_ui = False
            sp.show_region_toolbar = False

        v3d = a["view3d"].spaces.active
        v3d.show_region_ui = True              # sidebar = Channel Box dock (step 6, 11)
        v3d.show_region_toolbar = False        # the Tool Box column replaces it (step 49)
        v3d.show_region_tool_header = False    # Maya has no tool settings row (step 49)
        v3d.show_region_header = True          # Maya panel menu bar (step 37)
        v3d.lens = MAYA_LENS
        v3d.region_3d.view_perspective = 'PERSP'

        tb = a["toolbox"].spaces.active        # = ui/toolbox.py is_toolbox
        tb.show_region_toolbar = True
        tb.show_region_header = False
        tb.show_region_tool_header = False
        tb.show_region_ui = False
        tb.show_gizmo = False
        tb.overlay.show_overlays = False       # no kit grid / furniture / wire either (they check it)
        # No object type is visible in this view: nothing is drawn behind the tools, and a click under
        # them (it reaches the WINDOW region) selects or deselects nothing (BKE_base_is_visible checks
        # object_type_exclude_viewport). An empty local view would do the same but Blender drops it on load.
        for name in dir(tb):
            if name.startswith("show_object_viewport_"):
                setattr(tb, name, False)
        assert is_toolbox_space(tb)
        maya_views()
        self.bpy.data.workspaces["Layout"].name = "General"   # Maya workspace name (ui_layout.md:78)

    def report(self):
        for a in self.scr.areas:
            regions = {r.type: (r.x, r.y, r.width, r.height) for r in a.regions if r.width > 1 and r.height > 1}
            log("area", a.ui_type, (a.x, a.y, a.width, a.height), regions)

    def save(self):
        import bpy
        setup_scene()
        OUT.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT), compress=True, check_existing=False)
        OUT.with_suffix(".blend1").unlink(missing_ok=True)  # Blender's backup of the previous file
        log(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes)")


def maya_views():
    """Every 3D view of every workspace sees Maya's new-scene persp view in cm: a default
    pCube1 (1 cm, ) looks the size it does in Maya."""
    import bpy
    from mathutils import Vector
    eye = Vector(MAYA_PERSP_EYE) * MAYA_UNIT
    for screen in bpy.data.screens:
        for area in screen.areas:
            for space in area.spaces:
                if space.type != 'VIEW_3D':
                    continue
                space.clip_start, space.clip_end = (c * MAYA_UNIT for c in MAYA_CLIP)
                # Finest perspective grid step = 1 cm (= units.grid_scale; ):
                # Maya grid lines every 1 cm ().
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
                # Maya highlights a selection with its wireframe (ui/selection_wire.py), no outline (step 47).
                space.overlay.show_outline_selected = False
                rv3d = space.region_3d
                rv3d.view_location = (0.0, 0.0, 0.0)
                rv3d.view_rotation = eye.normalized().to_track_quat('Z', 'Y')
                rv3d.view_distance = eye.length


def setup_scene():
    import bpy
    scene = bpy.context.scene
    us = scene.unit_settings
    us.system = 'METRIC'
    us.length_unit = 'CENTIMETERS'         # : display cm, keep 1 BU = 1 m
    us.scale_length = 1.0
    # Maya animation range = frame range, playback range = preview range.
    scene.frame_start, scene.frame_end = 1, MAYA_RANGE_END
    scene.use_preview_range = True
    scene.frame_preview_start, scene.frame_preview_end = 1, MAYA_FRAME_END
    scene.render.fps, scene.render.fps_base = 24, 1.0
    # Maya's new scene is empty (concepts.md).
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
    gen = Builder().steps()

    def tick():
        try:
            next(gen)
        except StopIteration:
            bpy.ops.wm.quit_blender()
            return None
        except Exception:
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
            os._exit(1)
        return 0.3

    bpy.app.timers.register(tick, first_interval=1.5)


if __name__ == "__main__":
    try:
        import bpy  # noqa: F401
    except ImportError:
        sys.exit(run_outside_blender())
    if bpy.app.background:
        sys.exit("make_startup: needs a GUI Blender (see the module docstring)")
    main()
