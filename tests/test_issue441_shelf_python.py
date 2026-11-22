"""#441: in the Shelf Editor, switching a button's Command Type to Python fills the Python field with that button's own
command, not with an unrelated default."""
from importlib import import_module

import bpy

import kit

draft = import_module(kit.MODULE + ".ui.shelf_editor_draft")

BUTTONS = [
    {"label": "Cube", "type": "action", "action": {"type": "python", "code": "import bpy\n\nbpy.ops.mesh.primitive_cube_add()"}},
    {"label": "Planar", "menu": "UV/Planar"},
    {"label": "Smooth", "type": "action", "action": {"type": "operator", "id": "object.shade_smooth",
                                                     "properties": {"keep_sharp_edges": False}}},
    {"label": "Move", "type": "action", "action": {"type": "tool", "id": "builtin.move"}},
    {"label": "Planar X", "menu": "UV/Planar"},
]


def _load(index):
    saved = draft._draft_buttons
    draft._draft_buttons = lambda _shelf_id, create=False: BUTTONS
    try:
        draft._load_button(bpy.context, index)
    finally:
        draft._draft_buttons = saved
    return bpy.context.window_manager


def test_menu_item_becomes_its_operator():
    _load(0)                                       # a Python button first, as in the report
    wm = _load(1)
    assert wm.allset_se_type == "MAYA_MENU_ITEM"
    wm.allset_se_type = "PYTHON"
    assert wm.allset_se_script == "import bpy\n\nbpy.ops.allset.uv_planar()", wm.allset_se_script


def test_operator_keeps_its_properties():
    wm = _load(2)
    assert wm.allset_se_type == "OPERATOR"
    wm.allset_se_type = "PYTHON"
    assert wm.allset_se_script == "import bpy\n\nbpy.ops.object.shade_smooth(keep_sharp_edges=False)", \
        wm.allset_se_script


def test_tool():
    wm = _load(3)
    assert wm.allset_se_type == "TOOL"
    wm.allset_se_type = "PYTHON"
    assert wm.allset_se_script == "import bpy\n\nbpy.ops.wm.tool_set_by_id(name='builtin.move')", wm.allset_se_script


def test_python_button_keeps_its_code():
    wm = _load(0)
    assert wm.allset_se_type == "PYTHON"
    wm.allset_se_type = "PYTHON"
    assert wm.allset_se_script == "import bpy\n\nbpy.ops.mesh.primitive_cube_add()"


def test_menu_item_with_component_rules_runs_as_the_menu():
    from importlib import import_module as imp
    menu_map = imp(kit.MODULE + ".ui.menu_map")
    path = next(iter(sorted(menu_map.EDIT_MODE)))
    BUTTONS[4] = {"label": "Item", "menu": path}
    wm = _load(4)
    wm.allset_se_type = "PYTHON"
    assert wm.allset_se_script == f"import bpy\n\nbpy.ops.allset.menu_item(item={path!r})", wm.allset_se_script


def test_generated_python_runs():
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.mesh.primitive_plane_add()
    wm = _load(1)
    wm.allset_se_type = "PYTHON"
    exec(compile(wm.allset_se_script, "shelf", "exec"), {})
    assert bpy.context.active_object.data.uv_layers.active is not None
