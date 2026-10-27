"""QA 240 C: action executor, pairwise rows, random walk, shrinking and repro writing (engine, no test_* here)."""

import json
import random
import re
import time
import traceback
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import bpy

_HERE = Path(__file__).resolve().parent


def _load(name):
    spec = spec_from_file_location(name, _HERE / f"{name}.py")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


core = _load("qa_c_core")

# Classes already reported by qa_toggles.py (table): skipped in the random walk so new classes show (count kept).
KNOWN = (
    r"step_(TRANSLATE|ROTATE|RESIZE).*changed step_(TRANSLATE|ROTATE|RESIZE)",   # one tool's Step Snap moves another's
    r"after the setup clicks step_",
)

CLASSES = KNOWN + (r"shows Off but Blender steps",)

SEVERITY = {"I1": "S2", "I2": "S2", "I3": "S3", "I4": "S2", "I5": "S3", "EXC": "S2", "E": "S2", "ROW": "S3"}


def signature(oracle, msg):
    return oracle + ":" + re.sub(r"[-\d.]+", "#", msg)[:110]


class Run:
    """Executes an action list from a fresh scene and collects (index, oracle, message)."""

    def __init__(self, stop_at=None, ignore_known=False):
        self.found = []
        self.known = 0
        self.stop_at = stop_at        # a signature: stop as soon as it is seen
        self.ignore_known = ignore_known

    def add(self, i, oracle, msg):
        if self.ignore_known and any(re.search(k, msg) for k in KNOWN):
            self.known += 1
            return
        self.found.append((i, oracle, msg))
        if self.stop_at is not None and signature(oracle, msg) == self.stop_at:
            raise _Stop()

    def start(self):
        if not core.switch._registered[0]:
            core.switch.set_mode(True, layout=False)
        core.build_scene()
        core.reset_toggles()
        bpy.ops.ed.undo_push(message="qa start")

    def act(self, i, a):
        kind = a[0]
        before = core.ui_state()
        if kind == "click":
            t = core.BY_NAME[a[1]]
            core.log(i, "click", a[1], a[2] if len(a) > 2 else None)
            t.click(a[2] if len(a) > 2 else None)
            bpy.ops.ed.undo_push(message=f"qa {a[1]}")
            after = core.ui_state()
            twins = {t.name, "soft_select"} if t.name.startswith("soft") else {t.name}
            for k in after:
                if k not in twins and after[k] != before[k]:
                    self.add(i, "I3", f"click {t.name} changed {k}: {before[k]} -> {after[k]}")
        elif kind == "double":
            t = core.BY_NAME[a[1]]
            core.log(i, "double", a[1])
            if t.values == (False, True):
                t.click()
                t.click()
            else:
                orig = before[t.name] if t.name != "symmetry" else None
                if t.name == "symmetry":
                    t.click("TOGGLE")
                    t.click("TOGGLE")
                else:
                    other = next(v for v in t.values if v != orig)
                    t.click(other)
                    t.click(orig)
            bpy.ops.ed.undo_push(message=f"qa double {a[1]}")
            after = core.ui_state()
            for k in after:
                if after[k] != before[k]:
                    self.add(i, "I2", f"{t.name} clicked there and back changed {k}: {before[k]} -> {after[k]}")
        elif kind == "mode":
            core.log(i, "mode", a[1])
            core.mode_switch(a[1])
            bpy.ops.ed.undo_push(message=f"qa mode {a[1]}")
        elif kind == "undo":
            core.log(i, "undo")
            try:
                bpy.ops.ed.undo()
            except RuntimeError:
                pass
        elif kind == "redo":
            core.log(i, "redo")
            try:
                bpy.ops.ed.redo()
            except RuntimeError:
                pass
        elif kind == "undo_redo":
            core.log(i, "undo_redo")
            if core.C().object is not None and core.C().object.mode == 'OBJECT':
                s0 = core.scene_state()
                try:
                    bpy.ops.ed.undo()
                    bpy.ops.ed.redo()
                except RuntimeError:
                    return
                s1 = core.scene_state()
                for k in s0:
                    if s0[k] != s1[k]:
                        self.add(i, "I5", f"undo+redo changed {k}: {s0[k]} -> {s1[k]}")
        elif kind == "save_reopen":
            core.log(i, "save_reopen")
            s0 = core.scene_state()
            sess0 = {k: v for k, v in before.items() if k not in s0}
            core.save_reopen()
            s1 = core.scene_state()
            for k in s0:
                if s0[k] != s1[k]:
                    self.add(i, "I4", f"save+reopen changed {k}: {s0[k]} -> {s1[k]}")
            after = core.ui_state()
            for k in sess0:
                if after[k] != sess0[k]:
                    self.add(i, "I4", f"save+reopen changed session toggle {k}: {sess0[k]} -> {after[k]}")
        elif kind == "maya_off_on":
            core.log(i, "maya_off_on")
            s0 = core.ui_state()
            core.maya_off_on()
            s1 = core.ui_state()
            for k in s0:
                if s0[k] != s1[k]:
                    self.add(i, "I4", f"Maya mode off/on changed {k}: {s0[k]} -> {s1[k]}")
        elif kind == "expect":
            core.log(i, "expect")
            ui = core.ui_state()
            for k, v in a[1].items():
                got = ui[k][0] if k == "symmetry" else ui[k]
                if got != v:
                    self.add(i, "ROW", f"after the setup clicks {k} shows {got}, asked {v}")
        elif kind == "autokey_effect":
            core.log(i, "autokey_effect")
            for msg in core.autokey_effect():
                self.add(i, "E", msg)
        for msg in core.all_violations():
            self.add(i, "E" if "effect" in msg else "I1", msg)

    def run(self, actions):
        try:
            self.start()
            for i, a in enumerate(actions):
                try:
                    self.act(i, a)
                except _Stop:
                    raise
                except Exception as ex:
                    tb = traceback.format_exc()
                    if isinstance(ex, core.Violation):
                        self.add(i, "E", str(ex))
                    else:
                        self.add(i, "EXC", f"{type(ex).__name__}: {ex} | {_kit_frame(tb)}")
        except _Stop:
            pass
        return self.found


