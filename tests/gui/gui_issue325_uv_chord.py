"""#325 (UV Editor): with Alt held, the left and the middle button together zoom like Alt+RMB, whichever button comes
first, like Maya's UV Editor. Letting go of either button holds the view still; pressing it again zooms again.
Alt+RMB: a drag right or down zooms in, left or up zooms out, so a right+up drag does nothing. Alt+LMB and Alt+MMB
alone pan."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import load_maya_layout, run, setup, step, view3d  # noqa: E402
from chord2d import C, D, add_case, like, override, panned, still, unchanged, zoomed  # noqa: E402

GUI_TIMEOUT = 300
C["tag"] = "uv"


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    area, _reg = view3d()
    C["area"] = area
    area.ui_type = 'UV'


def frame():
    with override():
        bpy.ops.image.view_all()


C["frame"] = frame
step(lambda: None)

# references: Alt+RMB zoom, the Alt+MMB pan
add_case("altR_h", [('press', 'RIGHTMOUSE'), ('move', D, 0)], verify=zoomed("Alt+RMB right"))
add_case("altR_dn", [('press', 'RIGHTMOUSE'), ('move', 0, -D)], verify=zoomed("Alt+RMB down"))
add_case("altR_l", [('press', 'RIGHTMOUSE'), ('move', -D, 0)], verify=zoomed("Alt+RMB left", inward=False))
add_case("altR_v", [('press', 'RIGHTMOUSE'), ('move', 0, D)], verify=zoomed("Alt+RMB up", inward=False))
add_case("altR_d", [('press', 'RIGHTMOUSE'), ('move', D, D)], verify=unchanged("Alt+RMB right+up (they cancel)"))
add_case("altM_h", [('press', 'MIDDLEMOUSE'), ('move', D, 0)], verify=panned("Alt+MMB"))
add_case("altL_h", [('press', 'LEFTMOUSE'), ('move', D, 0)],
         verify=[panned("Alt+LMB"), like("altM_h", "Alt+LMB pans like Alt+MMB")])
add_case("zoom_zoom", [('press', 'RIGHTMOUSE'), ('move', D, 0), ('release', 'RIGHTMOUSE'), ('press', 'RIGHTMOUSE'),
                       ('move', D, 0)])
# the chord
add_case("chordLM_h", [('press', 'LEFTMOUSE'), ('press', 'MIDDLEMOUSE'), ('move', D, 0)],
         verify=like("altR_h", "Alt+LMB then MMB, drag right"))
add_case("chordML_h", [('press', 'MIDDLEMOUSE'), ('press', 'LEFTMOUSE'), ('move', D, 0)],
         verify=like("altR_h", "Alt+MMB then LMB, drag right"))
add_case("chordLM_v", [('press', 'LEFTMOUSE'), ('press', 'MIDDLEMOUSE'), ('move', 0, D)],
         verify=like("altR_v", "Alt+LMB+MMB, drag up"))
add_case("chordML_d", [('press', 'MIDDLEMOUSE'), ('press', 'LEFTMOUSE'), ('move', D, D)],
         verify=unchanged("Alt+MMB+LMB, drag right+up"))
# letting go of one button: the view stops either way
add_case("chord_relL", [('press', 'MIDDLEMOUSE'), ('press', 'LEFTMOUSE'), ('move', D, 0), ('snap', 'zoomed'),
                        ('release', 'LEFTMOUSE'), ('move', D, 0)],
         verify=[like("altR_h", "zoom before letting go of LMB"),
                 still("MMB, LMB, drag, let go of LMB, drag", "zoomed")])
add_case("chord_relM", [('press', 'LEFTMOUSE'), ('press', 'MIDDLEMOUSE'), ('move', D, 0), ('snap', 'zoomed'),
                        ('release', 'MIDDLEMOUSE'), ('move', D, 0)],
         verify=still("LMB, MMB, drag, let go of MMB, drag", "zoomed"))
add_case("chord_again", [('press', 'MIDDLEMOUSE'), ('press', 'LEFTMOUSE'), ('move', D, 0), ('release', 'LEFTMOUSE'),
                         ('press', 'LEFTMOUSE'), ('move', D, 0)],
         verify=like("zoom_zoom", "zoom, let go of LMB, press it again: zooms again"))
add_case("chord_relM_again", [('press', 'LEFTMOUSE'), ('press', 'MIDDLEMOUSE'), ('move', D, 0),
                              ('release', 'MIDDLEMOUSE'), ('press', 'MIDDLEMOUSE'), ('move', D, 0)],
         verify=like("zoom_zoom", "zoom, let go of MMB, press it again: zooms again"))

run()
