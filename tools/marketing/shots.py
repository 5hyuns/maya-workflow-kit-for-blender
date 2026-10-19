"""In-Blender part of tools/marketing/make_marketing.py (step 122): raw 1920 x 1080 GUI shots for the captioned
feature screens and the key visuals (docs/distribution/marketing/style.md, copy.md).

Runs in a GUI Blender on a clean sandbox with the extension installed, with --enable-event-simulate
(tests/gui/sim.py). The scene is built from the licensed models in 
(tools/marketing/assets.json, docs/distribution/marketing/CREDITS.md): a Poly Haven workbench with a drill and props,
Kenney's rigged character and Quaternius' RobotExpressive. Each shot is taken one tick after the UI change
(``screen.screenshot`` shows the previous frame). meta.json records UI rects (top-down window pixels) for callouts.
The approach (event-driven steps, menus opened from mid-window, logo painted over) follows tools/listing_shots.py;
the aborted 10-19 attempt (git stash) was read for the scene recipes only.
"""

import json
import math
import os
import sys
from importlib import import_module
from pathlib import Path

import bmesh
import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "gui"))
import sim  # noqa: E402
from sim import MODULE, check, ev, run, setup, step, tap, view3d, win  # noqa: E402

RAW = Path(os.environ.get("ALLSET_SHOTS", str(ROOT / "tmp" / "marketing" / "raw")))
ASSETS = ROOT / "research" / "marketing_assets"
C = {}
META = {}


def mod(name):
    return import_module(MODULE + name)


def prefs():
    return bpy.context.preferences.addons[MODULE].preferences


# ------------------------------------------------------------------------------------------------ helpers
def redraw():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def wait():
    redraw()


def v3d_override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), screen=win().screen, area=area, region=region)


def esc():
    tap('ESC')


def area_rect(a):
    h = win().height
    return [a.x, h - (a.y + a.height), a.width, a.height]


def region_rect(r):
    h = win().height
    return [r.x, h - (r.y + r.height), r.width, r.height]


def rects(extra=None):
    """Named UI rects in top-down window pixels for compose.py callouts."""
    out = {}
    md = mod(".ui.maya_dock")
    for a in win().screen.areas:
        key = a.ui_type
        if a.type == 'PROPERTIES':
            role = md.role_of(a) if hasattr(md, "role_of") else None
            key = f"dock_{role}" if role else "properties"
        out.setdefault(key, area_rect(a))
    area, region = view3d()
    out["viewport"] = region_rect(region)
    w = win().width
    out["switch"] = [w - 150, 0, 150, 30]          # Maya | Blender at the right of the top bar
    if extra:
        out.update(extra)
    return out


def shot(name, extra=None):
    RAW.mkdir(parents=True, exist_ok=True)
    path = str(RAW / f"{name}.png")
    sim.screenshot(path)
    hide_logo(path)
    vl = bpy.context.view_layer
    META[name] = {"window": [win().width, win().height], "rects": rects(extra),
                  "selected": [o.name for o in bpy.context.scene.objects if o.select_get()],
                  "active": vl.objects.active.name if vl.objects.active else None, "mode": bpy.context.mode}
    with open(RAW / "meta.json", "w", encoding="utf-8") as fh:
        json.dump(META, fh, indent=1)


def hide_logo(path):
    """Paint the top bar's Blender menu icon over with the bar colour (no Blender logo in the images,
    extensions.blender.org terms 2.2), as tools/listing_shots.py does."""
    import numpy as np
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)
    size = round(30 * bpy.context.preferences.system.ui_scale)
    px[h - size:, :size] = px[h - 2, size]
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)


def screen_pos(ob, local=(0, 0, 0)):
    area, region = view3d()
    rv3d = area.spaces.active.region_3d
    p = ob.matrix_world @ Vector(local)
    co = location_3d_to_region_2d(region, rv3d, p)
    return int(region.x + co.x), int(region.y + co.y)


def to_top(x, y):
    return [x, win().height - y]


