"""Generate the Maya layout startup.blend bundled inside the extension (in a GUI Blender; read from there by
switch.enter_layout and "New Scene in Maya Layout", never copied out of the extension since step 130).

    python tools/make_startup.py          # re-runs itself in `blender --factory-startup` (a window opens briefly)

Writes src/allset/app_template/Maya_Workflow_Kit/startup.blend. Layout and reasons: ,
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
OUT = ROOT / "src" / "allset" / "app_template" / "Maya_Workflow_Kit" / "startup.blend"

# Maya widget sizes at effective scale 1.0 (, ui_layout.md:122-127):
# Outliner 260, Channel Box / Layer Editor dock 260 (+ tab strip), Time Slider 36 (the timeline WINDOW region); the
# Range Slider is the timeline header, flipped under it.
OUTLINER_PX = 260
# Maya's right dock column (Channel Box / Layer Editor 260 + Maya's side tab strip; dock [1323, 260] then tabs to
# 1598) = the kit's tab-stack area, its own Properties editor right of the viewport (ui/maya_dock.py, step 116).
DOCK_PX = 260 + 17
# Tool Box column = room for one toolbar column up to UI scale 1.6 (step 112): area sizes are pixels scaled with
# the window, not with the UI scale, and a toolbar wider than its area is not drawn at all (an empty strip, the
# tools fell back into the main view). ui/toolbox.fit_columns fits it to one toolbar column when it can; until
# then the extra width is the toolbar colour (toolbox.settle). 1.6 = 125 % display in a window down to 1280 px.
TOOLBOX_ROOM = 1.6
# = ui/maya_dock.ROLE_FLAGS['STACK']: Tool tab + this hidden tab flag marks the tab-stack area (step 116)
STACK_FLAG = "show_properties_world"
# Maya Time Slider right end: current time field (90) + 8 transport buttons (22 each) and padding
# (20_time_slider_crop.png: from x 1300 of 1596; ui_layout.md:272-276).
TIME_CONTROLS_PX = 300   # = ui/channel_box.py CATEGORY
TIME_SLIDER_PX = 36
# Maya shelf: tab row + 32 px icon row = 64 (ui_layout.md:219-222; step 113: one WINDOW region draws both)
SHELF_PX = 64
WINDOW_SIZE = (1600, 900)
EDGE = 3                  # px the area edges take from a split (checked)
# Maya persp = focal length 35 on a 36 mm film back (, tools/look_data.py:25), horizontal
# 54.4 deg. Blender measures the viewport lens on a 72 mm sensor (tan(fov/2) = 36 / lens, :11-12),
# so the same angle is lens 70; lens 35 was a 91.6 deg view.
MAYA_LENS = 70.0
MAYA_FRAME_END = 120      # playback 1-120 (concepts.md, PREF:469-470)
MAYA_RANGE_END = 200      # animation range 1-200 (PREF:471-472; step 20: Range Slider outer fields)
STRIP_MARKER = ".AllsetStrip"  # = ui/shelf.py MARKER (Status Line row)
SHELF_MARKER = ".AllsetShelf"  # = ui/shelf.py SHELF_MARKER (Shelf row)
# Maya lengths are cm (): 1 Maya unit = 0.01 BU with 's m + cm display.
MAYA_UNIT = 0.01
# factory viewport #5c5c5c as a scene-linear View3DShading.background_color (sRGB 92/255 -> linear; #45)
MAYA_BG_LINEAR = round(((92 / 255 + 0.055) / 1.055) ** 2.4, 5)
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
    """= src/allset/ui/toolbox.py is_toolbox (kept in sync by tests/test_step49_layout.py)."""
    return (space.type == 'VIEW_3D' and space.show_region_toolbar and not space.show_region_header
            and not space.show_region_ui and not space.show_object_viewport_mesh)


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
        # 2. Maya strip (step 12): Status Line row, then the Shelf row, over everything, full width. The Status
        #    Line is a header-only area (Blender keeps it one header high at any UI scale, step 49); the
        #    Shelf area = tab row (header) + icon row (WINDOW, ui/shelf.py gizmos, step 51).
        strip = yield from self.split(view, 'HORIZONTAL', hdr + 3 + SHELF_PX + EDGE, 'TOP')
        strip.type = 'IMAGE_EDITOR'
        yield
        shelf = yield from self.split(strip, 'HORIZONTAL', SHELF_PX + 2, 'BOTTOM')
        strip = max((a for a in self.scr.areas if a.type == 'IMAGE_EDITOR'), key=lambda a: a.y)  # the top part
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
        toolbox = yield from self.split(view, 'VERTICAL', round(_region(view, 'TOOLS').width * TOOLBOX_ROOM) + 1, 'LEFT')
        yield
        outliner = yield from self.split(self.biggest_view(), 'VERTICAL', OUTLINER_PX + EDGE, 'LEFT')
        outliner.type = 'OUTLINER'
        yield
        # 5. Maya's right tab stack (Channel Box / Layer Editor | Attribute Editor | Modeling Toolkit): its own area,
        #    not the viewport's sidebar (step 116).
        dock = yield from self.split(self.biggest_view(), 'VERTICAL', DOCK_PX + EDGE, 'RIGHT')
        dock.type = 'PROPERTIES'
        yield
        yield from self.make_stack(dock)
        view = self.biggest_view()
        self.areas = {"strip": strip, "shelf": shelf, "timeline": timeline, "toolbox": toolbox, "outliner": outliner,
                      "view3d": view, "dock": dock}
        self.configure()
        yield
        # 6. The timeline's sidebar = the Time Slider's current frame field and transport buttons (step 50): drag
        #    its left edge (region size has no API).
        yield from self.drag_region_edge(timeline, TIME_CONTROLS_PX)
        self.report()
        shot = os.environ.get("MAKE_STARTUP_SHOT")
        if shot:
            with bpy.context.temp_override(window=self.win):
                bpy.ops.screen.screenshot(filepath=shot)
        self.save()

    def drag_region_edge(self, area, width):
        ui = _region(area, 'UI')
        x0, y = ui.x, ui.y + ui.height // 2
        target = area.x + area.width - width
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
        log("sidebar", area.ui_type, _region(area, 'UI').width)

    def make_stack(self, area):
        """The tab-stack area = a Properties editor on its Tool tab, header and tab column hidden, marked by
        ``STACK_FLAG`` (= ui/maya_dock.set_role; the Tool tab can be chosen once the editor has drawn)."""
        bpy = self.bpy
        space = area.spaces.active
        for _i in range(20):
            try:
                space.context = 'TOOL'
                break
            except TypeError:
                area.tag_redraw()
                yield
        assert space.context == 'TOOL', space.context
        for prop in space.bl_rna.properties:
            if prop.identifier.startswith("show_properties_"):
                setattr(space, prop.identifier, prop.identifier in ("show_properties_tool", STACK_FLAG))
        space.show_region_header = False
        with self.ov(area, 'NAVIGATION_BAR'):
            assert bpy.ops.screen.region_toggle(region_type='NAVIGATION_BAR') == {'FINISHED'}
        yield
        log("stack", area.width, [(r.type, r.width) for r in area.regions])

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
        so.show_restrict_column_hide = False   # no eye column: Maya hides with H (= ui/maya_outliner.setup, step 50)

        st = a["timeline"].spaces.active       # Time Slider: no channel list; sidebar = its buttons (step 50)
        st.show_region_channels = False
        st.show_region_ui = True

        for key, name in (("strip", STRIP_MARKER), ("shelf", SHELF_MARKER)):   # = ui/shelf.py markers
            sp = a[key].spaces.active
            marker = self.bpy.data.masks.new(name)
            marker.use_fake_user = True
            sp.mask = marker
            sp.mode = 'VIEW'
            # the shelf row draws tab strip + icons in its WINDOW region (ui/shelf.py, step 113)
            sp.show_region_header = key == "strip"
            sp.show_region_tool_header = False
            sp.show_region_ui = False
            sp.show_region_toolbar = False

        v3d = a["view3d"].spaces.active
        v3d.show_region_ui = False             # Maya panels are their own areas, not the viewport's sidebar (step 116)
        v3d.show_region_toolbar = False        # the Tool Box column replaces it (step 49)
        v3d.show_region_tool_header = True     # = Maya's panel toolbar (ui/panel_toolbar.py, step 113)
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
                space.lens = MAYA_LENS        # every view (and Four View's persp quadrant) = Maya's persp angle
                # Finest perspective grid step = 1 cm (= units.grid_scale; ):
                # Maya grid lines every 1 cm ().
                space.overlay.grid_scale = MAYA_UNIT
                # Maya's grid axes are grey (displayColor gridAxis = grid); Blender colours them with
                # the theme axis colours, which now are Maya's manipulator red/green (step 43).
                space.overlay.show_axis_x = space.overlay.show_axis_y = False
                # Maya's finite 12-unit grid instead of Blender's floor, also in ortho side views
                # (src/allset/ui/maya_grid.py: show_floor / show_ortho_grid off, grid_lines 0; step 45).
                space.overlay.show_floor = space.overlay.show_ortho_grid = False
                space.overlay.grid_lines = 0
                # Maya view furniture (ViewCube, axis triad, camera name; ui/view_furniture.py, step 46)
                # replaces Blender's navigation gizmo and text info.
                space.show_gizmo_navigate = False
                space.overlay.show_text = False
                # Maya highlights a selection with its wireframe (ui/selection_wire.py), no outline (step 47).
                space.overlay.show_outline_selected = False
                # Maya draws no line from a child to its parent (factory Maya 2022 shots:
                # *.png, step 91); Blender's dashed relationship lines go.
                space.overlay.show_relationship_lines = False
                # factory viewport is flat #5c5c5c (). Without the kit
                # theme (step 130) that is view data: the view's own background colour, scene linear (#45).
                space.shading.background_type = 'VIEWPORT'
                space.shading.background_color = (MAYA_BG_LINEAR,) * 3
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
    # Maya tool defaults (,  「계획」 3):
    # axis mode per tool (Move World, Rotate/Scale Object, P12), the manipulator at the lead
    # object's pivot (P11; edit mode switches to the bbox centre, operators/pivot.py), rotate
    # step 15 degrees (S3).
    ts = scene.tool_settings
    slots = scene.transform_orientation_slots
    slots[0].type = 'GLOBAL'
    slots[1].type, slots[2].type, slots[3].type = 'GLOBAL', 'LOCAL', 'LOCAL'
    ts.transform_pivot_point = 'ACTIVE_ELEMENT'
    ts.snap_angle_increment_3d = 0.2617993877991494
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
