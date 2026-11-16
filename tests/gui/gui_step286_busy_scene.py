"""#191: in a real UI: the Maya Workflow Kit layout with a busy scene (a 102k-vertex grid skinned to a
120-bone chain + 600 cubes, the qa_perf scene; the grid selected). For a few seconds one unselected cube is moved every
20 ms while the views redraw; a profiler records every Python call in that time (timers, draw handlers, depsgraph
handlers, panels). The same is done again after the 600 cubes are deleted. Reported: kit Python time per 3D View redraw
and the top kit functions (``tmp/s286/profile_<tag>.txt``). Checked: the 600 extra objects add less than ``BUDGET_MS``
of kit Python per 3D View redraw (time under the profiler, which slows Python down by about 2x; before the speed-up the
600 objects added 3.6 ms).

The two timings differ only in the object count:

- Viewport anti-aliasing is off while timing, so each move redraws the view once in both. With it on, Blender redraws a
  view again after a change until its samples are done: 1.6 - 2.5 times per move with few objects but 1.1 - 1.7 times
  in the busy scene, and the kit's once-per-move work (Channel Box, dock, Tool Box), divided by fewer redraws, alone
  made the figure 1.2 - 2.8 ms.
- The same selection in both (the grid selected and active, the moved cube not), so the Channel Box, Attribute Editor
  and dock draw the same.
- Other programs can slow the machine down between the two timings (by up to 20 %): the few-objects figure is scaled by
  the speed change, the time-weighted median of the kit functions' time ratios between the two timings over the
  functions called as often in both (nearly all of them do the same work in both)."""

import cProfile
import os
import pstats
import sys
import time
from pathlib import Path

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, setup, step, win  # noqa: E402

GUI_TIMEOUT = 240
ROOT = Path(__file__).resolve().parents[2]
TAG = os.environ.get("ALLSET_PROFILE_TAG", "current")
OUT = ROOT / "tmp" / "s286" / f"profile_{TAG}.txt"
BUDGET_MS = 1.0         # extra kit Python per 3D View redraw for 600 more objects (profiled time)
MOVES = 150
C = {}


def kit_file(path):
    p = path.replace("\\", "/")
    return "/allset/" in p and "/tests/" not in p


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    sys.path.insert(0, str(ROOT / "tests"))
    sys.path.insert(0, str(ROOT / "tools" / "qa"))
    import qa_perf
    qa_perf.build_scene()
    C["n"] = len(bpy.context.scene.objects)
    check(f"busy scene built ({C['n']} objects)", C["n"] > 600)


def _settle():
    for a in win().screen.areas:
        a.tag_redraw()


def _wait_icons():
    """Menu / shelf icons are made once after start (timers): not part of the timing. Wait until the menu icon
    timer is done (up to 40 ticks), then a few more redraws for the shelf icons."""
    import sim
    from importlib import import_module
    menu_icons = import_module(MODULE + ".ui.menu_icons")
    C["waits"] = C.get("waits", 0) + 1
    _settle()
    if bpy.app.timers.is_registered(menu_icons._tick) and C["waits"] < 40:
        sim._steps.insert(0, _wait_icons)


step(_wait_icons)
for _ in range(5):
    step(_settle)


def _start(phase, name):
    prof = cProfile.Profile()
    rec = C[phase] = {"prof": prof, "i": 0, "t0": time.perf_counter()}
    ob = bpy.data.objects[name]

    def mover():
        i = rec["i"]
        if i >= MOVES:
            rec["t1"] = time.perf_counter()
            prof.disable()
            return None
        ob.location.x = (i % 20) * 0.1
        for a in win().screen.areas:         # like a drag in the view: Blender's notifiers redraw the rest
            if a.type == 'VIEW_3D':
                a.tag_redraw()
        rec["i"] = i + 1
        return 0.02
    system = bpy.context.preferences.system
    C.setdefault("aa", system.viewport_aa)
    system.viewport_aa = 'OFF'           # one view redraw per move (module docstring)
    prof.enable()
    bpy.app.timers.register(mover, first_interval=0.02)


