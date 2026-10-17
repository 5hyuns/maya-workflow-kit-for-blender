"""Step 41: the Maya look comparison tools (tools/look_compare.py, look_data.py) compute right.

Only the bpy-free maths and the tables' shape are tested here; the tools themselves need the
Maya reference shots in research/ (untracked) and a GUI Blender (docs/steps/step_41.md).
"""

import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import look_compare as C  # noqa: E402
import look_data as L  # noqa: E402

AUTO_ENABLE = False


def test_ciede2000_reference_pairs():
    # Sharma, Wu, Dalal (2005) test data, pairs 1, 7 and 17
    for lab1, lab2, want in (((50.0, 2.6772, -79.7751), (50.0, 0.0, -82.7485), 2.0425),
                             ((50.0, 0.0, 0.0), (50.0, -1.0, 2.0), 2.3669),
                             ((50.0, 2.5, 0.0), (73.0, 25.0, -18.0), 27.1492)):
        got = C.de2000_lab(lab1, lab2)
        assert abs(got - want) < 1e-3, (lab1, lab2, got, want)
    assert C.de2000((0.3, 0.3, 0.3), (0.3, 0.3, 0.3)) == 0.0
    assert abs(C.de2000((1, 1, 1), (0, 0, 0)) - 100.0) < 0.01
    assert C.hex2rgb(C.rgb2hex((0.2667, 0.2667, 0.2667))) == (68 / 255,) * 3


def test_anchor_resolve():
    rects = {"a": [100, 50, 200, 40], "press": [700, 400, 0, 0]}
    assert L.resolve(rects, "a", 10, 5) == (110, 55)
    assert L.resolve(rects, "a", -20, -6) == (280, 84)        # from right / bottom
    assert L.resolve(rects, "press", -24, -99) == (676, 301)   # point anchor: plain offsets


def test_maya_camera_constants():
    # 35 mm on a 36 mm aperture: horizontal FOV 54.43 deg, focal length in pixels over the GL view
    fov = 2 * math.degrees(math.atan(L.MAYA_APERTURE_MM / 2 / L.MAYA_FOCAL_MM))
    assert abs(fov - 54.43) < 0.01, fov
    assert abs(L.maya_f_px() - (L.MAYA_VIEW_RECT[2] / 2) / math.tan(math.radians(fov / 2))) < 1e-6


def test_tables_shape():
    for name, spec in L.KIT_POINTS.items():
        assert spec[0] is None and isinstance(spec[1], str) or len(spec) == 6, (name, spec)
        if spec[0] is not None:
            shot, anchor, dx, dy, r, note = spec
            assert shot[:2].isdigit() and isinstance(anchor, str) and r in (0, 1, 2), (name, spec)
    anchors = {a for _w, a, _l in L.RECTS}
    assert {"topbar", "statusbar", "view3d.UI", "outliner"} <= anchors
    assert all(how in ("side", "over") for *_x, how in L.CROPS)
    assert set(L.CUBE_FITS) == {"02_cube_selected_move", "04_wire_selected_lead", "07_faces_selected"}


def test_colour_bbox_and_sample():
    import numpy as np
    img = np.zeros((50, 80, 3), np.float32)
    img[10:20, 30:45] = (0x43 / 255, 1.0, 0xa3 / 255)       # a lead-green block
    img[40, 70] = (0x43 / 255, 1.0, 0xa3 / 255)             # outside the search rect
    assert L.colour_bbox(img, "#43ffa3", (0, 0, 60, 50)) == [30, 10, 44, 19]
    assert L.colour_bbox(img, "#ff0000", (0, 0, 60, 50)) is None
    got = L.sample(img, 35, 15)
    assert all(abs(a - b) < 1e-6 for a, b in zip(got, (0x43 / 255, 1.0, 0xa3 / 255))), got
