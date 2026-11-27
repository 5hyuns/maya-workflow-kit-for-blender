"""#583: Create > Polygon Primitives (shelf, menu, a custom shelf's Maya menu button) in component mode makes the
primitive and leaves component mode for object mode, like Maya."""

from importlib import import_module

import bpy

import kit

shelf_data = import_module(kit.MODULE + ".ui.shelf_data")
shelf = import_module(kit.MODULE + ".ui.shelf")


def _index(shelf, label):
    for tab in shelf_data.SHELVES:
        if tab[0] == shelf:
            return next(i for i, b in enumerate(tab[2]) if b[0] == label)
    raise KeyError(shelf)


def _cube_in_edit_mode():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_cube_add()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    assert bpy.context.mode == 'EDIT_MESH'
    return bpy.context.active_object


def test_shelf_primitive_from_component_mode():
    for label in ("Polygon Sphere", "Polygon Cube"):
        first = _cube_in_edit_mode()
        res = bpy.ops.allset.shelf_button(shelf="Polygons", index=_index("Polygons", label))
        new = [ob for ob in bpy.data.objects if ob != first]
        print(label, res, bpy.context.mode, [ob.name for ob in new])
        assert res == {'FINISHED'} and len(new) == 1, (label, res, [ob.name for ob in new])
        assert bpy.context.mode == 'OBJECT', bpy.context.mode
        assert bpy.context.view_layer.objects.active == new[0]
        assert first.mode == 'OBJECT'


def test_create_operator_from_component_mode():
    first = _cube_in_edit_mode()
    assert bpy.ops.allset.create(kind='CYLINDER') == {'FINISHED'}
    new = [ob for ob in bpy.data.objects if ob != first]
    assert len(new) == 1 and bpy.context.mode == 'OBJECT', ([ob.name for ob in new], bpy.context.mode)


def test_custom_shelf_create_button_from_component_mode():
    """A button made from a Maya menu item on a custom shelf (Shelf Editor) runs like the menu item."""
    shelf.user_data()["shelves"].append({"name": "Mine583", "buttons": [
        {"label": "Cube", "type": "action", "action": {"type": "maya_menu", "id": "Create/Polygon Primitives/Cube"}},
        {"label": "Light", "type": "action", "action": {"type": "maya_menu", "id": "Create/Lights/Point Light"}}]})
    for index, kind in ((0, 'MESH'), (1, 'LIGHT')):
        first = _cube_in_edit_mode()
        res = bpy.ops.allset.shelf_button(shelf="USER:Mine583", index=index)
        new = [ob for ob in bpy.data.objects if ob != first]
        assert res == {'FINISHED'} and [ob.type for ob in new] == [kind], (index, res, [ob.name for ob in new])
        assert bpy.context.mode == 'OBJECT', bpy.context.mode
