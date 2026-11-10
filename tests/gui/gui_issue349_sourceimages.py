"""#349 in a real UI: a project with sourceimages, the scene saved in its scenes folder (Blender's own image browser
starts there). In Maya mode the file browser for an empty image slot starts in <project>/sourceimages:
- the Image Texture node's Open button in a Shader Editor of the main window (New Window file browser), picking a
  file there loads it from sourceimages; the same with Preferences > File Browser = Maximized Area;
- a project without sourceimages: Blender's start folder (scenes), the folder is not made;
- the Image Editor's Open with an empty slot (sourceimages) and with an image (that image's folder, as before);
- Create > Lights > Dome Light's image browser;
- the Attribute Editor File row's Open button and the Open button of the node in the Hypershade graph;
- Maya mode off: Blender's start folder (scenes)."""

import os
import shutil
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, dock_area, run, setup, step, view3d, win, load_maya_layout  # noqa: E402

GUI_TIMEOUT = 360
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tmp", "gui349")
PROJ = os.path.join(ROOT, "proj349")
BARE = os.path.join(ROOT, "bare349")          # a project without sourceimages
SRC = os.path.join(PROJ, "sourceimages")
SCENES = os.path.join(PROJ, "scenes")
OTHER = os.path.join(ROOT, "other")
C = {}


def mod(name):
    return import_module(MODULE + name)


def shot(name, window=None):
    if SHOTS:
        with bpy.context.temp_override(window=window or win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, name))


def norm(path):
    return os.path.normcase(os.path.normpath(path)) if path else path


def steps():
    return sys.modules["sim"]._steps


def again(fn, cond, limit=40):
    """Run ``fn`` again next tick while ``cond()`` is false (at most ``limit`` times); True = waiting."""
    n = C.setdefault("wait_" + fn.__name__, 0)
    if not cond() and n < limit:
        C["wait_" + fn.__name__] = n + 1
        steps().insert(0, fn)
        return True
    C["wait_" + fn.__name__] = 0
    return False


def wait_browser(fn, limit=40):
    """True while ``fn`` waits (it runs again next tick): no file browser yet, or one that appeared less than three
    ticks ago (it moves to its start folder after its first draw)."""
    n = C.get("wait_" + fn.__name__, 0)
    shown = C.get("shown_" + fn.__name__, 0) + (file_browser()[0] is not None)
    if shown < 3 and n < limit:
        C["wait_" + fn.__name__], C["shown_" + fn.__name__] = n + 1, shown
        steps().insert(0, fn)
        return True
    C["wait_" + fn.__name__] = C["shown_" + fn.__name__] = 0
    return False


def file_browser():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.type == 'FILE_BROWSER' and a.spaces.active.params is not None \
                    and a.spaces.active.active_operator is not None:
                return w, a
    return None, None


def browser_dir():
    _w, a = file_browser()
    if a is None:
        return None
    d = a.spaces.active.params.directory
    return norm(bpy.path.abspath(d.decode() if isinstance(d, bytes) else d))


def close_browser():
    w, a = file_browser()
    if w is None:
        return
    r = next(r for r in a.regions if r.type == 'WINDOW')
    x, y = r.x + r.width // 2, r.y + r.height // 2
    w.event_simulate(type='MOUSEMOVE', value='NOTHING', x=x, y=y)
    w.event_simulate(type='ESC', value='PRESS', x=x, y=y)
    w.event_simulate(type='ESC', value='RELEASE', x=x, y=y)


def hover(window, area, region):
    """(data path, Python command) of the button under the mouse."""
    wm = bpy.context.window_manager
    out = []
    for op, kw in ((bpy.ops.ui.copy_data_path_button, {"full_path": False}), (bpy.ops.ui.copy_python_command_button, {})):
        wm.clipboard = ""
        try:
            with bpy.context.temp_override(window=window, screen=window.screen, area=area, region=region):
                op(**kw)
        except RuntimeError:
            pass
        out.append(wm.clipboard)
    return tuple(out)


