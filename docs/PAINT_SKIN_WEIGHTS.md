# Paint Skin Weights workspace · 0.5.2

Restart Blender after updating the extension. Enable Maya mode, select a skinned mesh, and choose **Skin > Paint Skin Weights**. The Channel Box becomes the painting workspace. The menu's option box opens the same workspace in a wider Tool Settings dock. Double-clicking the paint tool also uses the new Tool Settings interface.

The layout follows Maya's influence-first workflow. Search, hierarchy order, influence selection, and lock controls remain above the three pages. A checkmark in the header finishes painting; Q/W/E/R retain the Maya tool-exit behavior.

## Paint

- Brush Assets: browse Blender's installed weight-paint brush assets and use the native brush asset context menu.
- Replace, Add, Subtract, Scale, Smooth, Average, and Smear; Blender's full native blend selector is in Advanced.
- Value, Opacity, Size, tablet-pressure switches, unified settings, and one-click weight values.
- Flood applies the chosen operation and opacity, preserves locked influences, and respects visible vertices, vertex/face masks, and Existing Weights Only. Smear requires a directional stroke, so Flood is disabled for it.
- Sample Weight, Pick Joint/Group, and Linear/Radial Gradient tools stay inside weight painting.
- Expandable native falloff curves and presets, spherical/projected falloff, front-face restriction, and front-face angle falloff.
- Native stroke methods, airbrush rate, spacing/pressure, dashes, jitter/unit/pressure, Paint Curve creation/drawing, input samples, and stroke stabilization.
- Custom tablet pressure curves for size, opacity, and jitter.
- Auto normalization is remembered per skin. Lock-relative, multi-paint, existing-weight restriction, and size units are available.
- Reflection & symmetry, directly below Brush: X/Y/Z reflection, mirrored influence names, topology matching, and radial symmetry.
- Selection masking: vertex/face switches; select all/none/invert; box/lasso/paint selection; grow/shrink/linked; hide/reveal; and select unweighted vertices.

## Weights

Set Weight, Normalize/Normalize All, Mirror, Invert, Prune/Clean, Quantize, Levels, Smooth, Limit Influences, Transfer, Automatic Weights, and Bone Envelope Weights. Each operation opens its own settings dialog, including the relevant native scope and numerical options. Existing locked influences are protected.

Transfer takes an explicit source mesh, supports native vertex mapping, layer matching, transforms, distance limits, and mix controls, and restores the previous object selection afterward.

The influence menu supports hierarchy/alphabetical/group order, non-joint groups, locked-only filtering, lock/unlock all, lock/unlock selected joints, lock/unlock other influences, and invert locks.

## Display

Weight opacity, contours, wireframe, overlays, zero-weight display, and X-ray joints. Native brush cursor color, surface following, and falloff overlay controls. Blender's custom weight-color ramp is available here; it is shared across Blender and only changes when you edit it.

## Validation

Verified in Blender 5.2.3 LTS against the installed native paint panels and weight operators. Advanced brush controls reuse Blender's own conditional panel drawing, avoiding a separate imitation of its settings. No theme is installed or automatically changed.

`tests/integration/blender_weight_workspace.py` exercises brush families, gradients/sampling, Flood arithmetic and masks, lock preservation, normalization, transfer, automatic/envelope weighting, filtering, and re-entry. `tests/integration/blender_weight_workspace_ui.py` renders every page and the expanded native controls in an isolated Tool Settings dock. The existing joint and paint-tool exit integration tests also pass.

Reference: [Blender's weight-paint tools](https://docs.blender.org/manual/en/4.3/sculpt_paint/weight_paint/tools.html). The running Blender installation supplies the version-specific settings and operator definitions.
