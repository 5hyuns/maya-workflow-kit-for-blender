"""#409: every command row of View > Image Plane and of the Image Plane button's right-click menu shows its own
tooltip (not the button's show / hide text), in Japanese and Chinese too. Other panel menu rows keep the tooltip of
the command they run."""

import types
from importlib import import_module

import bpy

import kit

i18n = import_module(kit.MODULE + ".i18n")
pip = import_module(kit.MODULE + ".ui.panel_image_plane")
pm = import_module(kit.MODULE + ".ui.panel_menus")
LOCALES = ("ja_JP", "zh_HANS", "zh_HANT")


class _Layout:
    """Records the panel_run buttons a menu draws."""

    def __init__(self, out):
        self.out = out
        self.enabled = True

    def row(self, **_kw):
        return self

    column = row

    def separator(self, **_kw):
        pass

    def label(self, **_kw):
        pass

    def menu(self, *_a, **_kw):
        pass

    def prop(self, *_a, **_kw):
        pass

    def operator(self, idname, text="", **_kw):
        ns = types.SimpleNamespace(op="", props="{}", tip="", item="", key="", camera="", name="")
        if idname == pm.ALLSET_OT_panel_run.bl_idname:
            self.out.append((text, ns))
        return ns


def _rows():
    out = []
    for cls in (pip.ALLSET_MT_panel_image_plane, pip.ALLSET_MT_pt_image_plane, pip.ALLSET_MT_pt_image_plane_display):
        cls.draw(types.SimpleNamespace(layout=_Layout(out), bl_idname=cls.bl_idname), bpy.context)
    return out


def _tip(ns):
    return pm.ALLSET_OT_panel_run.description(bpy.context, ns)


def test_each_image_plane_row_has_its_own_tooltip():
    rows = _rows()
    assert len(rows) == 6, [t for t, _ns in rows]       # Import Image x2, Import Movie, Delete, None, RGBA
    button = bpy.ops.allset.image_plane.get_rna_type().description
    tips = {text: _tip(ns) for text, ns in rows}
    for text, tip in tips.items():
        assert tip and tip != button, (text, tip)
    assert len({tips[t] for t in tips}) == 5, tips      # both Import Image... rows say the same
    assert "image" in tips["Import Image..."].lower() and "movie" in tips["Import Movie..."].lower(), tips


def test_the_tooltips_are_translated():
    rows = _rows()
    for locale in LOCALES:
        table = i18n.LANGUAGES[locale]
        missing = [ns.tip for _t, ns in rows if ns.tip not in table]
        assert not missing, (locale, missing)


def test_other_panel_rows_keep_their_command_tooltip():
    ns = types.SimpleNamespace(op="allset.camera_from_view", props="{}", tip="")
    assert _tip(ns) == i18n.tip_text(bpy.ops.allset.camera_from_view.get_rna_type().description)
