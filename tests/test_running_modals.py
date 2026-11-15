"""A modal operator that has just finished or been cancelled keeps its handler in the window until Blender removes it,
and ``Window.modal_operators`` lists that handler as None. ``live_refs.running_modals`` gives a window's modal
operators without such an entry; every check in the kit that looks at the running modals reads them through it (or
skips the None itself), so an ended modal neither raises nor hides the modal that is still running."""

import ast
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace

import bpy

import kit

SRC = Path(__file__).resolve().parent.parent / "src" / "allset"

live_refs = import_module(kit.MODULE + ".live_refs")

HELPER = ("live_refs.py", "running_modals")
# reads that skip the empty entry themselves (``op is not None`` in the same expression)
GUARDED = {
    ("ui/component_colors.py", "_navigating"),
    ("ui/graph_keys_draw.py", "_navigation"),
    ("ui/maya_joints.py", "transform_op"),
    ("ui/maya_joints.py", "scrubbing"),
    ("operators/joint_selection.py", "_switches"),
}

MOVE = "TRANSFORM_OT_translate"


def _op(idname):
    return SimpleNamespace(bl_idname=idname)


def _win(*ops):
    return SimpleNamespace(modal_operators=list(ops))


def _wm(*ops):
    return SimpleNamespace(windows=[_win(*ops)])


def _mod(name):
    return import_module(kit.MODULE + "." + name)


class _Bpy:
    """``bpy`` whose context has one window with the given modal operators."""

    def __init__(self, wm):
        self.context = SimpleNamespace(window_manager=wm, window=wm.windows[0])

    def __getattr__(self, name):
        return getattr(bpy, name)


def _with_bpy(module, wm, fn):
    saved = module.bpy
    module.bpy = _Bpy(wm)
    try:
        return fn()
    finally:
        module.bpy = saved


# --- the helper --------------------------------------------------------------------------------------------------


def test_running_modals_skips_ended_entries():
    move, box = _op(MOVE), _op("VIEW3D_OT_select_box")
    assert live_refs.running_modals(_win(None, move, None, box)) == [move, box]
    assert live_refs.running_modals(_win(None)) == []
    assert live_refs.running_modals(_win()) == []


def test_running_modals_of_a_missing_or_removed_window_is_empty():
    class Removed:
        @property
        def modal_operators(self):
            raise ReferenceError("StructRNA of type Window has been removed")

    assert live_refs.running_modals(None) == []
    assert live_refs.running_modals(Removed()) == []
    assert live_refs.running_modals(SimpleNamespace()) == []
    for w in bpy.context.window_manager.windows:
        assert None not in live_refs.running_modals(w)


# --- every read in the kit goes through it -----------------------------------------------------------------------


class _Reads(ast.NodeVisitor):
    """(function name, line) of each ``.modal_operators`` / ``"modal_operators"`` in a module, and the functions'
    source."""

    def __init__(self, text):
        self.text, self.func, self.reads, self.funcs = text, None, [], {}

    def _function(self, node):
        outer, self.func = self.func, node.name
        self.funcs[node.name] = ast.get_source_segment(self.text, node)
        self.generic_visit(node)
        self.func = outer

    visit_FunctionDef = visit_AsyncFunctionDef = _function

    def visit_Attribute(self, node):
        if node.attr == "modal_operators":
            self.reads.append((self.func, node.lineno))
        self.generic_visit(node)

    def visit_Constant(self, node):
        if node.value == "modal_operators":
            self.reads.append((self.func, node.lineno))


def _scan():
    reads, funcs = [], {}
    for path in sorted(SRC.rglob("*.py")):
        rel = path.relative_to(SRC).as_posix()
        text = path.read_text(encoding="utf-8")
        if "modal_operators" not in text:
            continue                    # no read (parsing the large table files is slow)
        visitor = _Reads(text)
        visitor.visit(ast.parse(text))
        reads += [(rel, func, line) for func, line in visitor.reads]
        funcs.update({(rel, name): src for name, src in visitor.funcs.items()})
    return reads, funcs


def test_every_modal_list_read_goes_through_the_helper():
    assert SRC.is_dir(), SRC
    reads, funcs = _scan()
    allowed = {HELPER} | GUARDED
    stray = [f"{rel}:{line} ({func})" for rel, func, line in reads if (rel, func) not in allowed]
    assert not stray, ("read a window's modal operators with live_refs.running_modals(window) (it skips the entry of "
                       "a modal that has just ended): " + ", ".join(stray))
    found = {(rel, func) for rel, func, _line in reads}
    assert allowed <= found, f"listed reads no longer in the source, update the list: {sorted(allowed - found)}"
    unguarded = sorted(key for key in GUARDED if "op is not None" not in funcs[key])
    assert not unguarded, f"listed reads no longer skip the empty entry: {unguarded}"


