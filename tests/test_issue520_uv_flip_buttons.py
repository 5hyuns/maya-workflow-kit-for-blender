"""#520: the UV Toolkit's Flip button (U / V) and the UV Shell marking menu's Flip Along U / V items flip the
selected faces in their own direction with the Coordinate and Cut UV Perimeter of the Flip options, like Maya (the
same command as UV Editor > Modify > Flip)."""

import inspect
from importlib import import_module

import bpy

import kit
import test_issue506_uv_flip_options as base

mm = import_module(kit.MODULE + ".marking.menus")
ow = import_module(kit.MODULE + ".operators.option_windows")
uvtk = import_module(kit.MODULE + ".ui.uv_toolkit")


def test_marking_items_run_the_flip_command():
    entries = {p: a for p, _l, a in mm.label_walk(mm.SHIFT_UV_SHELL, "S")}
    assert entries["S/Flip Along U"] == ("allset.uv_flip", {"direction": 'HORIZONTAL', "use_options": True})
    assert entries["S/Flip Along V"] == ("allset.uv_flip", {"direction": 'VERTICAL', "use_options": True})


def test_toolkit_buttons_run_the_flip_command():
    """The toolkit's Flip button with its U / V choice runs the Flip command in that direction."""
    src = inspect.getsource(uvtk)
    assert "transform.mirror" not in src
    assert src.count('"allset.uv_flip", text="Flip"') == 1
    assert "op.direction = 'HORIZONTAL' if tk.flip_axis == 'U' else 'VERTICAL'" in src


def test_defaults_flip_around_the_pivot_and_cut_free():
    ob = base._grid()
    base._select_faces(ob, base._left)
    before = base._corners(ob)
    assert bpy.ops.allset.uv_flip(direction='HORIZONTAL', use_options=True) == {'FINISHED'}
    base._check(before, base._corners(ob), base._faces_where(ob, base._left), 0, 0.425, ob)
    assert any(e.seam for e in base._bm(ob)[0].edges), "the cut border is a seam"


def test_saved_options_apply_but_not_their_direction():
    ob = base._grid()
    base._select_faces(ob, base._left)
    before = base._corners(ob)
    # saved: Horizontal, Global, no cut; the Flip V button still flips V, around V 0, dragging the shared UVs
    ow.store("uv_flip", {"direction": "Horizontal", "coordinate": "Global", "cut": False})
    assert bpy.ops.allset.uv_flip(direction='VERTICAL', use_options=True) == {'FINISHED'}
    bm, _uv = base._bm(ob)
    left = base._faces_where(ob, base._left)
    drag = {(f.index, l.vert.index) for f in bm.faces if f.index not in left for l in f.loops
            if abs(l.vert.co.x - 2.0) < 1e-6}
    base._check(before, base._corners(ob), left, 1, 0.0, ob, drag)
    assert not any(e.seam for e in bm.edges)
    ow.store("uv_flip", None)
