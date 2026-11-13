"""#357: dragging the ViewCube tumbles the view like Maya — the same direction as Alt+LMB, faster (Maya: a 60 px drag
on the cube turns the view about 35° where Alt+LMB turns it 24°), and no snap to a face on release; a click without a
drag still looks along the face; a locked top / front / side view stays locked. Looking through a camera, the drag
moves the camera as Alt+LMB does there (sideways and up / down the same way, around the same point, again about 1.5
times as far): the view stays the camera's, locked channels stay, one undo puts the camera back, Esc during the drag
too."""

import math
import os
import sys
from importlib import import_module

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, win  # noqa: E402

C = {}
DX = 60


def vf():
    return import_module(MODULE + ".ui.view_furniture")


def view():
    return import_module(MODULE + ".ui.status_line").main_view3d(win().screen)


def cube_face():
    area, region = view()
    m = vf()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        b = m._bounds(bpy.context)
    s = m._scale()
    size = m.cube_size(region.width, region.height, s)
    centre, _l, _t = m.layout(b, s, size)
    faces = m.faces_2d(m._cube_rotation(region.data), centre, size)
    name, poly, *_r = max(faces, key=lambda f: abs((f[1][0][0] - f[1][2][0]) * (f[1][0][1] - f[1][2][1])))
    return name, (region.x + int(sum(p[0] for p in poly) / len(poly)), region.y + int(sum(p[1] for p in poly) / len(poly)))


def yaw(q):
    d = q @ Vector((0.0, 0.0, -1.0))
    return math.degrees(math.atan2(d.y, d.x))


def look(q):
    return q @ Vector((0.0, 0.0, -1.0))


def drag_steps(tag, start, alt=False, dx=DX, dy=0, n=6):
    def press():
        x, y = start()
        C[tag + "_xy"] = (x, y)
        C[tag + "_rot0"] = view()[1].data.view_rotation.copy()
        ev('MOUSEMOVE', 'NOTHING', x=x - 2, y=y)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        if alt:
            ev('LEFT_ALT', 'PRESS', x=x, y=y, alt=True)
        ev('LEFTMOUSE', 'PRESS', x=x, y=y, alt=alt)

    steps = [press]
    for i in range(1, n + 1):
        def mv(i=i):
            x, y = C[tag + "_xy"]
            ev('MOUSEMOVE', 'NOTHING', x=x + dx * i // n, y=y + dy * i // n, alt=alt)
        steps.append(mv)

    def release():
        x, y = C[tag + "_xy"]
        ev('LEFTMOUSE', 'RELEASE', x=x + dx, y=y + dy, alt=alt)
        if alt:
            ev('LEFT_ALT', 'RELEASE', x=x + dx, y=y + dy)

    def done():
        C[tag + "_rot1"] = view()[1].data.view_rotation.copy()
    return steps + [release, idle, idle, done]


def idle():
    pass


def reset_view():
    rv = view()[1].data
    rv.view_perspective = 'PERSP'
    rv.is_orthographic_side_view = False
    rv.view_rotation = C["home"]


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_home():
    bpy.ops.allset.keymap_activate()
    C["home"] = view()[1].data.view_rotation.copy()


for _f in drag_steps("cube", lambda: cube_face()[1]):
    step(_f)


@step
def s_cube_checks():
    q0, q1 = C["cube_rot0"], C["cube_rot1"]
    C["cube_yaw"] = (yaw(q1) - yaw(q0) + 180.0) % 360.0 - 180.0
    d = look(q1)
    check(f"a ViewCube drag turns the view ({C['cube_yaw']:.1f} deg)", abs(C["cube_yaw"]) > 5.0)
    check(f"no snap to a face on release (look {tuple(round(c, 3) for c in d)})", max(abs(c) for c in d) < 0.999)
    check(f"the view stays perspective ({view()[1].data.view_perspective})", view()[1].data.view_perspective == 'PERSP')
    reset_view()


def _mid():
    _a, r = view()
    return r.x + int(r.width * 0.45), r.y + int(r.height * 0.5)


for _f in drag_steps("alt", _mid, alt=True):
    step(_f)


@step
def s_compare():
    alt_yaw = (yaw(C["alt_rot1"]) - yaw(C["alt_rot0"]) + 180.0) % 360.0 - 180.0
    ratio = C["cube_yaw"] / alt_yaw if abs(alt_yaw) > 1e-3 else 0.0
    check(f"the same direction as Alt+LMB, about 1.5 times as far (cube {C['cube_yaw']:.1f} / Alt+LMB {alt_yaw:.1f} "
          f"= {ratio:.2f})", 1.2 < ratio < 1.8)
    reset_view()


@step
def s_click_press():
    name, (x, y) = cube_face()
    C["click_face"] = name
    ev('MOUSEMOVE', 'NOTHING', x=x - 2, y=y)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)


