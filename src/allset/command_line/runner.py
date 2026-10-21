# SPDX-License-Identifier: GPL-3.0-or-later
"""Run one command-line entry: Python only (MEL is not supported, decision 5).

research/maya/ui_layout.md §4.12 (:290-293). Design: docs/steps/step_7.md 「계획」 4, docs/steps/step_130_exec.md.

The kit runs no code itself (extension review, issue #40): the entry is written into a Text datablock and run by
Blender's own ``text.run_script`` — the path of the Text Editor's Run Script. Before that the source is rewritten
with plain text edits (``prepare``):

- ``import maya.cmds as cmds`` / ``from maya import cmds`` / ``import maya.cmds`` / ``from maya.cmds import ls`` import
  the kit's ``cmds_shim`` (``maya_stub`` for ``maya``) by its real package path — no import hook, nothing new in the
  module table;
- one line in front hands the run's ``globals()`` to the runner (``bind``), which fills in the session names
  (``bpy``, ``C``, ``D``, ``cmds``, ``mc`` and the variables of earlier entries) and reads the run's variables back
  afterwards — also after an error, like Maya — so they persist between entries;
- a final expression ``x`` becomes ``_allset_result = (x)``: its value is the Maya-style ``# Result: ... #``.

``text.run_script`` runs in a fresh ``__main__`` namespace and reports a Python error as an operator error (a
RuntimeError when called from Python, measured in 4.5): its last traceback line is the result line.
"""

import ast
import contextlib
import io
import re

import bpy

HISTORY_LIMIT = 20
TEXT_NAME = ".allset_command_line"      # hidden Text the Command Line / Script Editor entry runs from
RESULT = "_allset_result"
RUNNER = "_allset_runner"
_PKG = __package__                      # "<extension package>.command_line"

_namespace = {}
history = []
_runs = []                              # per running entry (nested runs possible): {"names": its globals()}


class Result:
    __slots__ = ("text", "error")

    def __init__(self, text="", error=False):
        self.text = text
        self.error = error

    def __repr__(self):
        return f"Result({self.text!r}, error={self.error})"


def namespace():
    """Session names every run starts with: bpy, C, D, cmds / mc (maya.cmds subset) + earlier entries' variables."""
    if not _namespace:
        from . import cmds_shim
        _namespace.update(bpy=bpy, C=bpy.context, D=bpy.data, cmds=cmds_shim, mc=cmds_shim)
    return _namespace


def bind(names):
    """Called by the first line of a prepared entry with its ``globals()``: give it the session names and keep the
    dictionary, read after the run (Blender doesn't clear a Run Script namespace, measured in 4.5)."""
    names.update(namespace())
    if _runs:
        _runs[-1]["names"] = names


def _collect(run, persist):
    """(result value, variables) of a finished run; variables go into the session when ``persist``."""
    names = run.get("names") or {}
    value = names.pop(RESULT, None)
    if persist:
        for key, item in names.items():
            if not key.startswith("__") and key != RUNNER:
                _namespace[key] = item
    return value


def reset():
    _namespace.clear()
    history.clear()


def _remember(source):
    if history and history[-1] == source:
        return
    history.append(source)
    del history[:-HISTORY_LIMIT]


# --- source rewriting (plain text edits on the parsed statement positions) ---------------------------------------

def _maya_import(node):
    """Replacement text of an import statement that names ``maya`` / ``maya.cmds``, else None."""
    if isinstance(node, ast.Import):
        if not any(a.name in ("maya", "maya.cmds") for a in node.names):
            return None
        parts = []
        for a in node.names:
            if a.name == "maya.cmds" and a.asname:
                parts.append(f"from {_PKG} import cmds_shim as {a.asname}")
            elif a.name in ("maya", "maya.cmds"):              # binds ``maya`` (with .cmds)
                parts.append(f"from {_PKG} import maya_stub as {a.asname or 'maya'}")
            else:
                parts.append(f"import {a.name}" + (f" as {a.asname}" if a.asname else ""))
        return "; ".join(parts)
    if isinstance(node, ast.ImportFrom) and node.level == 0:
        if node.module == "maya.cmds":
            names = ", ".join(a.name + (f" as {a.asname}" if a.asname else "") for a in node.names)
            return f"from {_PKG}.cmds_shim import {names}"
        if node.module == "maya" and any(a.name == "cmds" for a in node.names):
            names = ", ".join(("cmds_shim as " + (a.asname or "cmds")) if a.name == "cmds"
                              else (a.name + (f" as {a.asname}" if a.asname else "")) for a in node.names)
            return f"from {_PKG}.maya_stub import {names}"
    return None


def prepare(source, tree=None):
    """The text that runs for ``source`` (see the module docstring); ``tree`` = ``ast.parse(source)``."""
    tree = tree if tree is not None else ast.parse(source)
    data = source.encode("utf-8")               # ast column offsets count UTF-8 bytes
    starts = [0]
    for line in data.split(b"\n")[:-1]:
        starts.append(starts[-1] + len(line) + 1)

    def span(node):
        return (starts[node.lineno - 1] + node.col_offset, starts[node.end_lineno - 1] + node.end_col_offset)

    edits = []
    for node in ast.walk(tree):
        text = _maya_import(node)
        if text is not None:
            edits.append((*span(node), text.encode("utf-8")))
    if tree.body and isinstance(tree.body[-1], ast.Expr):
        a, b = span(tree.body[-1])
        edits.append((a, b, f"{RESULT} = (".encode("utf-8") + data[a:b] + b"\n)"))
    for a, b, text in sorted(edits, reverse=True):
        data = data[:a] + text + data[b:]
    head = f"from {_PKG} import runner as {RUNNER}; {RUNNER}.bind(globals())\n"
    return head + data.decode("utf-8") + "\n"