def find_open(where, key):
    """A step that sweeps the mouse (one probe per tick) for an image slot's Open button: down the middle of the
    region, then right along the row of the slot's New / Open buttons. ``C[key]`` = (x, y) or None."""
    state = {}

    def look():
        window, area, region = where()
        if not state:
            state.update(x=region.x + region.width // 2, y=region.y + region.height - 6, dx=0, dy=-8)
            C[key] = None
        else:
            path, cmd = hover(window, area, region)
            print("FIND", key, state["x"], state["y"], repr(path), repr(cmd), flush=True)
            if "image.open" in cmd:
                C[key] = (state["x"], state["y"])
                return
            if "image.new" in cmd and state["dy"]:
                state.update(dx=8, dy=0)
            state["x"] += state["dx"]
            state["y"] += state["dy"]
            if state["y"] < region.y + 4 or state["x"] > region.x + region.width - 4:
                return
        window.event_simulate(type='MOUSEMOVE', value='NOTHING', x=state["x"], y=state["y"])
        steps().insert(0, look)
    return look


def still_there(where, key):
    """A step: the Open button found before is under ``C[key]`` again (the node redrew after its image went), else
    sweep for it again."""
    state = {"n": 0}

    def look():
        window, area, region = where()
        if C.get(key) is None:
            return
        if state["n"]:
            if "image.open" in hover(window, area, region)[1]:
                return
            if state["n"] > 4:
                steps().insert(0, find_open(where, key))
                return
        state["n"] += 1
        area.tag_redraw()
        window.event_simulate(type='MOUSEMOVE', value='NOTHING', x=C[key][0] + state["n"] % 2, y=C[key][1])
        steps().insert(0, look)
    return look


def click(window, pos):
    window.event_simulate(type='MOUSEMOVE', value='NOTHING', x=pos[0], y=pos[1])
    window.event_simulate(type='LEFTMOUSE', value='PRESS', x=pos[0], y=pos[1])
    window.event_simulate(type='LEFTMOUSE', value='RELEASE', x=pos[0], y=pos[1])


def save_png(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = bpy.data.images.new(os.path.basename(path), 8, 8)
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)


def tex_node(tree):
    return next(n for n in tree.nodes if n.type == 'TEX_IMAGE')


def frame_node(window, area, tree):
    """Only the Image Texture node selected and framed (fills the editor)."""
    node = tex_node(tree)
    for n in tree.nodes:
        n.select = False
    node.select = True
    tree.nodes.active = node
    region = next(r for r in area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=window, area=area, region=region):
        bpy.ops.node.view_selected()


def invoke_in(window, area, op):
    region = next(r for r in area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=window, area=area, region=region):
        return op('INVOKE_DEFAULT')


def main_area():
    return next((a for a in win().screen.areas if a.as_pointer() == C["main"]), None)


# --- scene -----------------------------------------------------------------------------------------------------

@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    shutil.rmtree(ROOT, ignore_errors=True)
    project = mod(".operators.project")
    project.create_project(PROJ)
    project.create_project(BARE)
    os.rmdir(os.path.join(BARE, "sourceimages"))
    project.set_current(PROJ)
    save_png(os.path.join(SRC, "tex349.png"))
    save_png(os.path.join(OTHER, "other349.png"))
    area, region = view3d()
    C["main"] = area.as_pointer()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CUBE')
    ob = bpy.context.active_object
    mat = mod(".operators.material").new_material('STANDARD_SURFACE')
    mod(".operators.shading_maps").build(mat, "Base Color", 'FILE')
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    C["mat"], C["ob"] = mat.name, ob.name
    with bpy.context.temp_override(window=win()):
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SCENES, "shot349.blend"))
    check(f"set-up: the scene is saved in <project>/scenes, Preferences > File Paths > Textures is "
          f"{bpy.context.preferences.filepaths.texture_directory!r}, the material's Color has an empty File node",
          norm(os.path.dirname(bpy.data.filepath)) == norm(SCENES)
          and bpy.context.preferences.filepaths.texture_directory == "//"
          and tex_node(mat.node_tree).image is None)
    area.ui_type = 'ShaderNodeTree'


# --- main window Shader Editor: the node's Open button -------------------------------------------------------

@step
def s_frame_main():
    frame_node(win(), main_area(), bpy.data.materials[C["mat"]].node_tree)


def _main_where():
    area = main_area()
    return win(), area, next(r for r in area.regions if r.type == 'WINDOW')


steps().append(find_open(_main_where, "main_open"))


@step
def s_click_main():
    check(f"the Image Texture node's Open button found in the Shader Editor ({C.get('main_open')})",
          C.get("main_open") is not None)
    if C.get("main_open"):
        click(win(), C["main_open"])


@step
def s_main_browser():
    if wait_browser(s_main_browser):
        return
    got = browser_dir()
    w, _a = file_browser()
    check(f"Shader Editor node Open (New Window browser): the browser starts in <project>/sourceimages "
          f"(got {got}, Blender's own start = {norm(SCENES)})", got == norm(SRC))
    C["new_window"] = w is not None and w != win()
    check("the file browser is a window of its own (Preferences default)", C["new_window"])


