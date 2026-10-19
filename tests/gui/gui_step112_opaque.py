"""Step 112 in a real UI: the user's report (2026-10-19) — Maya mode switched on in a Blender with its own theme, Maya
layout appended, the Tool Box column not fitted (the cursor fit didn't run, as in the user's session).

Before: the Channel Box dock was drawn over the viewport with the theme's region alpha (0 in Blender's theme), so
the grid showed through everything but the value fields; the Tool Box column (56 px, a 70 px toolbar at 1.25) drew
no toolbar at all and the tools fell back into the main view. Now: "Solid Side Panels" (region overlap off) puts
the dock beside the viewport on an opaque background, the template column has room for the toolbar, and its spare
width is the toolbar colour. Checked on screen pixels (``screen.screenshot`` read back)."""

import os
import sys
from importlib import import_module

import bpy

os.environ["ALLSET_GUI_KEEP_OVERLAP"] = "1"   # start with Blender's overlap on, like the user
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, run, step, setup, screenshot, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
os.environ["ALLSET_FIT_WARP"] = "0"   # the user's case: the column keeps the template width
C = {}


def mod(name):
    return import_module(f"{MODULE}.{name}")


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def column():
    return next((a for a in win().screen.areas if a.type == 'VIEW_3D' and mod("ui.toolbox").is_toolbox(a.spaces.active)),
                None)


def region(area, kind):
    return next((r for r in area.regions if r.type == kind and r.width > 1), None)


def grab():
    scale = round(bpy.context.preferences.system.ui_scale * 100)
    path = os.path.join(SHOTS or bpy.app.tempdir, f"step112_opaque_{scale}.png")
    screenshot(path)
    return path


def pixel(path, x, y):
    img = bpy.data.images.load(path, check_existing=False)
    try:
        w, _h = img.size
        i = (y * w + x) * 4
        return tuple(img.pixels[i:i + 3])
    finally:
        bpy.data.images.remove(img)


def near(a, b, tol=3 / 255):
    return all(abs(p - q) <= tol for p, q in zip(a, b))


def rgb(c):
    return tuple(round(v * 255) for v in c)


@step
def s_setup():
    setup()
    C["theme"] = bpy.context.preferences.themes[0].name
    mod("switch").enter_layout(win())


@step
def s_wait():
    redraw()


@step
def s_layout():
    prefs = bpy.context.preferences
    check(f"Blender's own theme ({C['theme']}), Solid Side Panels on -> region overlap off",
          C["theme"] != "Maya" and mod("preferences").get().use_maya_panels and not prefs.system.use_region_overlap)
    area, win_r = view3d()
    stack = mod("ui.maya_dock").find_stack(win().screen)     # its own area since step 116
    ui = region(stack, 'WINDOW') if stack else None
    check(f"the dock is beside the viewport, not over it (view {win_r.x}+{win_r.width}, dock {ui and ui.x})",
          ui is not None and win_r.x + win_r.width <= ui.x + 1)
    col = column()
    tools = region(col, 'TOOLS') if col else None
    check(f"the Tool Box column draws its toolbar unfitted ({col.width if col else None} px, toolbar "
          f"{tools.width if tools else None})", tools is not None)
    check("the main view shows no toolbar of its own", not area.spaces.active.show_region_toolbar)
    sp = col.spaces.active
    check("column: overlays off, flat background in the toolbar colour",
          not sp.overlay.show_overlays and sp.shading.background_type == 'VIEWPORT')
    redraw()


@step
def s_pixels_wait():
    redraw()


@step
def s_pixels():
    path = grab()
    theme = bpy.context.preferences.themes[0].view_3d
    back = tuple(mod("compat").toolbar_back(bpy.context.preferences.themes[0]))[:3]
    view_bg = tuple(theme.space.gradients.high_gradient)
    dock_back = tuple(bpy.context.preferences.themes[0].properties.space.back)[:3]   # a Properties editor (step 116)
    stack = mod("ui.maya_dock").find_stack(win().screen)
    ui = region(stack, 'WINDOW')
    p_dock = pixel(path, ui.x + 3, ui.y + ui.height // 2)    # the dock's left margin, half way down
    check(f"dock background opaque = its editor colour {rgb(dock_back)} (pixel {rgb(p_dock)}, viewport {rgb(view_bg)})",
          near(p_dock, dock_back) and not near(p_dock, view_bg))
    col = column()
    p_col = pixel(path, col.x + col.width - 4, col.y + col.height // 2)
    check(f"spare Tool Box width = toolbar colour {rgb(back)} (pixel {rgb(p_col)})", near(p_col, back))
    # something turns the column's overlays on (the user's shot showed the X axis line in it): settled again
    col.spaces.active.overlay.show_overlays = True


@step
def s_overlays_wait():
    pass


@step
def s_overlays_wait2():   # the fit timer runs every 0.5 s
    pass


@step
def s_overlays():
    col = column()
    check("a column whose overlays were turned on is still the Tool Box and is settled again",
          col is not None and not col.spaces.active.overlay.show_overlays)
    mod("switch").set_mode(False)


@step
def s_blender_check():
    check("Blender mode gives region overlap back", bpy.context.preferences.system.use_region_overlap)


run()
