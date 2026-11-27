"""Hypershade Create pane, Blender section (#577): Blender's own shader nodes beside the Maya section, a shader click
makes a material with that shader, any other node goes into the current material's graph."""

from importlib import import_module

import bpy

import kit
from test_step67_render import Rec

N = "ShaderNode"


def _bl():
    return import_module(kit.MODULE + ".ui.hypershade_blender")


def _hs():
    return import_module(kit.MODULE + ".ui.hypershade")


def _material_node_types():
    """Every shader node type a material can hold in this Blender (made and removed again)."""
    mat = bpy.data.materials.new("probe")
    try:
        try:
            mat.use_nodes = True
        except AttributeError:
            pass
        tree = mat.node_tree
        found = set()
        for idname in dir(bpy.types):
            if not idname.startswith(N):
                continue
            try:
                tree.nodes.remove(tree.nodes.new(idname))
                found.add(idname)
            except RuntimeError:
                pass
        return found
    finally:
        bpy.data.materials.remove(mat)


def test_every_material_node_is_listed_once():
    bl = _bl()
    listed = [idname for idname, _label in bl.items("BLENDER")]
    assert len(listed) == len(set(listed))
    expected = {t for t in _material_node_types() if t not in bl.EXCLUDED and "Internal" not in t}
    assert set(listed) == expected, (sorted(expected - set(listed)), sorted(set(listed) - expected))
    # the known ones sit in Blender's Add menu categories; nothing known falls into Other
    assert not [t for t in bl.items("BL_OTHER") if t[0] in bl.CATEGORY_OF]
    labels = dict(bl.items("BLENDER"))
    assert labels[N + "BsdfPrincipled"] == "Principled BSDF" and labels[N + "TexVoronoi"] == "Voronoi Texture"
    assert N + "TexVoronoi" in dict(bl.items("BL_TEXTURE")) and N + "ValToRGB" in dict(bl.items("BL_UTILITIES"))


def test_a_new_node_type_still_shows_under_other():
    bl = _bl()
    assert bl._category(N + "SomethingNew") == "BL_OTHER"
    assert bl._category(N + "TexSomethingNew") == "BL_TEXTURE"


def test_create_tree_has_the_blender_section_after_maya():
    hs = _hs()
    keys = [c[0] for c in hs.CREATE_CATEGORIES]
    assert keys[:2] == ["FAVORITES", "MAYA"] and keys.index("BLENDER") > keys.index("RENDERING")
    assert not [k for k in hs.MAYA_KEYS if k.startswith("BL_") or k == "BLENDER"]
    assert hs.create_items("BL_SHADER") == [] and hs.create_items("MAYA")


def test_create_pane_lists_and_searches_blender_nodes():
    hs = _hs()
    wm = bpy.context.window_manager
    try:
        wm.allset_hs_create_cat = 'BL_SHADER'
        rec = Rec()
        hs.draw_create(rec, bpy.context)
        shaders = [p.node_type for i, p in rec.ops() if i == "allset.hs_shader"]
        assert N + "BsdfPrincipled" in shaders and N + "Emission" in shaders and N + "VolumePrincipled" in shaders
        wm.allset_hs_create_cat = 'BL_TEXTURE'
        rec = Rec()
        hs.draw_create(rec, bpy.context)
        assert N + "TexVoronoi" in [p.node_type for i, p in rec.ops() if i == "allset.hs_node"]
        # search: Maya and Blender node types together
        wm.allset_hs_create_cat = 'MAYA'
        wm.allset_hs_create_filter = "voronoi"
        rec = Rec()
        hs.draw_create(rec, bpy.context)
        assert [p.node_type for i, p in rec.ops() if i == "allset.hs_node"] == [N + "TexVoronoi"]
        wm.allset_hs_create_filter = "checker"
        rec = Rec()
        hs.draw_create(rec, bpy.context)
        ops = rec.ops()
        assert any(i == "allset.menu_item" and p.item.endswith("/Checker") for i, p in ops)
        assert N + "TexChecker" in [p.node_type for i, p in ops if i == "allset.hs_node"]
    finally:
        wm.allset_hs_create_filter = ""
        wm.allset_hs_create_cat = 'MAYA'


def _surface(mat, socket="Surface"):
    out = next(n for n in mat.node_tree.nodes if n.bl_idname == N + "OutputMaterial")
    links = out.inputs[socket].links
    return links[0].from_node.bl_idname if links else None


def test_shader_click_makes_a_material_with_that_shader():
    before = set(bpy.data.materials)
    assert bpy.ops.allset.hs_shader(node_type=N + "Emission") == {'FINISHED'}
    mat = (set(bpy.data.materials) - before).pop()
    assert mat.name.startswith("Material") and mat.use_fake_user
    assert _surface(mat) == N + "Emission"
    assert not [n for n in mat.node_tree.nodes if n.bl_idname == N + "BsdfPrincipled"]
    assert bpy.context.window_manager.allset_hs_material == mat.name
    # a volume shader goes into Volume; Principled = Blender's new material as it is
    assert bpy.ops.allset.hs_shader(node_type=N + "VolumePrincipled") == {'FINISHED'}
    vol = bpy.data.materials[bpy.context.window_manager.allset_hs_material]
    assert _surface(vol, "Volume") == N + "VolumePrincipled" and _surface(vol) is None
    assert bpy.ops.allset.hs_shader(node_type=N + "BsdfPrincipled") == {'FINISHED'}
    pr = bpy.data.materials[bpy.context.window_manager.allset_hs_material]
    assert _surface(pr) == N + "BsdfPrincipled"


def test_shader_click_refuses_a_non_shader():
    try:
        bpy.ops.allset.hs_shader(node_type=N + "TexVoronoi")
    except RuntimeError:
        return
    raise AssertionError("a texture node made a material")


def test_other_node_click_adds_it_to_the_current_material():
    bpy.ops.allset.hs_shader(node_type=N + "BsdfDiffuse")
    mat = bpy.data.materials[bpy.context.window_manager.allset_hs_material]
    count = len(mat.node_tree.nodes)
    assert bpy.ops.allset.hs_node(node_type=N + "TexVoronoi") == {'FINISHED'}
    assert len(mat.node_tree.nodes) == count + 1
    assert mat.node_tree.nodes.active.bl_idname == N + "TexVoronoi"
