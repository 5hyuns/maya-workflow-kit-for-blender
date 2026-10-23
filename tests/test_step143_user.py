"""Step 143: GitHub user reports before 0.3.0 (docs/steps/step_143_user.md; GUI: tests/gui/gui_step143_user.py).

- #84: the Maya double-click loop pick passed ``ring=False`` to ``mesh.loop_select``, which Blender 5.1+ no longer has
  (ring pick is ``mesh.edgering_select`` there): "keyword "ring" unrecognized" on 5.2.
- #80: after Ctrl+E the extrude manipulator hid the kit Move manipulator, and W didn't bring it back (the Move tool
  was already active), so the new faces couldn't be moved the usual way. Maya: a tool key swaps the extrude
  manipulator for that tool's one; the node stays in Channel Box INPUTS.
"""

import inspect
from importlib import import_module

import bpy

import kit

loop_pick = import_module(kit.MODULE + ".operators.loop_pick")


# --- #84 ------------------------------------------------------------------------------------------------------------

def test_loop_select_keywords_exist_in_this_blender():
    props = {p.identifier for p in bpy.ops.mesh.loop_select.get_rna_type().properties}
    for between in (False, True):
        args = loop_pick.loop_select_args(between)
        missing = set(args) - props
        assert not missing, f"mesh.loop_select has no {missing} in Blender {bpy.app.version_string} ({props})"
        assert args["extend"] is between


def test_loop_pick_passes_no_ring_keyword():
    # 4.5 still has ``ring`` (default False), so the RNA check above can't catch it coming back there
    src = inspect.getsource(loop_pick.ALLSET_OT_loop_pick.invoke)
    assert "loop_select_args(" in src and "ring=" not in src, src
    assert "ring" not in loop_pick.loop_select_args(False)
