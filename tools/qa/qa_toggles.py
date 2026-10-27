"""QA 240 activity C (part 1): toggle table + pairwise matrix. Headless harness run by tests/run.py:

    ALLSET_SANDBOX=qa_c python tests/run.py --no-build -k __none__ --extra tools/qa/qa_toggles.py

Part 2 (seeded random walk): tools/qa/qa_toggles_walk.py. Engine: qa_c_core.py / qa_c_walk.py.
Results: tmp/qa240/qa_c.json (merged per sandbox tag), findings: tmp/qa240/findings.jsonl.
"""

import json
import time
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_spec = spec_from_file_location("qa_c_walk", Path(__file__).resolve().parent / "qa_c_walk.py")
walk = module_from_spec(_spec)
_spec.loader.exec_module(walk)
core = walk.core

RESULTS = {"table": None, "pairwise": None}
_seen = set()


def _merge(part, data):
    path = core.OUT / "qa_c.json"
    try:
        allr = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        allr = {}
    allr.setdefault(f"{core.TAG} {core.VERSION}", {})[part] = data
    path.write_text(json.dumps(allr, indent=1), encoding="utf-8")


def _report(found, actions, label, shrink_budget):
    out = []
    for i, oracle, msg in found:
        sig = walk.signature(oracle, msg)
        cls = next((k for k in walk.CLASSES if __import__("re").search(k, msg)), sig)   # one finding per root cause
        if cls in _seen:
            continue
        _seen.add(cls)
        prefix = actions[:i + 1]
        small = walk.shrink(prefix, sig, budget_s=shrink_budget) if shrink_budget else prefix
        name = f"repro_c_{label}_{len(_seen)}"
        path = walk.write_repro(name, [list(a) for a in small], sig, msg)
        rec = core.finding(f"C-{core.TAG}-{label}-{len(_seen)}", walk.SEVERITY.get(oracle, "S3"),
                           f"tools/qa/{path.name}", oracle, msg)
        rec["actions"] = len(small)
        out.append(rec)
        core.log("FINDING", oracle, msg, "->", path.name, len(small), "actions")
    return out


def test_table():
    """Each toggle alone, in Object / Edit / Pose: click there and back + ui == rna after every click."""
    acts = []
    for ctx in ("OBJECT", "EDIT_MESH", "POSE", "HANDLE"):
        acts.append(("mode", ctx))
        for t in core.TOGGLES:
            if t.values == (False, True):
                acts += [("click", t.name), ("click", t.name)]
            else:
                acts += [("click", t.name, v) for v in t.values]
            acts.append(("double", t.name))
        acts.append(("save_reopen",))
        acts.append(("undo_redo",))
    t0 = time.time()
    found = walk.Run().run(acts)
    recs = _report(found, acts, "table", 20.0)
    RESULTS["table"] = {"actions": len(acts), "violations": len(found), "unique": len(recs), "findings": recs,
                        "seconds": round(time.time() - t0, 1)}
    _merge("table", RESULTS["table"])


def test_pairwise():
    rows = walk.allpairs(walk.FACTORS)
    core.log("pairwise rows", len(rows))
    t0 = time.time()
    total, viol, recs = 0, 0, []
    for r, row in enumerate(rows):
        acts = walk.row_actions(row)
        total += len(acts)
        found = walk.Run().run(acts)
        viol += len(found)
        recs += _report(found, acts, f"pair{r}", 15.0 if time.time() - t0 < 150 else 0)
    RESULTS["pairwise"] = {"rows": len(rows), "actions": total, "violations": viol, "unique": len(recs),
                           "findings": recs, "seconds": round(time.time() - t0, 1)}
    _merge("pairwise", RESULTS["pairwise"])


def test_zero_violations():
    bad = [f for part in RESULTS.values() if part for f in part["findings"]]
    assert not bad, f"{len(bad)} unique violation(s): " + " | ".join(f["detail"][:120] for f in bad[:6])