def select(obs, active=None, mode='OBJECT'):
    with v3d_override():
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.context.view_layer.objects:
        o.select_set(o in obs)
    bpy.context.view_layer.objects.active = active or obs[-1]


def frame(obs, zoom=1.0, rot=None):
    """Frame objects in the main view (Maya F), then move the camera back by ``zoom``."""
    area, region = view3d()
    rv3d = area.spaces.active.region_3d
    if rot is not None:
        from mathutils import Euler
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


def show_bones(on):
    for a in win().screen.areas:
        if a.type == 'VIEW_3D':
            a.spaces.active.overlay.show_bones = on


# ------------------------------------------------------------------------------------------------ 0 before
@step
def s_before():
    tap('ESC')                                     # factory splash
    import addon_utils
    addon_utils.enable(MODULE, default_set=True)
    bpy.context.preferences.view.show_tooltips = False


step(wait)


@step
def s_welcome():
    _area, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + int(r.height * 0.62))
    with bpy.context.temp_override(window=win()):
        C["welcome"] = bpy.ops.allset.welcome('INVOKE_DEFAULT')
    check("welcome dialog opens on plain Blender", C["welcome"] == {'RUNNING_MODAL'})


step(wait)
step(wait)


@step
def s_before_shot():
    shot("switch_before")
    esc()


@step
def s_opt_in():
    setup()   # opts in to Maya mode (what the dialog's button does)
    check("install the Maya layout template", bpy.ops.allset.layout_install() == {'FINISHED'})
    bpy.ops.wm.read_homefile(app_template="Allset")


# ------------------------------------------------------------------------------------------------ scene
@step
def s_scene():
    kc = bpy.context.window_manager.keyconfigs.active
    check("Maya keymap active in the Allset layout", kc is not None and kc.name == "Maya-style")
    mod(".theme").apply()
    mod(".operators.key_batch3").reset_background()    # factory background #5c5c5c (step 120)
    bpy.context.preferences.view.show_tooltips = False
    prefs().in_view_messages = False
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)

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

    robot, r_objs = import_asset("robot_expressive", "RobotExpressive.glb")
    place(robot, r_objs, height=1.5, pos=(1.55, -0.45, 0), rot_z=-30)
    kid, k_objs = import_asset("kenney_protagonists", "characterMedium.fbx")
    kenney_skin(k_objs)
    place(kid, k_objs, height=1.7, pos=(-1.7, -0.3, 0), rot_z=25)

    C.update(table=table, drill=drill, box=box, robot=robot, kid=kid)
    C["drill_mesh"] = next(o for o in d_objs if o.type == 'MESH')
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
    check("scene built from the licensed models (table, drill, props, two characters)",
          all(C[k] for k in ("table", "drill", "robot", "kid")) and bool(acts))
    shading()
    select([C["drill_mesh"]])
    frame([C["table"]] + t_objs, 1.0, rot=(68, 0, 28))
    _area, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width - 30, y=r.y + 30)
    redraw()


step(wait)
step(wait)


# ------------------------------------------------------------------------------------------------ hero (key visual)
@step
def s_hero():
    select([C["kid_mesh"]])
    with v3d_override():
        bpy.ops.wm.tool_set_by_id(name="builtin.move")
    area, _r = view3d()
    rv3d = area.spaces.active.region_3d
    from mathutils import Euler
    rv3d.view_rotation = Euler([math.radians(a) for a in (72, 0, 18)]).to_quaternion()
    rv3d.view_location = Vector((0, 0.1, 0.75))
    rv3d.view_distance = 5.4
    redraw()


step(wait)
step(wait)


@step
def s_hero_shot():
    shot("hero")


# ------------------------------------------------------------------------------------------------ 1 hotbox
@step
def s_hotbox_press():
    select([C["robot_meshes"][0]], C["robot_meshes"][0])
    _area, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)
    ev('SPACE', 'PRESS')


step(wait)
step(wait)


