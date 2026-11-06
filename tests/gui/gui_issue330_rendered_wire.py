"""#330 in a real UI: the selection highlight (the kit's Maya wire, lead green #43ffa3 / other selected white) is
drawn in Rendered shading too — the Maya layout keeps Blender's own outline off, so without the wire a selection
in a lit view (EEVEE or Cycles) had no highlight at all. Rendered shading with overlays off (the IPR picture) stays
clean. Screenshots: gui_issue330_solid.png, gui_issue330_eevee.png, gui_issue330_cycles.png."""

import os
import sys
from importlib import import_module

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, view3d, win  # noqa: E402

GUI_TIMEOUT = 360
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])


LEAD, OTHER = hexrgb("#43ffa3"), hexrgb("#ffffff")


def space():
    return view3d()[0].spaces.active


def shot(name):
    """Window screenshot as (h, w, 3) sRGB floats, row 0 = window bottom; also kept in SHOTS."""
    path = os.path.join(SHOTS or bpy.app.tempdir, f"gui_issue330_{name}.png")
    screenshot(path)
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)[..., :3]


def near(px, colour, tol=0.09):
    return np.abs(px - colour).max(axis=-1) < tol


def hits(px, xy, colour, r=1, tol=0.09):
    """Any pixel within r px of window point xy is ``colour``."""
    x, y = int(round(xy[0])), int(round(xy[1]))
    return bool(near(px[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1], colour, tol).any())


def to_window(world):
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    area, region = view3d()
    p = location_3d_to_region_2d(region, area.spaces.active.region_3d, world)
    return None if p is None else (p.x + region.x, p.y + region.y)


def edge_points(ob):
    mw = ob.matrix_world
    return [(mw @ ((ob.data.vertices[a].co + ob.data.vertices[b].co) / 2)) for a, b in
            (e.vertices for e in ob.data.edges)]


def wire_counts(px):
    """(lead green edge midpoints hit, other white edge midpoints hit, Blender orange px around the lead, green px)."""
    lead, other = (bpy.data.objects[n] for n in C["names"])
    on = {}
    for ob, col in ((lead, LEAD), (other, OTHER)):
        pts = [to_window(p) for p in edge_points(ob)]
        on[ob.name] = sum(1 for p in pts if p is not None and hits(px, p, col))
    theme = np.array(bpy.context.preferences.themes[0].view_3d.object_active[:3])
    pts = np.array([to_window(p) for p in edge_points(lead)])
    x0, y0 = (pts.min(axis=0) - 6).astype(int)
    x1, y1 = (pts.max(axis=0) + 6).astype(int)
    orange = int(near(px[y0:y1, x0:x1], theme, 0.06).sum())
    green = int(near(px[y0:y1, x0:x1], LEAD).sum())
    return on[lead.name], on[other.name], orange, green


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def wait(fn, cond, limit=40):
    """Run ``fn`` again next tick until ``cond()`` or ``limit`` ticks."""
    C.setdefault(fn.__name__, 0)
    if not cond() and C[fn.__name__] < limit:
        C[fn.__name__] += 1
        sys.modules["sim"]._steps.insert(0, fn)
        return True
    return False


def ticks(fn, n):
    """Give the view ``n`` more ticks (redraws) before ``fn`` goes on."""
    key = "ticks_" + fn.__name__
    C[key] = C.get(key, 0) + 1
    if C[key] <= n:
        redraw()
        sys.modules["sim"]._steps.insert(0, fn)
        return True
    return False


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    area, region = view3d()
    unit = import_module(MODULE + ".operators.units").maya_unit()
    obs = []
    with bpy.context.temp_override(window=win(), area=area, region=region):
        for x in (0.0, 2.2):
            bpy.ops.allset.create(kind='CUBE')
            ob = bpy.context.view_layer.objects.active
            ob.location = (x * unit, 0.0, 0.5 * unit)
            obs.append(ob)
        lead, other = obs
        for ob in bpy.context.scene.objects:
            ob.select_set(ob in (lead, other))
        bpy.context.view_layer.objects.active = lead
        bpy.ops.view3d.view_selected()
    C["names"] = [o.name for o in obs]
    C["engine"] = bpy.context.scene.render.engine
    sp = space()
    check(f"the Maya layout view has Blender's outline off ({sp.overlay.show_outline_selected}), overlays on "
          f"({sp.overlay.show_overlays}), shading {sp.shading.type}",
          not sp.overlay.show_outline_selected and sp.overlay.show_overlays)
    # rest the pointer in the viewport's empty corner (the pre-selection highlight would draw over the wire)
    ev('MOUSEMOVE', 'NOTHING', x=region.x + 12, y=region.y + 12)
    redraw()


@step
def s_solid():
    if ticks(s_solid, 2):
        return
    lead, other, orange, green = wire_counts(shot("solid"))
    check(f"Solid shading: lead green wire on {lead}/12 edges, other white on {other}/12 (>= 7 each)",
          lead >= 7 and other >= 7)
    C["solid_green"] = green
    space().shading.type = 'MATERIAL'
    redraw()


@step
def s_material():
    if ticks(s_material, 3):
        return
    lead, other, orange, green = wire_counts(shot("material"))
    check(f"Material Preview: lead green wire on {lead}/12 edges, other white on {other}/12 (>= 7 each)",
          lead >= 7 and other >= 7)
    space().shading.type = 'RENDERED'
    redraw()


@step
def s_eevee():
    if ticks(s_eevee, 4):
        return
    sp = space()
    lead, other, orange, green = wire_counts(shot("eevee"))
    check(f"Rendered shading ({C['engine']}): lead green wire on {lead}/12 edges, other white on {other}/12 (>= 7 each)",
          sp.shading.type == 'RENDERED' and lead >= 7 and other >= 7)
    check(f"Rendered shading: lead box green {green} px (Solid had {C['solid_green']}), Blender orange {orange} px",
          green >= C["solid_green"] // 2 and orange < max(1, green // 10))
    sp.overlay.show_overlays = False
    redraw()


@step
def s_no_overlays():
    if ticks(s_no_overlays, 2):
        return
    lead, other, orange, green = wire_counts(shot("no_overlays"))
    check(f"Rendered shading with overlays off (the IPR picture): no wire ({lead}/12 green, {other}/12 white, {green} px)",
          lead == 0 and other == 0 and green == 0)
    space().overlay.show_overlays = True
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.device = 'CPU'
    bpy.context.scene.cycles.preview_samples = 2
    redraw()


@step
def s_cycles():
    if ticks(s_cycles, 8):
        return
    lead, other, orange, green = wire_counts(shot("cycles"))
    check(f"Rendered shading (CYCLES): lead green wire on {lead}/12 edges, other white on {other}/12 (>= 7 each), "
          f"Blender orange {orange} px", lead >= 7 and other >= 7 and orange < max(1, green // 10))
    bpy.context.scene.render.engine = C["engine"]
    space().shading.type = 'SOLID'
    redraw()


@step
def s_back():
    if ticks(s_back, 2):
        return
    lead, other, orange, green = wire_counts(shot("back"))
    check(f"back in Solid shading: lead green wire on {lead}/12 edges, other white on {other}/12", lead >= 7 and other >= 7)


run()