class _Stop(Exception):
    pass


def _kit_frame(tb):
    frames = re.findall(r'File "([^"]+)", line (\d+)', tb)
    kit_frames = [f"{Path(f).name}:{n}" for f, n in frames if "allset" in f and "qa" not in Path(f).parts]
    return kit_frames[-1] if kit_frames else (f"{Path(frames[-1][0]).name}:{frames[-1][1]}" if frames else "?")


def reproduces(actions, sig):
    found = Run(stop_at=sig).run(actions)
    return any(signature(o, msg) == sig for _i, o, msg in found)


def shrink(actions, sig, budget_s=40.0):
    t0 = time.time()
    cur = list(actions)
    # drop from the front while it still fails
    changed = True
    while changed and time.time() - t0 < budget_s:
        changed = False
        n = max(1, len(cur) // 4)
        while n >= 1 and time.time() - t0 < budget_s:
            for start in range(0, len(cur), n):
                cand = cur[:start] + cur[start + n:]
                if cand and reproduces(cand, sig):
                    cur = cand
                    changed = True
                    break
            else:
                n //= 2
                continue
            break
    return cur


def write_repro(name, actions, sig, oracle_msg):
    path = _HERE / f"{name}.py"
    path.write_text(
        '"""QA 240 C repro (generated by tools/qa/qa_c_walk.py): ' + oracle_msg.replace('"""', "'") + '\n\n'
        'Run: ALLSET_SANDBOX=qa_c python tests/run.py --no-build -k __none__ --extra tools/qa/' + path.name + '\n"""\n'
        "from importlib.util import module_from_spec, spec_from_file_location\n"
        "from pathlib import Path\n\n"
        "_spec = spec_from_file_location('qa_c_walk', Path(__file__).resolve().parent / 'qa_c_walk.py')\n"
        "walk = module_from_spec(_spec)\n_spec.loader.exec_module(walk)\n\n"
        f"ACTIONS = {json.dumps(actions)}\nSIGNATURE = {json.dumps(sig)}\n\n\n"
        "def test_repro():\n"
        "    found = walk.Run().run([tuple(a) for a in ACTIONS])\n"
        "    hits = [f for f in found if walk.signature(f[1], f[2]) == SIGNATURE]\n"
        "    assert not hits, hits[0]\n",
        encoding="utf-8")
    return path


# ---------------------------------------------------------------------------------------- generators

def random_actions(seed, n):
    rng = random.Random(seed)
    names = [t.name for t in core.TOGGLES]
    acts = []
    for _ in range(n):
        r = rng.random()
        if r < 0.55:
            t = core.BY_NAME[rng.choice(names)]
            if t.values == (False, True):
                acts.append(("click", t.name))
            else:
                acts.append(("click", t.name, rng.choice(t.values)))
        elif r < 0.65:
            acts.append(("double", rng.choice(names)))
        elif r < 0.75:
            acts.append(("mode", rng.choice(("OBJECT", "EDIT_MESH", "POSE", "HANDLE"))))
        elif r < 0.82:
            acts.append((rng.choice(("undo", "redo")),))
        elif r < 0.88:
            acts.append(("undo_redo",))
        elif r < 0.92:
            acts.append(("save_reopen",))
        elif r < 0.94:
            acts.append(("maya_off_on",))
        else:
            acts.append(("autokey_effect",))
    return acts


FACTORS = {
    "snap_GRID": (False, True), "snap_POINT": (False, True), "snap_CURVE": (False, True),
    "step_TRANSLATE": core.STEP_MODES, "step_ROTATE": core.STEP_MODES, "step_RESIZE": core.STEP_MODES,
    "symmetry": ("OFF", "OBJECT_X", "WORLD_Y", "TOPOLOGY"),
    "soft_select": (False, True), "auto_key": (False, True), "menu_set": tuple(core.SET_IDS),
    "layer_mute": (False, True), "layer_solo": (False, True), "ik_solver": (False, True),
    "context": ("OBJECT", "EDIT_MESH", "POSE", "HANDLE"), "file": ("new", "reopened"),
}


def allpairs(factors, seed=240, tries=60):
    """Greedy all-pairs: pick, among random candidates, the row covering most uncovered pairs."""
    rng = random.Random(seed)
    keys = list(factors)
    todo = {(a, va, b, vb) for i, a in enumerate(keys) for b in keys[i + 1:]
            for va in factors[a] for vb in factors[b]}
    rows = []
    while todo:
        # seed the candidate with one uncovered pair so every row makes progress
        a, va, b, vb = next(iter(sorted(todo, key=str)))
        best, best_n = None, -1
        for _ in range(tries):
            row = {k: rng.choice(factors[k]) for k in keys}
            row[a], row[b] = va, vb
            n = sum(1 for i, x in enumerate(keys) for y in keys[i + 1:] if (x, row[x], y, row[y]) in todo)
            if n > best_n:
                best, best_n = row, n
        rows.append(best)
        todo -= {(x, best[x], y, best[y]) for i, x in enumerate(keys) for y in keys[i + 1:]}
    return rows


def row_actions(row):
    acts = []
    for k in ("snap_GRID", "snap_POINT", "snap_CURVE", "soft_select", "auto_key", "layer_mute", "layer_solo"):
        acts.append(("click", k, row[k]))
    for k in ("step_TRANSLATE", "step_ROTATE", "step_RESIZE"):
        acts.append(("click", k, row[k]))
    acts.append(("click", "symmetry", row["symmetry"]))
    acts.append(("click", "menu_set", row["menu_set"]))
    if row["ik_solver"]:
        acts.append(("mode", "HANDLE"))
        acts.append(("click", "ik_solver", True))
    acts.append(("expect", expected_after_setup(row)))
    acts.append(("mode", row["context"]))
    if row["file"] == "reopened":
        acts.append(("save_reopen",))
    if row["context"] == "OBJECT":
        acts.append(("autokey_effect",))
    for t in core.TOGGLES:
        if t.name != "ik_solver":
            acts.append(("double", t.name))
    return acts


def expected_after_setup(row):
    """The UI each row asked for (checked right after the setup clicks)."""
    return {k: row[k] for k in row if k not in ("context", "file", "ik_solver")}