@step
def s_hotbox_shot():
    _area, r = view3d()
    cx, cy = r.x + r.width // 2, r.y + r.height // 2
    shot("hotbox", {"hotbox_centre": [*to_top(cx - 90, cy + 40), 180, 80]})
    ev('SPACE', 'RELEASE')


# ------------------------------------------------------------------------------------------------ 2 marking menus
@step
def s_rmb_press():
    select([C["kid_mesh"]])
    frame([C["kid_mesh"]], 1.6, rot=(78, 0, -10))
    redraw()


step(wait)


@step
def s_rmb_press2():
    x, y = screen_pos(C["kid_mesh"], (0, 0, 0))
    _area, r = view3d()
    y = r.y + int(r.height * 0.55)
    C["rmb"] = (x, y)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('RIGHTMOUSE', 'PRESS', x=x, y=y)


step(wait)
step(wait)


@step
def s_rmb_shot():
    x, y = C["rmb"]
    shot("marking_menus", {"press": [*to_top(x - 12, y + 12), 24, 24]})
    ev('RIGHTMOUSE', 'RELEASE', x=x, y=y)
    esc()


# ------------------------------------------------------------------------------------------------ 3 CB + AE
@step
def s_cb_ae():
    d = C["drill_mesh"]
    select([d])
    sc = bpy.context.scene
    for f, z, rz in ((1, 0.0, 0), (12, 0.06, 20), (24, 0.0, 0)):
        sc.frame_set(f)
        d.location.z = z
        d.rotation_euler.z = math.radians(rz)
        d.keyframe_insert("location")
        d.keyframe_insert("rotation_euler")
    sc.frame_set(8)
    frame([C["drill_mesh"]], 1.7, rot=(64, 0, 24))
    md = mod(".ui.maya_dock")
    stack = sim.dock_area('CHANNEL_BOX')
    before = set(win().screen.areas[:])
    with bpy.context.temp_override(window=win(), screen=win().screen, area=stack):
        bpy.ops.screen.area_split(direction='HORIZONTAL', factor=0.55)
    new = [a for a in win().screen.areas if a not in before]
    C["ae"] = new[0] if new else None
    if C["ae"]:
        md.set_role(C["ae"], 'ATTRIBUTE_EDITOR', win())
    with v3d_override():
        bpy.ops.allset.ae_tab(key="T")
    _area, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width - 30, y=r.y + 30)
    redraw()


step(wait)
step(wait)


@step
def s_cb_ae_shot():
    extra = {}
    if C.get("ae"):
        extra["ae"] = area_rect(C["ae"])
    stack = sim.dock_area('CHANNEL_BOX')
    extra["cb"] = area_rect(stack)
    shot("channel_box_ae", extra)
    mod(".ui.maya_dock").close_area(bpy.context, win(), C.get("ae"))
    redraw()


# ------------------------------------------------------------------------------------------------ 4 menu sets / shelf / option boxes
@step
def s_rigging():
    prefs().menu_set = 'riggingMenuSet'
    bpy.ops.allset.shelf_select(shelf="Rigging")
    select([C["kid_mesh"]])
    frame([C["kid_mesh"]], 1.3, rot=(80, 0, -5))
    redraw()


@step
def s_rig_menu():
    _area, region = view3d()
    C["menu_at"] = (region.x + int(region.width * 0.2), region.y + int(region.height * 0.8))
    ev('MOUSEMOVE', 'NOTHING', x=C["menu_at"][0], y=C["menu_at"][1])
    name = mod(".ui.menu_sets").menu_idname("mainRigSkeletonsMenu")
    with bpy.context.temp_override(window=win()):
        bpy.ops.wm.call_menu(name=name)


step(wait)
step(wait)


@step
def s_rig_shot():
    shot("menus_shelves")
    esc()