@step
def s_click_release():
    _n, (x, y) = cube_face()
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


for _i in range(5):
    step(idle)


@step
def s_click_checks():
    d = look(view()[1].data.view_rotation)
    check(f"a click on {C['click_face']} still looks along it ({tuple(round(c, 3) for c in d)})",
          max(abs(c) for c in d) > 0.999)
    rv = view()[1].data
    reset_view()
    rv.view_rotation = (1.0, 0.0, 0.0, 0.0)                 # the top view, looking straight down
    rv.view_perspective = 'ORTHO'
    rv.is_orthographic_side_view = True


for _f in drag_steps("ortho", lambda: cube_face()[1]):
    step(_f)


@step
def s_ortho():
    q0, q1 = C["ortho_rot0"], C["ortho_rot1"]
    changed = max(abs(a - b) for a, b in zip(q0, q1)) > 1e-4
    check("a locked ortho side view doesn't tumble from the ViewCube either", not changed)
    reset_view()
    # looking through a camera
    sc = bpy.context.scene
    ob = bpy.data.objects.new("camera1", bpy.data.cameras.new("cameraShape1"))
    sc.collection.objects.link(ob)
    pos = Vector((10.0, -10.0, 6.0))
    ob.matrix_world = Matrix.Translation(pos) @ (-pos).to_track_quat('-Z', 'Y').to_matrix().to_4x4()
    bpy.context.view_layer.update()
    C["cam0"] = ob.matrix_basis.copy()
    area, region = view()
    area.spaces.active.camera = ob
    sc.camera = ob
    region.data.view_perspective = 'CAMERA'
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.ed.undo_push(message="camera set up")


def camera():
    return bpy.data.objects["camera1"]


def cam_yaw():
    d = camera().matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
    return math.degrees(math.atan2(d.y, d.x))


def cam_pitch():
    d = camera().matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
    return math.degrees(math.asin(max(-1.0, min(1.0, d.z))))


def orbit_point():
    """How far along its first look the camera's turn from the start pivots, and how far the move is from such a
    turn (0 = it turns around one point on that line)."""
    m0, m1 = C["cam0"], camera().matrix_world
    q0, q1 = m0.to_quaternion(), m1.to_quaternion()
    look0 = q0 @ Vector((0.0, 0.0, -1.0))
    w = look0 - (q1 @ q0.inverted()) @ look0
    v = m1.translation - m0.translation
    t = v.dot(w) / w.dot(w)
    return t, (v - w * t).length


def put_camera():
    camera().matrix_basis = C["cam0"]
    bpy.context.view_layer.update()
    view()[1].data.view_perspective = 'CAMERA'


@step
def s_cam_start():
    C["cam_yaw0"] = cam_yaw()


for _f in drag_steps("camcube", lambda: cube_face()[1]):
    step(_f)


@step
def s_cam_checks():
    C["cam_cube_yaw"] = (cam_yaw() - C["cam_yaw0"] + 180.0) % 360.0 - 180.0
    check(f"in a camera view the drag moves the camera ({C['cam_cube_yaw']:.1f} deg)", abs(C["cam_cube_yaw"]) > 5.0)
    check(f"... and the view stays the camera's ({view()[1].data.view_perspective})",
          view()[1].data.view_perspective == 'CAMERA')
    C["cube_pivot"] = orbit_point()
    area, region = view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.ed.undo()