def _report(phase):
    rec = C[phase]
    if "t1" not in rec:
        rec["prof"].disable()
        rec["t1"] = time.perf_counter()
    bpy.context.preferences.system.viewport_aa = C["aa"]
    wall = rec["t1"] - rec["t0"]
    st = pstats.Stats(rec["prof"])
    kit_total, rows, draws, funcs = 0.0, [], 0, {}
    for (fname, line, func), (_cc, nc, tt, ct, _callers) in st.stats.items():
        if kit_file(fname) and fname.replace("\\", "/").endswith("ui/view_furniture.py") and func == "draw":
            draws = max(draws, nc)        # one call per 3D View region redraw (ViewCube / HUD)
        if kit_file(fname):
            kit_total += tt
            funcs[(fname, line, func)] = (nc, tt)
            rows.append((ct, tt, f"{Path(fname).relative_to(Path(fname).parents[1])}:{line}({func})"))
    rows.sort(reverse=True)
    rec["draws"] = draws
    rec["funcs"] = funcs
    rec["per_move"] = kit_total * 1000 / max(draws, 1)
    rec["text"] = (f"{phase}: objects {len(bpy.context.scene.objects)} moves {rec['i']} wall {wall:.3f} s kit "
                   f"{kit_total * 1000:.1f} ms / {draws} view redraws = {rec['per_move']:.2f} ms per redraw\n"
                   + "".join(f"{ct * 1000:10.1f} {tt * 1000:9.1f}  {n}\n" for ct, tt, n in rows[:30]))
    check(f"{phase}: {rec['i']} moves done ({wall:.2f} s, kit {rec['per_move']:.2f} ms per view redraw)",
          rec["i"] >= MOVES and draws > 0)


def _wait():
    pass


@step
def s_start_many():
    _start("many", "c0")


for _ in range(12):          # 12 × 0.4 s: enough for 150 moves at 20 ms plus redraws
    step(_wait)


@step
def s_report_many():
    _report("many")
    shots = os.environ.get("ALLSET_GUI_SHOTS", "")
    if shots:
        with bpy.context.temp_override(window=win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(shots, "gui_step286_busy.png"))
    cubes = [o for o in bpy.data.objects if o.name.startswith("c") and o.name[1:].isdigit()]
    bpy.data.batch_remove(cubes)
    bpy.ops.mesh.primitive_cube_add(size=0.2)
    mover = bpy.context.active_object
    mover.name = "mover"
    mover.select_set(False)             # the selection of the busy scene: the grid selected and active
    heavy = bpy.data.objects["heavy"]
    heavy.select_set(True)
    bpy.context.view_layer.objects.active = heavy


for _ in range(5):
    step(_settle)


@step
def s_start_few():
    _start("few", "mover")


for _ in range(12):
    step(_wait)


def speed_factor(many, few):
    """How much slower the machine ran the busy-scene timing than the few-objects one: the median, weighted by time, of
    each kit function's time ratio between the two, over the functions called as often in both (within 5 %) that take
    at least 5 us a move. A function slowed down by the object count is one of many and leaves the median alone."""
    pairs = []
    for key, (n_few, t_few) in few["funcs"].items():
        n_many, t_many = many["funcs"].get(key, (0, 0.0))
        if n_few and abs(n_many - n_few) <= 0.05 * n_few and t_few >= 5e-6 * few["i"] and t_many > 0:
            pairs.append((t_many / t_few, t_few))
    pairs.sort()
    half, acc = sum(w for _r, w in pairs) / 2, 0.0
    for ratio, weight in pairs:
        acc += weight
        if acc >= half:
            return ratio
    return 1.0


@step
def s_report_few():
    _report("few")
    many, few = C["many"], C["few"]
    check(f"both timings redraw the view as often ({many['draws']} and {few['draws']} redraws for {MOVES} moves)",
          abs(many["draws"] - few["draws"]) <= 0.1 * few["draws"])
    factor = speed_factor(many, few)
    extra = many["per_move"] - factor * few["per_move"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(f"tag {TAG} blender {bpy.app.version_string}; 600 more objects add {extra:.2f} ms kit Python per "
                 f"view redraw (few-objects figure x {factor:.3f} for the machine's speed)\n"
                 f"cumulative ms  self ms  function\n" + many["text"] + few["text"])
    print(f"PROFILE many {many['per_move']:.2f} few {few['per_move']:.2f} ms per view redraw, speed x {factor:.3f} "
          f"-> {OUT}", flush=True)
    check(f"600 more objects add {extra:.2f} ms kit Python per view redraw (budget {BUDGET_MS:.2f} ms; few objects "
          f"x {factor:.2f} for the machine's speed)", extra < BUDGET_MS)


run()