# ------------------------------------------------------------------------------------------------ 5 navigation & selection
@step
def s_components():
    prefs().menu_set = 'modelingMenuSet'
    bpy.ops.allset.shelf_select(shelf="Polygons")
    d = C["drill_mesh"]
    select([d])
    with v3d_override():
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        bm = bmesh.from_edit_mesh(d.data)
        lo = min(v.co.z for v in bm.verts)
        hi = max(v.co.z for v in bm.verts)
        for f in bm.faces:
            f.select_set(f.calc_center_median().z < lo + (hi - lo) * 0.28)
        bmesh.update_edit_mesh(d.data)
        bpy.ops.wm.tool_set_by_id(name="builtin.move")
    frame([d], 1.0, rot=(70, 0, 30))
    redraw()


step(wait)


@step
def s_components_hover():
    x, y = screen_pos(C["drill_mesh"], (0, 0, 0))
    ev('MOUSEMOVE', 'NOTHING', x=x + 40, y=y + 60)
    redraw()


step(wait)
step(wait)


@step
def s_components_shot():
    shot("navigate_select")


# ------------------------------------------------------------------------------------------------ 6 Modeling Toolkit (still in edit mode)
@step
def s_mtk():
    sim.dock_area('MODELING_TOOLKIT')
    redraw()


step(wait)
step(wait)


@step
def s_mtk_shot():
    shot("modeling_toolkit", {"mtk": area_rect(sim.dock_area('MODELING_TOOLKIT'))})
    with v3d_override():
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    sim.dock_area('CHANNEL_BOX')
    redraw()


# ------------------------------------------------------------------------------------------------ 7 pivot & snapping
@step
def s_pivot_press():
    d = C["drill_mesh"]
    select([d])
    with v3d_override():
        bpy.ops.wm.tool_set_by_id(name="builtin.move")
    frame([d], 1.2, rot=(70, 0, 30))
    redraw()


step(wait)


@step
def s_pivot_d():
    x, y = screen_pos(C["drill_mesh"])
    C["piv"] = (x, y)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('D', 'PRESS', x=x, y=y)


step(wait)


@step
def s_pivot_rmb():
    ev('RIGHTMOUSE', 'PRESS', x=C["piv"][0], y=C["piv"][1])


step(wait)
step(wait)


@step
def s_pivot_shot():
    x, y = C["piv"]
    shot("pivot_snapping", {"press": [*to_top(x - 12, y + 12), 24, 24]})
    ev('RIGHTMOUSE', 'RELEASE', x=x, y=y)
    esc()


@step
def s_pivot_release():
    ev('D', 'RELEASE', x=C["piv"][0], y=C["piv"][1])
    with v3d_override():
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    redraw()


# ------------------------------------------------------------------------------------------------ 8 rigging: joints + skin weights
@step
def s_rig():
    prefs().menu_set = 'riggingMenuSet'
    arm, mesh = C["kid_arm"], C["kid_mesh"]
    select([mesh])
    res = None
    with v3d_override():
        try:
            res = bpy.ops.allset.paint_skin_weights()
        except RuntimeError as e:
            print("paint_skin_weights:", e)
        if bpy.context.mode != 'PAINT_WEIGHT':
            bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    vg = next((g for g in mesh.vertex_groups if "arm" in g.name.lower() and "left" in g.name.lower()), None) \
        or next((g for g in mesh.vertex_groups if "arm" in g.name.lower()), None)
    best, best_n = vg, -1
    for g in mesh.vertex_groups:
        n = 0
        for v in mesh.data.vertices:
            for e in v.groups:
                if e.group == g.index and 0.15 < e.weight < 0.95:
                    n += 1
        if any(k in g.name.lower() for k in ("spine", "chest", "neck")) and n > best_n:
            best, best_n = g, n
    vg = best
    if vg is not None:
        mesh.vertex_groups.active_index = vg.index
    names = {g.name for g in mesh.vertex_groups}
    for b in arm.data.bones:
        b.hide = b.name not in names            # IK / control / root helper bones: not joints a skin follows
    arm.show_in_front = True
    show_bones(True)
    check(f"rigging: weight paint on the skinned character ({res}, group {vg.name if vg else None})",
          bpy.context.mode == 'PAINT_WEIGHT')
    frame([mesh], 1.15, rot=(80, 0, -8))
    _area, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width - 30, y=r.y + 30)
    redraw()


