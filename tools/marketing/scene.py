"""Scene helpers shared by tools/marketing/shots.py (step 122 stills) and tools/marketing/clips.py (step 123 clips).

Runs inside a GUI Blender started with --enable-event-simulate (tests/gui/sim.py). The scene is built from the
licensed models in  (tools/marketing/assets.json, docs/distribution/marketing/CREDITS.md):
a Poly Haven workbench with a drill and props, Kenney's rigged character and Quaternius' RobotExpressive.
"""

import math
import sys
from importlib import import_module
from pathlib import Path

import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Euler, Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "gui"))
from sim import MODULE, view3d, win  # noqa: E402

ASSETS = ROOT / "research" / "marketing_assets"


def mod(name):
    return import_module(MODULE + name)


def prefs():
    return bpy.context.preferences.addons[MODULE].preferences


def redraw():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def v3d_override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), screen=win().screen, area=area, region=region)


def area_rect(a):
    h = win().height
    return [a.x, h - (a.y + a.height), a.width, a.height]


def region_rect(r):
    h = win().height
    return [r.x, h - (r.y + r.height), r.width, r.height]


def screen_pos(ob, local=(0, 0, 0), world=None):
    """Window pixel (bottom-up, as event_simulate wants) of a point of ``ob`` (or of ``world``) in the main view."""
    area, region = view3d()
    rv3d = area.spaces.active.region_3d
    p = Vector(world) if world is not None else ob.matrix_world @ Vector(local)
    co = location_3d_to_region_2d(region, rv3d, p)
    return int(region.x + co.x), int(region.y + co.y)


def to_top(x, y):
    return [x, win().height - y]


def select(obs, active=None):
    with v3d_override():
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.context.view_layer.objects:
        o.select_set(o in obs)
    bpy.context.view_layer.objects.active = active or (obs[-1] if obs else None)