@step
def s_main_pick():
    w, a = file_browser()
    if a is None:
        return
    if browser_dir() != norm(SRC):     # tex349.png isn't there: leave the browser, the later checks start clean
        C["exec"] = "not in sourceimages"
        close_browser()
        return
    a.spaces.active.params.filename = "tex349.png"
    region = next(r for r in a.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=w, area=a, region=region):
        C["exec"] = bpy.ops.file.execute()


@step
def s_main_loaded():
    if again(s_main_loaded, lambda: tex_node(bpy.data.materials[C["mat"]].node_tree).image is not None, 10):
        return
    img = tex_node(bpy.data.materials[C["mat"]].node_tree).image
    path = img.filepath if img else ""
    check(f"picking tex349.png there loads it from sourceimages into the node ({C.get('exec')}, {path!r})",
          img is not None and norm(bpy.path.abspath(path)) == norm(os.path.join(SRC, "tex349.png")))
    tex_node(bpy.data.materials[C["mat"]].node_tree).image = None
    bpy.context.preferences.view.filebrowser_display_type = 'SCREEN'


steps().append(still_there(_main_where, "main_open"))


@step
def s_click_screen():
    if C.get("main_open"):
        click(win(), C["main_open"])


@step
def s_screen_browser():
    if wait_browser(s_screen_browser):
        return
    got = browser_dir()
    w, _a = file_browser()
    check(f"File Browser = Maximized Area: the browser (in the main window: {w == win()}) starts in sourceimages "
          f"(got {got})", got == norm(SRC) and w == win())
    close_browser()


@step
def s_bare_prep():
    if again(s_bare_prep, lambda: file_browser()[0] is None, 10):
        return
    bpy.context.preferences.view.filebrowser_display_type = 'WINDOW'
    mod(".operators.project").set_current(BARE)


steps().append(still_there(_main_where, "main_open"))


@step
def s_bare_click():
    if C.get("main_open"):
        click(win(), C["main_open"])


@step
def s_bare_browser():
    if wait_browser(s_bare_browser):
        return
    got = browser_dir()
    check(f"a project without sourceimages: Blender's own start folder, the scene's folder (got {got})",
          got == norm(SCENES))
    check("the missing sourceimages folder is not made", not os.path.exists(os.path.join(BARE, "sourceimages")))
    close_browser()
    mod(".operators.project").set_current(PROJ)


# --- Image Editor ----------------------------------------------------------------------------------------------

@step
def s_image_editor():
    if again(s_image_editor, lambda: file_browser()[0] is None, 10):
        return
    area = main_area()
    area.ui_type = 'IMAGE_EDITOR'
    area.spaces.active.image = None


@step
def s_image_empty():
    C["ie_empty"] = invoke_in(win(), main_area(), bpy.ops.image.open)


@step
def s_image_empty_browser():
    if wait_browser(s_image_empty_browser):
        return
    got = browser_dir()
    check(f"Image Editor > Open with no image ({C.get('ie_empty')}): sourceimages (got {got})", got == norm(SRC))
    close_browser()


@step
def s_image_full():
    if again(s_image_full, lambda: file_browser()[0] is None, 10):
        return
    area = main_area()
    area.spaces.active.image = bpy.data.images.load(os.path.join(OTHER, "other349.png"))
    C["ie_full"] = invoke_in(win(), area, bpy.ops.image.open)


@step
def s_image_full_browser():
    if wait_browser(s_image_full_browser):
        return
    got = browser_dir()
    check(f"Image Editor > Open showing an image: that image's folder, as before (got {got})", got == norm(OTHER))
    close_browser()


# --- Dome Light -------------------------------------------------------------------------------------------------

@step
def s_view3d():
    if again(s_view3d, lambda: file_browser()[0] is None, 10):
        return
    area = main_area()
    area.spaces.active.image = None
    area.ui_type = 'VIEW_3D'


@step
def s_dome():
    C["dome"] = invoke_in(win(), main_area(), bpy.ops.allset.dome_light)


@step
def s_dome_browser():
    if wait_browser(s_dome_browser):
        return
    got = browser_dir()
    check(f"Create > Lights > Dome Light ({C.get('dome')}): the image browser starts in sourceimages (got {got})",
          got == norm(SRC))
    close_browser()


# --- Attribute Editor File row ----------------------------------------------------------------------------------