@step
def s_cam_undo():
    back = camera().matrix_basis
    diff = max(abs(back[i][j] - C["cam0"][i][j]) for i in range(4) for j in range(4))
    check(f"one undo puts the camera back (difference {diff:.5f})", diff < 1e-4)
    put_camera()
    C["cam_yaw0"] = cam_yaw()


for _f in drag_steps("camalt", _mid, alt=True):
    step(_f)


@step
def s_cam_compare():
    alt_yaw = (cam_yaw() - C["cam_yaw0"] + 180.0) % 360.0 - 180.0
    ratio = C["cam_cube_yaw"] / alt_yaw if abs(alt_yaw) > 1e-3 else 0.0
    check(f"the camera turns the same way as with Alt+LMB, about 1.5 times as far (cube {C['cam_cube_yaw']:.1f} / "
          f"Alt+LMB {alt_yaw:.1f} = {ratio:.2f})", 1.2 < ratio < 1.8)
    (tc, rc), (ta, ra) = C["cube_pivot"], orbit_point()
    check(f"... around the same point as Alt+LMB ({tc:.3f} / {ta:.3f} along the look; off by {rc:.5f} / {ra:.5f})",
          abs(tc - ta) < 1e-3 * max(1.0, abs(ta)) and rc < 1e-3 and ra < 1e-3)
    put_camera()
    C["cam_pitch0"] = cam_pitch()


for _f in drag_steps("camcubev", lambda: cube_face()[1], dx=0, dy=-DX):
    step(_f)


@step
def s_cam_cube_v():
    C["cam_cube_pitch"] = cam_pitch() - C["cam_pitch0"]
    put_camera()


for _f in drag_steps("camaltv", _mid, alt=True, dx=0, dy=-DX):
    step(_f)


@step
def s_cam_compare_v():
    alt_pitch = cam_pitch() - C["cam_pitch0"]
    ratio = C["cam_cube_pitch"] / alt_pitch if abs(alt_pitch) > 1e-3 else 0.0
    check(f"a drag down tilts the camera the same way as Alt+LMB, about 1.5 times as far (cube "
          f"{C['cam_cube_pitch']:.1f} / Alt+LMB {alt_pitch:.1f} = {ratio:.2f})", 1.2 < ratio < 1.8)
    put_camera()
    camera().lock_location = (True, False, False)
    C["cam_x"] = camera().location.x


for _f in drag_steps("camlock", lambda: cube_face()[1]):
    step(_f)


@step
def s_cam_lock():
    c = camera()
    check(f"a locked channel stays (Translate X {c.location.x:.4f}, was {C['cam_x']:.4f})",
          abs(c.location.x - C["cam_x"]) < 1e-5)
    c.lock_location = (False, False, False)
    put_camera()
    name, (x, y) = cube_face()
    C["esc_xy"] = (x, y)
    ev('MOUSEMOVE', 'NOTHING', x=x - 2, y=y)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)


@step
def s_cam_esc_move():
    x, y = C["esc_xy"]
    ev('MOUSEMOVE', 'NOTHING', x=x + 30, y=y)
    ev('MOUSEMOVE', 'NOTHING', x=x + 60, y=y)


@step
def s_cam_esc():
    x, y = C["esc_xy"]
    C["esc_moved"] = max(abs(camera().matrix_basis[i][j] - C["cam0"][i][j]) for i in range(4) for j in range(4))
    ev('ESC', 'PRESS', x=x + 60, y=y)
    ev('ESC', 'RELEASE', x=x + 60, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x + 60, y=y)


@step
def s_cam_esc_check():
    diff = max(abs(camera().matrix_basis[i][j] - C["cam0"][i][j]) for i in range(4) for j in range(4))
    check(f"Esc during the drag puts the camera back (moved {C['esc_moved']:.3f}, now {diff:.5f})",
          C["esc_moved"] > 1e-3 and diff < 1e-4)


run()
