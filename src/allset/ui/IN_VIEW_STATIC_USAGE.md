# StaticInViewOperator — Usage Guide

## Purpose

`StaticInViewOperator` is a Python mixin that defines the lifecycle contract for
one-shot operators which are intended to use Blender's official Maya In-View
HUD implementation.

It is **not** a HUD renderer, parameter widget system, or standalone modal tool.
The `ui.in_view` module remains the single owner of HUD drawing, hit testing,
parameter interaction, and viewport event routing. Do not add a second draw
handler or duplicate the HUD's mouse/keyboard interaction logic in an operator.

> **Integration status:** the current In-View HUD is still driven by the
> Extrude/Bevel operation records. `StaticInViewOperator` establishes the
> reusable operator-side contract, but arbitrary operator properties are not
> automatically displayed by the current HUD. A concrete implementation must
> connect to the generic session adapter owned by `ui.in_view` when that adapter
> is implemented. Do not treat the hook contract alone as a completed HUD
> integration.

## Import and inheritance

Import the mixin from the UI package and place it before `bpy.types.Operator` in
the inheritance list:

```python
import bpy
from ..ui.in_view_static import StaticInViewOperator


class MESH_OT_example(StaticInViewOperator, bpy.types.Operator):
    bl_idname = "mesh.example_in_view"
    bl_label = "Example In-View Operation"
    bl_options = {'REGISTER', 'UNDO'}
```

The mixin itself is not a Blender operator and must not be registered. Register
only the concrete operator class using the add-on's normal registration flow.

## Required hooks

| Hook | Responsibility |
|---|---|
| `in_view_params(context)` | Return declarative parameter descriptors in the format accepted by the official In-View adapter. |
| `in_view_begin(context, event)` | Initialize operation state and connect it to the official In-View HUD session. Store any session handle on `self`. |
| `in_view_process_event(context, event)` | Forward events to the official In-View HUD session and return its modal result. |
| `in_view_execute(context)` | Commit the one-shot operation exactly once after confirmation. |
| `in_view_cancel(context)` | Release preview geometry, temporary data, and adapter state. This hook should be safe to call after partial initialization. |

`in_view_process_event` must return one of the following:

- `None` or `{'RUNNING_MODAL'}` — keep the operation active.
- `{'FINISHED'}` — confirm the operation; the mixin calls `in_view_execute`.
- `{'CANCELLED'}` — cancel the operation; the mixin calls `in_view_cancel`.

The mixin handles the modal lifecycle only. It does not define parameter
formats, draw the HUD, or decide how a particular mesh operation is calculated.

## Implementation template

The following is a structural template. The `official_in_view_adapter` calls
are intentionally marked as integration points: replace them with the public
session functions exposed by `ui.in_view` once the generic session API is
available. Do not implement those functions as a second HUD engine.

```python
import bpy
from ..ui.in_view_static import StaticInViewOperator, selection_anchor


class MESH_OT_example(StaticInViewOperator, bpy.types.Operator):
    bl_idname = "mesh.example_in_view"
    bl_label = "Example In-View Operation"
    bl_options = {'REGISTER', 'UNDO'}

    amount: bpy.props.FloatProperty(
        name="Amount",
        default=1.0,
        min=0.0,
    )

    def in_view_params(self, context):
        # Return descriptors using the official In-View adapter's schema.
        return [
            {
                "identifier": "amount",
                "label": "Amount",
                "data_type": "FLOAT",
                "value": self.amount,
            },
        ]

    def in_view_begin(self, context, event):
        self._anchor = selection_anchor(context)
        self._preview_data = None
        # TODO: Create a session through the official ui.in_view adapter.
        # self._in_view_session = in_view.begin_operator_session(...)
        raise NotImplementedError("Connect this operator to ui.in_view session API")

    def in_view_process_event(self, context, event):
        # TODO: Forward the event to the official ui.in_view session.
        # return in_view.process_operator_event(self._in_view_session, context, event)
        raise NotImplementedError("Connect this operator to ui.in_view session API")

    def in_view_execute(self, context):
        # Apply the final operation using the confirmed property values.
        pass

    def in_view_cancel(self, context):
        # Remove temporary preview data and release the session if it exists.
        session = getattr(self, "_in_view_session", None)
        if session is not None:
            # TODO: Close the session through the official ui.in_view adapter.
            pass
```

The `NotImplementedError` lines are deliberate safeguards in this template:
they prevent a copied example from appearing to work while no generic session
API is connected. Replace them only after the official adapter API is present.

## Selection anchor helper

`selection_anchor(context)` returns a world-space point suitable as an initial
HUD anchor:

1. Selected faces take priority; their median centres are averaged.
2. If no faces are selected, selected edge midpoints are averaged.
3. If neither faces nor edges are selected, selected vertex positions are
   averaged.
4. If there is no mesh selection, the active object's world translation is
   returned.
5. If there is no active object, the function returns `None`.

This helper only calculates a point. It does not position, draw, or activate a
HUD by itself.

## Design rules

- Keep all HUD rendering and pointer interaction inside `ui.in_view`.
- Keep operation-specific geometry and commit logic inside the concrete tool.
- Use the hook methods as the boundary between the tool and the HUD session.
- Make `in_view_cancel` idempotent and safe after partial initialization.
- Do not register draw handlers, timers, or independent modal HUD operators in
  a concrete subclass unless the official In-View architecture explicitly
  requires them.