@step
def s_ae():
    if again(s_ae, lambda: file_browser()[0] is None, 10):
        return
    ob = bpy.data.objects[C["ob"]]
    for o in bpy.context.view_layer.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    wm = bpy.context.window_manager
    wm.allset_ae_tab, wm.allset_ae_kind = "MAT:0", "MAT"
    C["dock"] = dock_area('ATTRIBUTE_EDITOR').as_pointer()


def _dock_where():
    area = next(a for a in win().screen.areas if a.as_pointer() == C["dock"])
    return win(), area, next(r for r in area.regions if r.type == 'WINDOW')


@step
def s_ae_redraw():
    for a in win().screen.areas:
        a.tag_redraw()


steps().append(find_open(_dock_where, "ae_open"))


@step
def s_ae_click():
    shot("gui_issue349_ae.png")
    check(f"the Attribute Editor's File row Open button found ({C.get('ae_open')})", C.get("ae_open") is not None)
    if C.get("ae_open"):
        click(win(), C["ae_open"])


@step
def s_ae_browser():
    if wait_browser(s_ae_browser):
        return
    got = browser_dir()
    check(f"Attribute Editor File row Open: sourceimages (got {got})", got == norm(SRC))
    close_browser()


# --- Hypershade graph -------------------------------------------------------------------------------------------

def hs_ready():
    hs = mod(".ui.hypershade")
    for w in bpy.context.window_manager.windows[1:]:
        if hs.is_hypershade(w.screen) and hs.graph_area(w.screen) is not None:
            return w
    return None


@step
def s_hypershade():
    if again(s_hypershade, lambda: file_browser()[0] is None, 10):
        return
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        C["hs"] = mod(".marking.modal").run_action(bpy.context,
                                                   mod(".ui.menu_map").MAP["Windows/Rendering Editors/Hypershade"])


@step
def s_hs_frame():
    if again(s_hs_frame, lambda: hs_ready() is not None, 60):
        return
    w = hs_ready()
    check(f"Windows > Rendering Editors > Hypershade opens its window ({C.get('hs')})", w is not None)
    if w is None:
        steps().clear()
        return
    C["hs_win"] = w.as_pointer()
    graph = mod(".ui.hypershade").graph_area(w.screen)
    space = graph.spaces.active
    tree = space.node_tree
    check(f"the Hypershade graph shows the material ({tree.name if tree else None})",
          tree is not None and tree == bpy.data.materials[C["mat"]].node_tree)
    if tree is not None:
        frame_node(w, graph, tree)


def _hs_where():
    w = next(x for x in bpy.context.window_manager.windows if x.as_pointer() == C["hs_win"])
    graph = mod(".ui.hypershade").graph_area(w.screen)
    return w, graph, next(r for r in graph.regions if r.type == 'WINDOW')


steps().append(find_open(_hs_where, "hs_open"))


@step
def s_hs_click():
    shot("gui_issue349_hypershade.png", _hs_where()[0])
    check(f"the node's Open button found in the Hypershade graph ({C.get('hs_open')})", C.get("hs_open") is not None)
    if C.get("hs_open"):
        click(_hs_where()[0], C["hs_open"])


@step
def s_hs_browser():
    if wait_browser(s_hs_browser):
        return
    got = browser_dir()
    check(f"Hypershade graph node Open: sourceimages (got {got})", got == norm(SRC))
    close_browser()


# --- Maya mode off ----------------------------------------------------------------------------------------------

@step
def s_maya_off():
    if again(s_maya_off, lambda: file_browser()[0] is None, 10):
        return
    mod(".switch").set_mode(False)


@step
def s_off_open():
    # Maya mode off leaves the Maya layout over a few ticks: open from the largest area once it is a node editor
    area = max(win().screen.areas, key=lambda a: a.width * a.height)
    if area.ui_type != 'ShaderNodeTree':
        area.ui_type = 'ShaderNodeTree'
    if again(s_off_open, lambda: C.get("off_seen") == (win().screen.as_pointer(), area.as_pointer()), 10):
        C["off_seen"] = (win().screen.as_pointer(), area.as_pointer())
        return
    C["off_maya"] = mod(".switch").is_on()
    C["off"] = invoke_in(win(), area, bpy.ops.image.open)


@step
def s_off_browser():
    if wait_browser(s_off_browser):
        return
    got = browser_dir()
    check(f"Maya mode off (on: {C.get('off_maya')}, {C.get('off')}): Blender's own start folder, the scene's folder "
          f"(got {got})", got == norm(SCENES) and C.get("off_maya") is False)
    close_browser()


@step
def s_back_on():
    if again(s_back_on, lambda: file_browser()[0] is None, 10):
        return
    mod(".switch").set_mode(True, layout=False)


run(interval=0.15)
