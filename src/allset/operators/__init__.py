# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya-behaviour operators (group, pick-walk, hold/tap snap, pivot, freeze, parent,
duplicate, delete history, create, visibility, ...).

Operator ids use the ``allset.`` prefix. Each module lists its classes in
``classes``; they are registered in that order.
"""

import bpy

from . import (auto_key, bookmarks, component, create, curve_tools, curves_maya, cut_sew, display, driven_key, duplicate, extrude, file_io, freeze, option_windows, fx, global_keys4, graph_keys, graph_key_menu, deformer_weights, joint_labels, group, history, hold, joints, pivot_menu, key_batch, key_batch3, key_insert, loop_pick, manip, marquee,
               anim_layers, lights, light_links, material, menu_extras, menu_items, mesh_maya, multi_cut, poly_maya, rig_maya, mesh_tools, outliner_drag, parenting, pickwalk, pivot, playblast, preselect, project, render_persp, rig_tools, select_convert, select_priority, sets, shading_maps, skin, snap_align, soft_select, symmetry, taphold,
               time_keys, tool_keys, units, uv_shells, uv_tools, uv_modify, uv_select_178, view, view_keys3, visibility)
from . import poly_draw, quad_draw  # step 144 POLY: Create Polygon / Append to Polygon / Quad Draw (#30)
from . import edge_loops  # step 144 LOOP: Insert / Offset Edge Loop, Slide Edge (#31)

classes = (*display.classes, *group.classes, *hold.classes, *taphold.classes,
           *pickwalk.classes, *view.classes, *freeze.classes, *parenting.classes,
           *duplicate.classes, *history.classes, *create.classes, *visibility.classes,
           *component.classes, *manip.classes, *material.classes,
           *marquee.classes, *preselect.classes, *select_priority.classes, *menu_extras.classes,
           *tool_keys.classes, *symmetry.classes, *pivot.classes, *snap_align.classes, *time_keys.classes,
           *joints.classes, *skin.classes, *driven_key.classes, *rig_tools.classes, *mesh_maya.classes,
           *mesh_tools.classes, *extrude.classes, *uv_tools.classes, *uv_shells.classes, *uv_modify.classes, *light_links.classes, *anim_layers.classes, *uv_select_178.classes, *shading_maps.classes, *fx.classes, *project.classes, *graph_keys.classes, *graph_key_menu.classes, *deformer_weights.classes, *joint_labels.classes, *playblast.classes, *key_batch.classes, *cut_sew.classes, *multi_cut.classes,
           *outliner_drag.classes, *key_insert.classes, *view_keys3.classes, *global_keys4.classes,
           *pivot_menu.classes, *sets.classes, *menu_items.classes, *file_io.classes, *option_windows.classes,
           *key_batch3.classes, *bookmarks.classes, *curve_tools.classes, *curves_maya.classes,
           *poly_maya.classes, *rig_maya.classes, *loop_pick.classes,
           *render_persp.classes, *select_convert.classes, *poly_draw.classes, *quad_draw.classes,
           *edge_loops.classes)

from . import deformers  # noqa: E402  step 144 DEFORM: Maya Deform menu deformers + Paint Weights (#34)

classes += deformers.classes

from . import default_light, render_batch  # noqa: E402  step 152 RENDER: default light, Test Resolution, Batch (#101)

classes += render_batch.classes

from . import curve_draw  # noqa: E402  step 156 lane T: CV / EP Curve Tool, Three / Two Point Circular Arc

classes += curve_draw.classes

from . import dag  # noqa: E402  step 164: Maya DAG rules for parents (hide / delete / export / isolate)

classes += dag.classes

from . import by_type  # noqa: E402  step 166: Select All by Type for the kit's IK handles / clusters / particles

classes += by_type.classes

from . import modify_maya  # noqa: E402  step 168: Modify menu (Smooth Mesh Preview to Polygons, Evaluate Nodes, ...)

classes += modify_maya.classes

from . import deform_edit  # noqa: E402  step 169: Deform > Wire / ShrinkWrap / Lattice edits, Prune, Point On Curve

classes += deform_edit.classes

from . import select_2d  # noqa: E402  step 170: Maya click / marquee modifiers in Graph / Dope Sheet / UV

classes += select_2d.classes

from . import anim_snapshot  # noqa: E402  step 171: Visualize > Create Animation Snapshot / Update Snapshot

classes += anim_snapshot.classes

from . import repeat_maya  # noqa: E402  step 175: Maya G / Edit > Repeat / Recent Commands for menu commands

classes += repeat_maya.classes

from . import surfaces_maya  # noqa: E402  step 181: Maya Surfaces menu on NURBS surfaces

classes += surfaces_maya.classes

_register_classes, _unregister_classes = bpy.utils.register_classes_factory(classes)


def register():
    _register_classes()
    default_light.register()
    snap_align.register_props()
    material.register_props()
    lights.register_props()
    light_links.register_props()
    anim_layers.register_props()
    driven_key.register_props()
    mesh_tools.register_props()
    poly_draw.register_props()
    edge_loops.register_props()
    extrude.register_handlers()
    uv_tools.register_props()
    fx.register_props()
    taphold.register_bindings()
    graph_keys.register_bindings()
    graph_key_menu.register_bindings()
    deformer_weights.register_bindings()
    joint_labels.register_bindings()
    pivot_menu.register_props()
    sets.register_props()
    view.register_timer()
    units.register_handler()
    tool_keys.register_timer()
    symmetry.register_handler()
    soft_select.register_handlers()
    pivot.register_handler()
    project.register_handlers()
    preselect.register_handlers()
    cut_sew.register_handlers()
    multi_cut.register_handlers()
    poly_draw.register_handlers()
    quad_draw.register_handlers()
    outliner_drag.register_handlers()
    material.register_handlers()
    auto_key.register_handlers()
    dag.register_handlers()
    modify_maya.register_props()
    anim_snapshot.register_handlers()
    repeat_maya.register_handlers()


def unregister():
    repeat_maya.unregister_handlers()
    anim_snapshot.unregister_handlers()
    select_2d.unregister_timers()
    modify_maya.unregister_props()
    dag.unregister_handlers()
    curve_draw.unregister_handlers()
    auto_key.unregister_handlers()
    material.unregister_handlers()
    outliner_drag.unregister_handlers()
    quad_draw.unregister_handlers()
    poly_draw.unregister_handlers()
    multi_cut.unregister_handlers()
    cut_sew.unregister_handlers()
    project.unregister_handlers()
    pivot.unregister_handler()
    soft_select.unregister_handlers()
    symmetry.unregister_handler()
    tool_keys.unregister_timer()
    marquee.restore_all()
    preselect.clear()
    units.unregister_handler()
    duplicate.PAIRS.clear()
    view.unregister_timer()
    hold.unregister_cleanup()
    joint_labels.unregister_bindings()
    deformer_weights.unregister_bindings()
    graph_key_menu.unregister_bindings()
    graph_keys.unregister_bindings()
    sets.unregister_props()
    pivot_menu.unregister_props()
    taphold.unregister_bindings()
    fx.unregister_props()
    anim_layers.unregister_props()
    light_links.unregister_props()
    lights.unregister_props()
    material.unregister_props()
    uv_tools.unregister_props()
    extrude.unregister_handlers()
    mesh_tools.clear()
    edge_loops.unregister_props()
    edge_loops.clear()
    poly_draw.unregister_props()
    mesh_tools.unregister_props()
    driven_key.unregister_props()
    snap_align.unregister_props()
    render_batch.unregister()
    default_light.unregister()
    _unregister_classes()