# --- running through Blender's Run Script ------------------------------------------------------------------------

def _error_line(message):
    """Last traceback line of a ``text.run_script`` error report ("ZeroDivisionError: division by zero")."""
    lines = [ln for ln in message.splitlines() if ln.strip() and not ln.startswith("Location:")]
    last = lines[-1].strip() if lines else message.strip()
    for prefix in ("Error: Python: ", "Error: "):
        if last.startswith(prefix):
            last = last[len(prefix):]
    return last


def run_text(code, name=TEXT_NAME, persist=True):
    """Run prepared ``code`` with Blender's Run Script from a temporary Text ``name``; (result value, error line or
    None, printed text)."""
    text = bpy.data.texts.new(name)
    text_name = text.name
    text.write(code)
    run = {"names": None}
    _runs.append(run)
    out = io.StringIO()
    error = None
    try:
        with contextlib.redirect_stdout(out), bpy.context.temp_override(edit_text=text):
            bpy.ops.text.run_script()
    except RuntimeError as ex:
        error = _error_line(str(ex))
    finally:
        _runs.pop()
        leftover = bpy.data.texts.get(text_name)     # the script may have loaded a file or removed it
        if leftover is not None:
            bpy.data.texts.remove(leftover)
    printed = out.getvalue()
    if printed:
        print(printed, end="")              # still reach the system console
    value = _collect(run, persist)
    if error is None and run["names"] is None:
        error = "RuntimeError: the script did not run"
    return value, error, printed


def run(source, name=TEXT_NAME, persist=True, remember=True):
    """Run ``source`` (Command Line / Script Editor / shelf button); the value of a final expression is the result."""
    source = source.strip()
    if not source:
        return Result()
    if remember:
        _remember(source)
    try:
        tree = ast.parse(source, mode="exec")
    except SyntaxError as ex:
        hint = mel_to_python(source)
        if hint == "":
            return Result("# Error: MEL is not supported, use Python", True)
        if hint is not None:
            return Result(f"# Error: no MEL, use Python: {hint}", True)
        return Result(f"# Error: SyntaxError: {ex.msg}", True)

    value, error, printed = run_text(prepare(source, tree), name, persist)
    if error is not None:
        from . import cmds_shim
        m = re.match(r"NameError: name '(\w+)' is not defined", error)
        if m and hasattr(cmds_shim, m.group(1)):
            return Result(f"# Error: {error} (Maya command? use cmds.{m.group(1)}(...))", True)
        return Result(f"# Error: {error}", True)
    if value is not None:
        return Result(f"# Result: {_format(value)} #")
    lines = printed.strip().splitlines()
    return Result(lines[-1]) if lines else Result()


def _format(value):
    if isinstance(value, bpy.types.ID):
        return value.name
    return repr(value)


# --- MEL hint: "polyCube -w 2 -h 3;" -> "cmds.polyCube(w=2, h=3)" -------------------

# A MEL statement: command word, then flags / numbers / names / "strings" only.
_MEL_STATEMENT = re.compile(r'^\s*[A-Za-z_]\w*(\s+("(?:[^"\\]|\\.)*"|-?[\w.|:\[\]]+))*\s*$')
_TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|\S+')


def _value(token):
    if token.startswith('"'):
        return token
    try:
        float(token)
        return token
    except ValueError:
        return repr(token)


def _statement(stmt):
    tokens = _TOKEN.findall(stmt)
    if not tokens:
        return None
    cmd, args, flags = tokens[0], [], []
    i = 1
    while i < len(tokens):
        tok = tokens[i]
        if re.match(r"^-[A-Za-z]\w*$", tok):
            values = []
            i += 1
            while i < len(tokens) and not re.match(r"^-[A-Za-z]\w*$", tokens[i]):
                values.append(tokens[i])
                i += 1
            if len(values) == 1:
                flags.append(f"{tok[1:]}={_value(values[0])}")
            else:
                flags.append(f"{tok[1:]}=True")
                args.extend(_value(v) for v in values)
            continue
        args.append(_value(tok))
        i += 1
    return f"cmds.{cmd}({', '.join(args + flags)})"


def mel_to_python(source):
    """Best-effort cmds translation of MEL-looking input; "" = MEL without a
    translation (variables, backquotes); None = doesn't look like MEL."""
    if "$" in source or "`" in source:
        return ""
    parts = [p for p in source.split(";") if p.strip()]
    if not parts or not all(_MEL_STATEMENT.match(p) for p in parts):
        return None
    # Needs a MEL marker, so plain typos ("hello world") stay Python syntax errors.
    if not (source.rstrip().endswith(";") or re.search(r"\s-[A-Za-z]", source) or '"' in source):
        return None
    out = [_statement(p) for p in parts]
    return "; ".join(o for o in out if o)
