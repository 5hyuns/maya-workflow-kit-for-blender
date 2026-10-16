# SPDX-License-Identifier: GPL-3.0-or-later
"""Run one command-line entry: Python only (MEL is not supported, ).

 (:290-293);  #14
(:93-94: exec in a namespace like the Python console). Design:
 「계획」 4. Plain functions, no UI: headless-testable.
"""

import ast
import contextlib
import io
import re
import traceback

import bpy

HISTORY_LIMIT = 20

_namespace = {}
history = []


class Result:
    __slots__ = ("text", "error")

    def __init__(self, text="", error=False):
        self.text = text
        self.error = error

    def __repr__(self):
        return f"Result({self.text!r}, error={self.error})"


def namespace():
    """Session namespace: bpy, C, D, cmds (maya.cmds subset); variables persist."""
    if not _namespace:
        from . import cmds_shim
        _namespace.update(__name__="__maya_kit_cmd__", bpy=bpy, C=bpy.context, D=bpy.data,
                          cmds=cmds_shim, mc=cmds_shim)
    return _namespace


def reset():
    _namespace.clear()
    history.clear()


def _remember(source):
    if history and history[-1] == source:
        return
    history.append(source)
    del history[:-HISTORY_LIMIT]


def run(source):
    """Execute ``source``; the value of a final expression is the result."""
    source = source.strip()
    if not source:
        return Result()
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

    last = None
    if tree.body and isinstance(tree.body[-1], ast.Expr):
        last = ast.Expression(tree.body.pop().value)
    ns = namespace()
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            if tree.body:
                exec(compile(tree, "<command line>", "exec"), ns)
            value = eval(compile(last, "<command line>", "eval"), ns) if last else None
    except NameError as ex:
        from . import cmds_shim
        name = getattr(ex, "name", None)
        if name and hasattr(cmds_shim, name):
            return Result(f"# Error: NameError: {ex} (Maya command? use cmds.{name}(...))", True)
        return Result(f"# Error: NameError: {ex}", True)
    except Exception as ex:
        traceback.print_exc()
        return Result(f"# Error: {type(ex).__name__}: {ex}", True)
    if value is not None:
        return Result(f"# Result: {_format(value)} #")
    printed = out.getvalue().strip().splitlines()
    if printed:
        print(out.getvalue(), end="")  # still reach the system console
        return Result(printed[-1])
    return Result()


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
