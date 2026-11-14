"""Issue #176: "name '__annotations__' is not defined" right after install on CachyOS (Blender 5.2.3 built
against the system Python 3.14).

Python 3.14 evaluates annotations lazily (PEP 649 / 749): a class body has no ``__annotations__`` name any more, so
``__annotations__.update(...)`` inside a class body raises NameError while the module imports (the extension then
fails to register although Blender lists it as installed), and ``cls.__dict__`` holds ``__annotate__`` instead of
``__annotations__``. The kit reads class annotations through ``compat.own_annotations``."""

import ast
import os
import shutil
import subprocess
from importlib import import_module
from pathlib import Path

import bpy

import kit

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "allset"
compat = import_module(kit.MODULE + ".compat")


class _ClassBodyReads(ast.NodeVisitor):
    """``__annotations__`` read inside a class body (assignment ``__annotations__ = {...}`` is fine on 3.14)."""

    def __init__(self):
        self.hits = []
        self.depth = 0

    def visit_ClassDef(self, node):
        self.depth += 1
        for stmt in node.body:
            self.visit(stmt)
        self.depth -= 1

    def visit_FunctionDef(self, node):
        depth, self.depth = self.depth, 0       # a method body is not the class namespace
        self.generic_visit(node)
        self.depth = depth

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_Lambda = visit_FunctionDef

    def visit_Name(self, node):
        if self.depth and node.id == "__annotations__" and isinstance(node.ctx, ast.Load):
            self.hits.append(node.lineno)


def _sources():
    for path in SRC.rglob("*.py"):
        yield path, path.read_text(encoding="utf-8")


def test_no_python_3_14_annotation_reads():
    bad = []
    for path, text in _sources():
        v = _ClassBodyReads()
        v.visit(ast.parse(text))
        bad += [f"{path.relative_to(SRC)}:{n} reads __annotations__ in a class body" for n in v.hits]
        for n, line in enumerate(text.splitlines(), 1):
            if '__dict__.get("__annotations__"' in line or "__dict__.get('__annotations__'" in line:
                if path.name != "compat.py":
                    bad.append(f"{path.relative_to(SRC)}:{n} reads __dict__['__annotations__'] (empty on 3.14)")
    assert not bad, bad


def test_own_annotations_and_merged_classes():
    class Base:
        a: int

    class Child(Base):
        b: str
    assert set(compat.own_annotations(Base)) == {"a"} and set(compat.own_annotations(Child)) == {"b"}
    wp = import_module(kit.MODULE + ".operators.weight_paint")
    ann = wp.ALLSET_PG_weight_workspace.__annotations__
    assert "show_numbers" in ann and all(k.lower() in ann for k in wp.ACTIONS), sorted(ann)
    assert isinstance(bpy.context.window_manager.allset_weight_workspace.transfer, bpy.types.PropertyGroup)
    # undo_steps.no_redo_panel keeps the inherited operator properties (hidden), e.g. the extrude edit operator
    ex = import_module(kit.MODULE + ".operators.extrude")
    props = bpy.ops.allset.extrude_edit.get_rna_type().properties
    assert "local_translate_z" in props and props["local_translate_z"].is_hidden, list(props.keys())


def _is_3_14(exe):
    try:
        out = subprocess.run([exe, "-I", "-c", "import sys; print(sys.version_info[:2])"], capture_output=True,
                             text=True, timeout=30, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return False
    return out.returncode == 0 and out.stdout.strip() == "(3, 14)"


def _python_3_14():
    """A Python 3.14 interpreter: $ALLSET_PY314 (must be one), else python3.14 on PATH, the py launcher or a
    uv-managed Python. None when the machine has none."""
    exe = os.environ.get("ALLSET_PY314")
    if exe:
        assert _is_3_14(exe), f"ALLSET_PY314 is not a Python 3.14 interpreter: {exe}"
        return exe
    found = shutil.which("python3.14")
    if found and _is_3_14(found):
        return found
    for tool, args in (("py", ["-3.14", "-c", "import sys; print(sys.executable)"]),
                       ("uv", ["python", "find", "--no-project", "3.14"])):
        path = shutil.which(tool)
        if path is None:
            continue
        try:
            out = subprocess.run([path, *args], capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
        except (OSError, subprocess.SubprocessError):
            continue
        cand = out.stdout.strip().splitlines()[-1].strip() if out.returncode == 0 and out.stdout.strip() else ""
        if cand and _is_3_14(cand):
            return cand
    return None


# The kit's class patterns, outside Blender: the old one must fail on 3.14 (the reported error), the new ones work.
_PROBE = r'''
import ast, sys
text = open(sys.argv[1], encoding="utf-8").read()
fn = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == "own_annotations")
ns = {}
exec(compile(ast.Module([fn], []), sys.argv[1], "exec"), ns)    # only compat.own_annotations (no bpy here)
own = ns["own_annotations"]
try:
    class Old:
        x: int
        __annotations__.update({"y": int})
    old = "ok"
except NameError as e:
    old = str(e)
class New:
    x: int
New.__annotations__ = {**own(New), "y": int}
class Base:
    a: int
class Child(Base):
    b: str
merged = {}
for base in reversed(Child.__mro__):
    if base is not object:
        merged.update(own(base))
print(sys.version_info[:2], repr(old), sorted(New.__annotations__), sorted(merged))
'''


def test_patterns_on_python_3_14():
    exe = _python_3_14()
    if exe is None:
        raise kit.Skip("no Python 3.14 interpreter (set ALLSET_PY314, or install one: uv python install 3.14)")
    print("Python 3.14:", exe)
    probe = ROOT / "tmp" / "s259_probe.py"
    probe.parent.mkdir(exist_ok=True)
    probe.write_text(_PROBE, encoding="utf-8")
    out = subprocess.run([exe, "-I", str(probe), str(SRC / "compat.py")], capture_output=True, text=True,
                         timeout=60, stdin=subprocess.DEVNULL)
    print(out.stdout, out.stderr)
    assert out.returncode == 0, out.stderr
    assert "(3, 14)" in out.stdout
    assert "name '__annotations__' is not defined" in out.stdout, "the reported error reproduces on 3.14"
    assert "['x', 'y'] ['a', 'b']" in out.stdout, out.stdout
