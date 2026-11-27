"""Hypershade graph hands (the Hypershade Graph and every material Shader Editor): RMB = Maya's graph marking menus by
the node under the mouse (empty graph / material / texture / utility / shading group), Tab = the create-node field
(node made where the mouse was, selected), keys 1 / 2 / 3 / 4 view modes, / , . stream selection, Shift+? < > graph
the stream. Other node trees keep Blender's keys. GUI: tests/gui/gui_hypershade_hands.py."""

from importlib import import_module

import bpy

import kit

marking = import_module(kit.MODULE + ".marking")
mm = import_module(kit.MODULE + ".marking.menus")
hands = import_module(kit.MODULE + ".ui.hypershade_hands")
notices = import_module(kit.MODULE + ".ui.notices")


def _scene():
    """A cube with a material: Principled -> Output, Image Texture -> Base Color, Mapping -> Image Texture, plus a
    lone Math node. Returns (object, material, nodes by role)."""
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    me = bpy.data.meshes.new("cube")
    ob = bpy.data.objects.new("pCube1", me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    mat = bpy.data.materials.new("blinn1")
    kit_compat = import_module(kit.MODULE + ".compat")
    kit_compat.ensure_material_nodes(mat)
    ob.data.materials.append(mat)
    tree = mat.node_tree
    bsdf = next(n for n in tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
    out = next(n for n in tree.nodes if n.bl_idname == "ShaderNodeOutputMaterial")
    tex = tree.nodes.new("ShaderNodeTexImage")
    mapping = tree.nodes.new("ShaderNodeMapping")
    math = tree.nodes.new("ShaderNodeMath")
    tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    tree.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    return ob, mat, {"bsdf": bsdf, "out": out, "tex": tex, "mapping": mapping, "math": math}


def _shader_area(tree=None, tree_type="ShaderNodeTree"):
    """The biggest area as a Shader Editor; ``tree`` is pinned so the editor shows it (a background session draws
    nothing, so the editor never picks the active object's material by itself)."""
    win = bpy.context.window_manager.windows[0]
    area = max(win.screen.areas, key=lambda a: a.width * a.height)
    area.type = 'NODE_EDITOR'
    space = area.spaces.active
    space.tree_type = tree_type
    if tree is not None:
        space.pin = True
        space.node_tree = tree
    return win, area, space


def _override(win, area):
    region = next(r for r in area.regions if r.type == 'WINDOW')
    return bpy.context.temp_override(window=win, screen=win.screen, area=area, region=region,
                                     space_data=area.spaces.active)


def test_menus_follow_maya_layout():
    radial = {name: {k: v[0] for k, v in mm.MENUS[name].radial.items()} for name in
              ("NODE_EMPTY", "NODE_MATERIAL", "NODE_TEXTURE", "NODE_OUTPUT")}
    assert radial["NODE_EMPTY"] == {"N": "Create Node...", "E": "Select All in Graph", "W": "Select Items in Stream",
                                    "SE": "Remove Material Soloing", "SW": "Solo Last Connection",
                                    "S": "Graph Materials on Viewport Selection"}, radial["NODE_EMPTY"]
    assert radial["NODE_MATERIAL"] == {"SW": "Refresh Swatch", "N": "Assign Material To Viewport Selection",
                                       "NE": "Paint Assign Shader", "E": "Select Objects with Material", "S": "Solo",
                                       "SE": "Remove Material Soloing"}, radial["NODE_MATERIAL"]
    assert radial["NODE_TEXTURE"]["N"] == "Assign Texture's Material to Viewport Selection"
    assert radial["NODE_TEXTURE"]["W"] == "Test Texture" and radial["NODE_TEXTURE"]["E"] == "Render Texture Range"
    assert radial["NODE_OUTPUT"] == {"N": "Regraph Stream Nodes", "E": "Remove Stream Nodes"}
    labels = [e[0] for e in mm.MENUS["NODE_MATERIAL"].items if e != mm.DIVIDER]
    assert labels == [mm.NODE_TITLE, "Frame Objects with Material", "Inputs", "Outputs", "Rename",
                      "Toggle Swatch Size", "Toggle Selection Swatch Size", "Edit Custom Attribute List",
                      "Show All Attributes", "Add Attributes...", "Delete Attributes...", mm.NODE_HELP], labels
    for path, _label in mm.greyed_entries():
        if path.startswith("NODE_"):
            assert path in notices.MARKING, path


def test_menu_kind_by_node():
    _ob, _mat, n = _scene()
    kinds = {k: hands.menu_kind(v) for k, v in n.items()}
    assert kinds == {"bsdf": "NODE_MATERIAL", "out": "NODE_OUTPUT", "tex": "NODE_TEXTURE", "mapping": "NODE_UTILITY",
                     "math": "NODE_UTILITY"}, kinds
    assert hands.menu_kind(None) == "NODE_EMPTY"


def test_resolve_in_a_shader_editor_only():
    ob, mat, n = _scene()
    win, area, space = _shader_area(mat.node_tree)
    wm = bpy.context.window_manager
    with _override(win, area):
        assert hands.shader_space(bpy.context) is not None
        wm.allset_mm_node = ""
        assert marking.resolve("RMB", bpy.context) == ("pie", marking.idname("NODE_EMPTY"))
        wm.allset_mm_node = n["tex"].name
        assert marking.resolve("RMB", bpy.context) == ("pie", marking.idname("NODE_TEXTURE"))
        wm.allset_mm_node = n["out"].name
        assert marking.resolve("RMB", bpy.context) == ("pie", marking.idname("NODE_OUTPUT"))
        assert marking.resolve("SHIFT_RMB", bpy.context) is None
    space.tree_type = "GeometryNodeTree"
    with _override(win, area):
        assert hands.shader_space(bpy.context) is None
        assert marking.resolve("RMB", bpy.context) is None, "Geometry Nodes keep Blender's context menu"


def test_filled_menu_lists_the_node():
    ob, mat, n = _scene()
    win, area, _space = _shader_area(mat.node_tree)
    bpy.context.window_manager.allset_mm_node = n["bsdf"].name
    with _override(win, area):
        menu = hands.fill_menu(mm.MENUS["NODE_MATERIAL"], bpy.context)
    labels = [e[0] for e in menu.items if e != mm.DIVIDER]
    assert labels[0] == f"{n['bsdf'].name}...", labels
    assert labels[-1] == 'Help on "Principled BSDF"', labels
    inputs = dict((e[0], e[1]) for e in menu.items if e != mm.DIVIDER)["Inputs"]
    rows = [e[0] for e in inputs.items if e != mm.DIVIDER]
    # Maya: Select / Enable / Disable All, then the node itself and the nodes feeding it, by type name
    assert rows[:3] == ["Select All Inputs", "Enable All Inputs", "Disable All Inputs"], rows
    assert rows[3:] == ["Principled BSDF", "Image Texture", "Mapping"], rows


def test_node_commands():
    ob, mat, n = _scene()
    win, area, _space = _shader_area(mat.node_tree)
    wm = bpy.context.window_manager
    tree = mat.node_tree
    with _override(win, area):
        wm.allset_mm_node = n["bsdf"].name
        assert bpy.ops.allset.hs_node_cmd(action="ALL_INPUTS_SELECT") == {'FINISHED'}
        assert {x.name for x in tree.nodes if x.select} == {n["bsdf"].name, n["tex"].name, n["mapping"].name}
        bpy.ops.allset.hs_node_cmd(action="ALL_INPUTS_DISABLE")
        assert n["tex"].mute and n["mapping"].mute and n["bsdf"].mute and not n["math"].mute
        bpy.ops.allset.hs_node_cmd(action="ALL_INPUTS_ENABLE")
        assert not n["tex"].mute
        ob.select_set(False)
        assert bpy.ops.allset.hs_node_cmd(action="SELECT_OBJECTS") == {'FINISHED'}
        assert ob.select_get(), "Select Objects with Material"
        wm.allset_mm_node = n["tex"].name
        bpy.ops.allset.hs_node_cmd(action="SWATCH")
        assert n["tex"].show_preview
        # keys: the selected nodes, not the menu's node
        for x in tree.nodes:
            x.select = x == n["mapping"]
        bpy.ops.allset.hs_node_cmd(action="STREAM_DOWN", selected=True)
        assert {x.name for x in tree.nodes if x.select} == {n["mapping"].name, n["tex"].name, n["bsdf"].name,
                                                            n["out"].name}


def test_tab_lists_blender_and_maya_nodes_and_makes_one_at_the_point():
    ob, mat, n = _scene()
    items = hands._tab_items(None, bpy.context)
    labels = {it[1] for it in items}
    assert {"Image Texture", "Principled BSDF", "Mapping"} <= labels, "Blender names"
    assert {"File", "Ramp", "Checker"} <= labels, "Maya texture names the kit builds"
    tree = mat.node_tree
    key = next(it[0] for it in items if it[1] == "File")
    node = hands.make_node(tree, key, (120.0, -40.0))
    assert node.bl_idname == "ShaderNodeTexImage" and node.label == "File"
    assert tuple(node.location) == (120.0, -40.0)
    assert [x for x in tree.nodes if x.select] == [node] and tree.nodes.active == node


def test_view_modes():
    ob, mat, n = _scene()
    tex = n["tex"]
    hands.set_view_mode([tex], 'CONNECTED')
    shown = [s.name for s in (*tex.inputs, *tex.outputs) if not s.hide]
    assert shown == ["Vector", "Color"], shown
    hands.set_view_mode([tex], 'SIMPLE')
    assert tex.hide
    hands.set_view_mode([tex], 'ALL')
    assert not tex.hide and not any(s.hide for s in (*tex.inputs, *tex.outputs))


def test_keymap_items():
    kc = kit.maya_kc()
    km = kc.keymaps["Node Editor"]
    items = [(k.idname, k.type, k.shift) for k in km.keymap_items if k.active]
    rmb = [k for k in km.keymap_items if k.type == 'RIGHTMOUSE' and k.value == 'PRESS' and not k.ctrl
           and not k.shift and not k.alt]
    assert rmb and rmb[0].idname == "allset.marking_menu", [k.idname for k in rmb]
    for want in (("allset.hs_view_mode", 'ONE', False), ("allset.hs_view_mode", 'THREE', False),
                 ("allset.hs_node_cmd", 'COMMA', False), ("allset.hs_node_cmd", 'PERIOD', True),
                 ("view2d.zoom_in", 'EQUAL', False)):
        assert want in items, want
    tab = [k for k in kc.keymaps["Node Generic"].keymap_items if k.type == 'TAB' and k.active]
    assert tab and tab[0].idname == "allset.hs_tab_create", [k.idname for k in tab]