def frame(obs, zoom=1.0, rot=None):
    """Frame objects in the main view (Maya F), then move the camera back by ``zoom``."""
    area, region = view3d()
    rv3d = area.spaces.active.region_3d
    if rot is not None:
        rv3d.view_rotation = Euler([math.radians(a) for a in rot]).to_quaternion()
    rv3d.view_perspective = 'PERSP'
    pts = [o.matrix_world @ Vector(c) for o in obs if o.type in {'MESH', 'ARMATURE'} for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    rv3d.view_location = (lo + hi) / 2
    rv3d.view_distance = (hi - lo).length * 1.25 * zoom


def bounds(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == 'MESH' for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi


def place(root, objs, height=None, pos=(0, 0, 0), rot_z=0.0, floor=True):
    """Scale an imported hierarchy to ``height`` metres and stand it at ``pos`` (its lowest point on z = pos.z)."""
    bpy.context.view_layer.update()
    if height:
        lo, hi = bounds(objs)
        root.scale = root.scale * (height / max(hi.z - lo.z, 1e-6))
    root.rotation_euler.z += math.radians(rot_z)
    bpy.context.view_layer.update()
    lo, hi = bounds(objs)
    centre = (lo + hi) / 2
    root.location += Vector((pos[0] - centre.x, pos[1] - centre.y, pos[2] - lo.z if floor else 0))
    bpy.context.view_layer.update()


def import_asset(asset_id, filename):
    path = next((ASSETS / asset_id).rglob(filename))
    before = set(bpy.data.objects)
    with v3d_override():
        if path.suffix.lower() in {".gltf", ".glb"}:
            bpy.ops.import_scene.gltf(filepath=str(path))
        elif path.suffix.lower() == ".fbx":
            bpy.ops.import_scene.fbx(filepath=str(path))
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        o.rotation_mode = 'XYZ'             # glTF quaternions -> Rotate X/Y/Z channels (the value is converted)
        if o.type == 'EMPTY':
            o.empty_display_size = 1e-4      # import helpers: no axes drawn through the scene
    roots = [o for o in new if o.parent is None]
    if len(roots) > 1:
        empty = bpy.data.objects.new(asset_id, None)
        empty.empty_display_size = 1e-4
        bpy.context.scene.collection.objects.link(empty)
        for r in roots:
            r.parent = empty
        root = empty
        new.append(empty)
    else:
        root = roots[0]
    return root, new


def kenney_skin(objs):
    """Kenney's FBX comes in with an untextured, alpha 0 material: connect its skin texture (file unchanged)."""
    png = next((ASSETS / "kenney_protagonists").rglob("skaterMaleA.png"))
    img = bpy.data.images.load(str(png))
    for o in objs:
        if o.type != 'MESH':
            continue
        for slot in o.material_slots:
            m = slot.material
            if m is None:
                continue
            m.use_nodes = True
            nt = m.node_tree
            bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if bsdf is None:
                continue
            tex = nt.nodes.new("ShaderNodeTexImage")
            tex.image = img
            nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
            bsdf.inputs["Alpha"].default_value = 1.0
            m.blend_method = 'OPAQUE' if hasattr(m, "blend_method") else None


def shading():
    for a in win().screen.areas:
        if a.type == 'VIEW_3D' and not mod(".ui.toolbox").is_toolbox(a.spaces.active):
            sh = a.spaces.active.shading
            sh.type = 'MATERIAL'
            sh.use_scene_world = False
            sh.studiolight_background_alpha = 0.0    # the viewport shows the theme background (#5c5c5c)
            sh.studiolight_intensity = 1.0
            ov = a.spaces.active.overlay
            ov.show_floor = True
            ov.show_bones = False                    # bones only in the rigging shot
            if hasattr(a.spaces.active, "show_region_asset_shelf"):
                a.spaces.active.show_region_asset_shelf = False


def show_bones(on):
    for a in win().screen.areas:
        if a.type == 'VIEW_3D':
            a.spaces.active.overlay.show_bones = on


def maya_look():
    """Maya theme, factory background #5c5c5c (step 120), no tooltips / in-view messages in the pictures."""
    mod(".theme").apply()
    mod(".operators.key_batch3").reset_background()
    bpy.context.preferences.view.show_tooltips = False
    prefs().in_view_messages = False


def clear_objects():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)


def build_workbench(C, characters=True):
    """The step 122 scene: a Poly Haven workbench (table, drill, toolbox, plant, barrel, box) and, with
    ``characters``, Kenney's skinned character and Quaternius' walking robot. Fills ``C``; returns True when every
    model came in (and the robot's walk action was found)."""
    table, t_objs = import_asset("ph_woodentable_01", "WoodenTable_01_1k.gltf")
    place(table, t_objs, pos=(0, 0, 0))
    top = bounds(t_objs)[1].z
    drill, d_objs = import_asset("ph_drill_01", "Drill_01_1k.gltf")
    place(drill, d_objs, pos=(0.05, -0.05, top), rot_z=-30)
    box, b_objs = import_asset("ph_metal_toolbox", "metal_toolbox_1k.gltf")
    place(box, b_objs, pos=(-0.42, 0.12, top), rot_z=15)
    plant, p_objs = import_asset("ph_potted_plant_02", "potted_plant_02_1k.gltf")
    place(plant, p_objs, pos=(2.5, 1.3, 0))
    barrel, ba_objs = import_asset("ph_barrel_01", "Barrel_01_1k.gltf")
    place(barrel, ba_objs, pos=(-1.15, 1.0, 0))
    crate, c_objs = import_asset("ph_cardboard_box_01", "cardboard_box_01_1k.gltf")
    place(crate, c_objs, pos=(-0.55, 1.45, 0), rot_z=20)
    C.update(table=table, table_objs=t_objs, drill=drill, box=box, top=top)
    C["drill_mesh"] = next(o for o in d_objs if o.type == 'MESH')
    if not characters:
        return all(C[k] for k in ("table", "drill"))

    robot, r_objs = import_asset("robot_expressive", "RobotExpressive.glb")
    place(robot, r_objs, height=1.5, pos=(1.55, -0.45, 0), rot_z=-30)
    kid, k_objs = import_asset("kenney_protagonists", "characterMedium.fbx")
    kenney_skin(k_objs)
    place(kid, k_objs, height=1.7, pos=(-1.7, -0.3, 0), rot_z=25)
    C.update(robot=robot, kid=kid)
    C["kid_mesh"] = next(o for o in k_objs if o.type == 'MESH')
    C["kid_arm"] = next(o for o in k_objs if o.type == 'ARMATURE')
    C["robot_arm"] = next(o for o in r_objs if o.type == 'ARMATURE')
    C["robot_meshes"] = [o for o in r_objs if o.type == 'MESH']

    # robot walking: the glTF actions come in as NLA tracks / stashed actions; play "Walking" from frame 1
    acts = [a for a in bpy.data.actions if "walk" in a.name.lower()]
    ad = C["robot_arm"].animation_data or C["robot_arm"].animation_data_create()
    for t in list(ad.nla_tracks):
        ad.nla_tracks.remove(t)
    if acts:
        ad.action = acts[0]
        sc = bpy.context.scene
        fr = acts[0].frame_range
        n = int(round(fr[1] - fr[0])) + 1
        sc.frame_start, sc.frame_end = 1, n
        sc.use_preview_range = True
        sc.frame_preview_start, sc.frame_preview_end = 1, n
        sc.frame_set(8)
        C["walk"] = acts[0]
    return all(C[k] for k in ("table", "drill", "robot", "kid")) and bool(acts)