# --- the checks that read the list -------------------------------------------------------------------------------


def test_window_checks_skip_an_ended_entry():
    manip = _mod("operators.manip")
    assert manip._transform_running(_win(None, _op(MOVE))) is True
    assert manip._transform_running(_win(None)) is False

    weights = _mod("ui.weight_numbers")
    assert weights._stroke_running(SimpleNamespace(window=_win(None, _op("PAINT_OT_weight_paint")))) is True
    assert weights._stroke_running(SimpleNamespace(window=_win(None))) is False

    command_line = _mod("command_line")
    command_line.MODAL_HELP["ALLSET_OT_test_modal"] = "Test help"
    try:
        context = SimpleNamespace(window=_win(None, _op("ALLSET_OT_test_modal")))
        assert command_line.modal_help(context) == "Test help"
        assert command_line.modal_help(SimpleNamespace(window=_win(None))) == ""
    finally:
        command_line.MODAL_HELP.pop("ALLSET_OT_test_modal", None)


def test_window_manager_checks_skip_an_ended_entry():
    listeners = _mod("modal_listeners")
    assert listeners.tool_running(_wm(None, _op(MOVE))) is True, "the ended entry hides the running move"
    assert listeners.tool_running(_wm(None, _op("ALLSET_OT_cb_wheel"))) is False

    uv_arrays = _mod("operators.uv_arrays")
    assert uv_arrays.editing_now(_wm(None)) is False, "an ended entry is no running edit"
    assert uv_arrays.editing_now(_wm(None, _op(MOVE))) is True

    select_2d = _mod("operators.select_2d")
    assert select_2d._modal_running(_wm(None, _op("GRAPH_OT_select_box")), "GRAPH_OT_select_box") is True
    assert select_2d._modal_running(_wm(None), "GRAPH_OT_select_box") is False

    graph_move = _mod("operators.graph_move")
    assert graph_move._transform_running(_wm(None, _op(MOVE))) is True
    assert graph_move._transform_running(_wm(None)) is False

    preview = _mod("operators.joint_preview")
    assert preview._tool_running(SimpleNamespace(window_manager=_wm(None, _op(preview.TOOL)))) is True
    assert preview._tool_running(SimpleNamespace(window_manager=_wm(None))) is False

    follow = _mod("operators.pivot_follow")
    assert follow._running(SimpleNamespace(window_manager=_wm(None, _op(MOVE)))) == MOVE
    assert follow._running(SimpleNamespace(window_manager=_wm(None))) is None


def test_context_checks_skip_an_ended_entry():
    checks = (("ui.channel_box", "_transforming"), ("operators.auto_key", "_transforming"),
              ("operators.pivot", "_transform_running"), ("operators.anim_snapshot", "_transforming"),
              ("operators.graph_curves_203", "_transform_running"), ("ui.soft_overlay", "_transform_running"))
    for name, fn in checks:
        module = _mod(name)
        check = getattr(module, fn)
        assert _with_bpy(module, _wm(None, _op(MOVE)), check) is True, name
        assert _with_bpy(module, _wm(None), check) is False, name
    skin_layers = _mod("operators.skin_layers")
    assert _with_bpy(skin_layers, _wm(None, _op("PAINT_OT_weight_paint")), skin_layers.stroke_running) is True
    assert _with_bpy(skin_layers, _wm(None), skin_layers.stroke_running) is False
    shells = _mod("operators.uv_shell_select")
    assert _with_bpy(shells, _wm(None, _op("UV_OT_select_box")), shells._box_running) is True
    assert _with_bpy(shells, _wm(None), shells._box_running) is False


def test_navigation_chord_watch_skips_an_ended_entry():
    view = _mod("operators.view")
    op = SimpleNamespace(held={'MIDDLEMOUSE'})
    move = SimpleNamespace(type='MOUSEMOVE', value='NOTHING')
    running = SimpleNamespace(window=_win(None, _op("VIEW3D_OT_move")))
    assert view.ALLSET_OT_nav_chord.modal(op, running, move) == {'PASS_THROUGH'}, "the track still runs"
    ended = SimpleNamespace(window=_win(None))
    assert view.ALLSET_OT_nav_chord.modal(op, ended, move) == {'FINISHED', 'PASS_THROUGH'}