step(wait)
step(wait)


@step
def s_rig_shot2():
    shot("rigging", {"cb": area_rect(sim.dock_area('CHANNEL_BOX'))})
    with v3d_override():
        bpy.ops.object.mode_set(mode='OBJECT')
    show_bones(False)
    prefs().menu_set = 'modelingMenuSet'
    bpy.ops.allset.shelf_select(shelf="Polygons")
    redraw()


# ------------------------------------------------------------------------------------------------ 9 animation
@step
def s_anim():
    prefs().menu_set = 'animationMenuSet'
    bpy.ops.allset.shelf_select(shelf="Animation")
    arm = C["robot_arm"]
    with v3d_override():
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
    select([arm])
    with v3d_override():
        bpy.ops.object.mode_set(mode='POSE')
        for b in arm.pose.bones:
            mod(".ui.channel_box").set_bone_selected(b, False) if hasattr(mod(".ui.channel_box"), "set_bone_selected") \
                else None
        span = {}
        for fc in mod(".compat").action_fcurves(C["walk"]):
            if fc.data_path.startswith('pose.bones["') and "rotation" in fc.data_path:
                name = fc.data_path.split('"')[1]
                vals = [k.co[1] for k in fc.keyframe_points]
                span[name] = span.get(name, 0) + (max(vals) - min(vals) if vals else 0)
        pick = max(span, key=span.get) if span else None
        bone = arm.pose.bones.get(pick) or arm.pose.bones[0]
        arm.data.bones.active = bone.bone
        bpy.ops.pose.select_all(action='DESELECT')
        bone.bone.select = True
    bpy.context.scene.frame_set(8)
    area, _r = view3d()
    before = set(win().screen.areas[:])
    with bpy.context.temp_override(window=win(), screen=win().screen, area=area):
        bpy.ops.screen.area_split(direction='HORIZONTAL', factor=0.5)
    new = [a for a in win().screen.areas if a not in before]
    C["graph"] = None
    if new:
        top = new[0]
        if hasattr(top.spaces.active, "show_region_asset_shelf"):
            top.spaces.active.show_region_asset_shelf = False   # its 29 px header row drew stale pixels
        bottom = min((a for a in win().screen.areas if a.type == 'VIEW_3D' and a is not top
                      and a.x == top.x and a.width == top.width), key=lambda a: a.y)
        bottom.ui_type = 'FCURVES'
        bottom.spaces.active.show_region_ui = False
        bottom.spaces.active.dopesheet.show_only_selected = True
        C["graph"] = bottom
    redraw()


@step
def s_anim_graph():
    a = C["graph"]
    check("Graph Editor split under the viewport", a is not None)
    r = next(rg for rg in a.regions if rg.type == 'WINDOW')
    with bpy.context.temp_override(window=win(), area=a, region=r):
        bpy.ops.graph.select_all(action='SELECT')
        bpy.ops.graph.view_all()
    frame(C["robot_meshes"], 2.3, rot=(80, 0, 30))
    _area, vr = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=vr.x + vr.width - 30, y=vr.y + 30)
    redraw()


step(wait)
step(wait)
step(wait)   # the split area keeps stale pixels of the old view for a tick or two
step(wait)


@step
def s_anim_shot():
    extra = {"graph": area_rect(C["graph"])} if C.get("graph") else {}
    shot("animation", extra)
    META["animation"]["regions"] = [[a.ui_type, a.y, a.height, [(r.type, r.y, r.height) for r in a.regions]]
                                    for a in win().screen.areas if a.type in {'VIEW_3D', 'GRAPH_EDITOR'}]
    with open(RAW / "meta.json", "w", encoding="utf-8") as fh:
        json.dump(META, fh, indent=1)


run(interval=0.7, first=3.0)
