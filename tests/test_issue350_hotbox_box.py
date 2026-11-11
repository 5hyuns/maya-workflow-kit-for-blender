"""#350: the option box ❒ of a Maya menu the Space hotbox opens. The hotbox notes the menu and the pointer x when it
opens it; the menu's draw then takes the popup-at-pointer model (the pointer at 0.8 of the menu's width, kept 10 px
inside the window), so ``option_click.box_zone`` knows its ❒ zone. A menu called from anywhere else keeps no zone.
The geometry against real menus: tests/gui/gui_issue350_hotbox_box.py (UI scale 1.0 and 1.25)."""

from importlib import import_module
from types import SimpleNamespace

import bpy

import kit

oc = import_module(kit.MODULE + ".ui.option_click")
ms = import_module(kit.MODULE + ".ui.menu_sets")

WIN_PTR, REGION_PTR, OTHER_PTR = 0x350A, 0x350B, 0x350C


class _Ref(SimpleNamespace):
    def as_pointer(self):
        return self.ptr


def _context(region_ptr=REGION_PTR, width=1600):
    window = _Ref(ptr=WIN_PTR, width=width)
    region = _Ref(ptr=region_ptr, type='WINDOW', x=0)
    return SimpleNamespace(window=window, region=region, area=_Ref(ptr=0x350D, type='VIEW_3D'),
                           preferences=bpy.context.preferences)


def _clear():
    oc._OPEN.pop(WIN_PTR, None)
    oc._CALLED.pop(WIN_PTR, None)


def _u():
    return oc._unit(bpy.context)


def test_hotbox_menu_draw_takes_the_pointer_model():
    _clear()
    ctx = _context()
    oc.note_called(ctx, "Edit Mesh", 700)
    oc.note_draw(ctx, "Edit Mesh")
    assert oc._OPEN[WIN_PTR]["Edit Mesh"] == ("AT", 700)
    oc.note_draw(ctx, "Create")                        # another menu drawn there: not the one the hotbox opened
    assert oc._OPEN[WIN_PTR]["Create"] is None
    oc.note_draw(_context(OTHER_PTR), "Edit Mesh")     # the same menu called from another region
    assert oc._OPEN[WIN_PTR]["Edit Mesh"] is None
    oc.note_draw(ctx, "Edit Mesh")
    assert oc._OPEN[WIN_PTR]["Edit Mesh"] == ("AT", 700)
    oc.forget_called(ctx)                              # a marking menu item opened it at an unknown pointer
    oc.note_draw(ctx, "Edit Mesh")
    assert oc._OPEN[WIN_PTR]["Edit Mesh"] is None
    _clear()


def test_popup_width_model():
    u, size = 20, 11.0
    w = oc.popup_width("Edit Mesh", u, size)
    pulldown = oc.width("Edit Mesh", u, size)
    widest = max(ms.text_width(t, size) for t, _sub in oc.rows("Edit Mesh")[0])
    assert w == int(widest + oc.POPUP_PAD_UNITS * u) + 2, (w, widest)
    assert abs(w - pulldown) < 2 * u, (w, pulldown)
    assert oc.popup_width("No Such Menu", u, size) is None


def test_zone_of_a_menu_opened_at_the_pointer():
    _clear()
    ctx = _context()
    u = _u()
    size = ms.font_size(bpy.context)
    w = oc.popup_width("Edit Mesh", u, size)
    oc._OPEN[WIN_PTR] = {"Edit Mesh": ("AT", 800)}
    x0, x1, left, right = oc.box_zone(ctx, "Edit Mesh/Bevel")
    assert left == 800 - round(oc.POPUP_AT * w) and right == left + w, (left, right, w)
    assert left < x0 < x1 == right, (x0, x1)
    # the ❒ glyph ends at the text start (1 px border + the pulldown's text inset) + the aligned row text
    text = oc.rows("Edit Mesh")[1]["Edit Mesh/Bevel"]
    end = left + 1 + oc.TEXT_UNITS * u + ms.text_width(text, size)
    glyph = ms.text_width(ms.BOX_MARK.strip(), size)
    assert abs((x0 + oc.ZONE_LEFT_UNITS * u + glyph) - end) < 0.01
    # kept inside the window: near the left edge, near the right edge
    oc._OPEN[WIN_PTR] = {"Edit Mesh": ("AT", 40)}
    assert oc.box_zone(ctx, "Edit Mesh/Bevel")[2] == oc.SCREEN_MARGIN
    oc._OPEN[WIN_PTR] = {"Edit Mesh": ("AT", 1590)}
    assert oc.box_zone(ctx, "Edit Mesh/Bevel")[3] == 1600 - oc.SCREEN_MARGIN
    # a submenu opens against the popup's right edge (its own pulldown width)
    oc._OPEN[WIN_PTR] = {"Create": ("AT", 600)}
    wc = oc.popup_width("Create", u, size)
    zone = oc.box_zone(ctx, "Create/Polygon Primitives/Cube")
    assert zone is not None and zone[2] == 600 - round(oc.POPUP_AT * wc) + wc, zone
    assert zone[3] - zone[2] == oc.width("Create/Polygon Primitives", u, size)
    # a menu drawn anywhere else: no zone
    oc._OPEN[WIN_PTR] = {"Edit Mesh": None}
    assert oc.box_zone(ctx, "Edit Mesh/Bevel") is None
    _clear()


def test_background_click_is_never_a_box_click():
    assert oc.on_box(bpy.context, "Edit Mesh/Bevel") is False
