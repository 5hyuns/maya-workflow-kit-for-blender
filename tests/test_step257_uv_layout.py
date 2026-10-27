"""Step 257 (Issue #150): UV > Automatic lays shells out like Maya's "Into square" packer
(research/maya/re/autoproj_layout_257.md).

Maya truth = tests/maya257_uv_data.py (mayapy 2026: raw projection with Layout 0 and the factory Layout 2 result on
copies of the same mesh). The packer module is bpy-free; it is fed the raw projected bbox of every shell."""

from importlib import import_module

import kit
from maya257_uv_data import CASES

al = import_module(kit.MODULE + ".operators.autoproj_layout")

TOL = 1e-5


def _run(case):
    shells = case["shells"]
    return al.layout([s["raw"] for s in shells], case["spacing"])


def test_every_shell_bbox_matches_maya():
    worst, bad = 0.0, []
    for name, case in CASES.items():
        lay = _run(case)
        for i, s in enumerate(case["shells"]):
            err = max(abs(a - b) for a, b in zip(lay.bbox(i), s["maya"]))
            worst = max(worst, err)
            if err > TOL:
                bad.append((name, s["face"], err))
    print("cases", len(CASES), "shells", sum(len(c["shells"]) for c in CASES.values()), "worst", worst)
    assert not bad, bad


def test_points_land_where_maya_puts_them():
    """Rotation direction and offsets per point, not only the bbox: the first face of every shell."""
    worst = 0.0
    for name, case in CASES.items():
        lay = _run(case)
        for i, s in enumerate(case["shells"]):
            for (u, v), (mu, mv) in zip(s["raw_uvs"], s["maya_uvs"]):
                fu, fv = lay.transform(i, u, v)
                err = max(abs(fu - mu), abs(fv - mv))
                worst = max(worst, err)
                assert err <= TOL, (name, s["face"], (u, v), (fu, fv), (mu, mv))
    print("worst point error", worst)


def test_issue_150_v_range():
    """#150: the bevelled cylinder chain packs to V 0.001856 - 0.929769 (Maya), not 0.96."""
    lay = _run(CASES["chain150"])
    boxes = [lay.bbox(i) for i in range(len(CASES["chain150"]["shells"]))]
    assert len(boxes) == 6
    assert abs(min(b[1] for b in boxes) - 0.001856) < 1e-5, boxes
    assert abs(max(b[3] for b in boxes) - 0.929769) < 1e-5, boxes
    assert abs(min(b[0] for b in boxes) - 0.001992) < 1e-5 and abs(max(b[2] for b in boxes) - 0.998008) < 1e-5


def test_wide_shells_turn_upright():
    """Rotate mode 1: a shell wider than tall turns 90 degrees (1x2x3 box: both 3x2 sides end 2 wide, 3 tall)."""
    case = CASES["box123_ps0"]
    lay = _run(case)
    turned = [s["face"] for i, s in enumerate(case["shells"]) if lay.rotated(i)]
    assert turned == [4, 5], turned
    for i in range(len(case["shells"])):
        u0, v0, u1, v1 = lay.bbox(i)
        assert v1 - v0 >= u1 - u0 - 1e-6


def test_spacing_border():
    """Percentage Space p: the limiting side keeps a border of p/100 / (1 + 2 p/100) on both ends; p = 0 fills it."""
    for name, p in (("box123_ps0", 0.0), ("box123", 0.2), ("box123_ps1", 1.0)):
        lay = _run(CASES[name])
        boxes = [lay.bbox(i) for i in range(6)]
        m = p / 100.0
        edge = m / (1 + 2 * m)
        assert abs(min(b[1] for b in boxes) - edge) < 1e-6, (name, boxes)
        assert abs(max(b[3] for b in boxes) - (1 - edge)) < 1e-6, (name, boxes)


def test_units_matter():
    """The packer works in Maya units: the same shells given in centimetres-as-metres (x 0.01) pack differently
    (absolute 1e-6 size tolerance, 1.19e-7 area seed), which is why the caller divides by maya_unit()."""
    case = CASES["sphere_ps2"]
    ref = _run(case)
    small = al.layout([[x * 0.01 for x in s["raw"]] for s in case["shells"]], case["spacing"])
    diff = max(abs(a - b) for i in range(len(case["shells"])) for a, b in zip(ref.bbox(i), small.bbox(i)))
    assert diff > 1e-4, diff


def test_empty_and_single():
    assert al.layout([], 0.2).shells == []
    lay = al.layout([(0.0, 0.0, 2.0, 1.0)], 0.2)
    assert lay.rotated(0)
    u0, v0, u1, v1 = lay.bbox(0)
    assert abs(v1 - v0 - 1 / 1.004) < 1e-6 and abs(v0 - 0.002 / 1.004) < 1e-6
