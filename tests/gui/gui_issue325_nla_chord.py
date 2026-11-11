"""#325 (NLA editor, the kit's Time Editor / Trax Editor): with Alt held, the left and the middle button together zoom
the time axis like Alt+RMB, whichever button comes first, like Maya's Trax Editor. Letting go of the left button
carries on panning with the middle one; letting go of the middle one holds the view still; pressing the button again
zooms again. Alt+RMB zooms by the left / right drag; an up / down drag does nothing. Alt+MMB / Alt+LMB pan as before."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import load_maya_layout, run, setup, step, view3d, win  # noqa: E402
from chord2d import C, D, add_case, like, override, panned, still, unchanged, zoomed  # noqa: E402

GUI_TIMEOUT = 300
C["tag"] = "nla"


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    area, reg = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=reg):
        bpy.ops.allset.create(kind='CUBE')
    ob = bpy.data.objects["pCube1"]
    for f, v in ((1, 0.0), (12, 10.0), (48, 4.0)):
        ob.location.x = v
        ob.keyframe_insert("location", index=0, frame=f)
    ad = ob.animation_data
    action = ad.action
    track = ad.nla_tracks.new()
    track.strips.new("chord", 1, action)
    ad.action = None
    bpy.context.scene.frame_set(1)
    C["area"] = area
    area.ui_type = 'NLA_EDITOR'


def frame():
    with override():
        bpy.ops.nla.view_all()


C["frame"] = frame
step(lambda: None)

# references: Blender's Alt+RMB zoom, the Alt+MMB / Alt+LMB pan
add_case("altR_h", [('press', 'RIGHTMOUSE'), ('move', D, 0)], verify=zoomed("Alt+RMB right", y_too=False))
add_case("altR_v", [('press', 'RIGHTMOUSE'), ('move', 0, D)], verify=unchanged("Alt+RMB up"))
add_case("altR_d", [('press', 'RIGHTMOUSE'), ('move', D, D)], verify=like("altR_h", "Alt+RMB right+up = right"))
add_case("altM_h", [('press', 'MIDDLEMOUSE'), ('move', D, 0)], verify=panned("Alt+MMB"))
add_case("altL_h", [('press', 'LEFTMOUSE'), ('move', D, 0)], verify=panned("Alt+LMB"))
add_case("zoom_pan", [('press', 'RIGHTMOUSE'), ('move', D, 0), ('release', 'RIGHTMOUSE'), ('press', 'MIDDLEMOUSE'),
                      ('move', D, 0)])
add_case("zoom_zoom", [('press', 'RIGHTMOUSE'), ('move', D, 0), ('release', 'RIGHTMOUSE'), ('press', 'RIGHTMOUSE'),
                       ('move', D, 0)])
# the chord
add_case("chordLM_h", [('press', 'LEFTMOUSE'), ('press', 'MIDDLEMOUSE'), ('move', D, 0)],
         verify=like("altR_h", "Alt+LMB then MMB, drag right"))
add_case("chordML_h", [('press', 'MIDDLEMOUSE'), ('press', 'LEFTMOUSE'), ('move', D, 0)],
         verify=like("altR_h", "Alt+MMB then LMB, drag right"))
add_case("chordLM_v", [('press', 'LEFTMOUSE'), ('press', 'MIDDLEMOUSE'), ('move', 0, D)],
         verify=unchanged("Alt+LMB+MMB, drag up"))
add_case("chordML_d", [('press', 'MIDDLEMOUSE'), ('press', 'LEFTMOUSE'), ('move', D, D)],
         verify=like("altR_d", "Alt+MMB+LMB, drag right+up"))
# letting go of one button
add_case("chord_relL", [('press', 'MIDDLEMOUSE'), ('press', 'LEFTMOUSE'), ('move', D, 0), ('snap', 'zoomed'),
                        ('release', 'LEFTMOUSE'), ('move', D, 0)],
         verify=[like("zoom_pan", "zoom, let go of LMB, drag: pans like Alt+MMB"),
                 panned("after letting go of LMB", "zoomed")])
add_case("chord_relM", [('press', 'LEFTMOUSE'), ('press', 'MIDDLEMOUSE'), ('move', D, 0), ('snap', 'zoomed'),
                        ('release', 'MIDDLEMOUSE'), ('move', D, 0)],
         verify=still("LMB, MMB, drag, let go of MMB, drag", "zoomed"))
add_case("chord_again", [('press', 'MIDDLEMOUSE'), ('press', 'LEFTMOUSE'), ('move', D, 0), ('release', 'LEFTMOUSE'),
                         ('press', 'LEFTMOUSE'), ('move', D, 0)],
         verify=like("zoom_zoom", "zoom, let go of LMB, press it again: zooms again"))
add_case("chord_relM_again", [('press', 'LEFTMOUSE'), ('press', 'MIDDLEMOUSE'), ('move', D, 0),
                              ('release', 'MIDDLEMOUSE'), ('press', 'MIDDLEMOUSE'), ('move', D, 0)],
         verify=like("zoom_zoom", "zoom, let go of MMB, press it again: zooms again"))


# Blender's Zoom to Mouse Position: the chord keeps the point under the mouse like Alt+RMB does then
@step
def s_zoom_to_mouse_on():
    bpy.context.preferences.inputs.use_zoom_to_mouse = True


add_case("altR_mouse", [('press', 'RIGHTMOUSE'), ('move', D, 0)], at=(0.3, 0.65))
add_case("chord_mouse", [('press', 'LEFTMOUSE'), ('press', 'MIDDLEMOUSE'), ('move', D, 0)], at=(0.3, 0.65),
         verify=like("altR_mouse", "Zoom to Mouse Position on: the chord"))


@step
def s_zoom_to_mouse_off():
    bpy.context.preferences.inputs.use_zoom_to_mouse = False


run()
