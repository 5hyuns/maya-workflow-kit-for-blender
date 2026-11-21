"""#433: the light tabs of the Attribute Editor have a Cycles section with the light settings that have no Maya
attribute row (Exposure, Normalize, Spread, Soft Falloff, Max Bounces, ...), and every row reaches a real property."""

from importlib import import_module

import bpy

import kit

ae_layout = import_module(kit.MODULE + ".ui.ae_layout")
ae_rows = import_module(kit.MODULE + ".ui.ae_rows")

WANT = {
    "POINT": {"exposure", "normalize", "use_soft_falloff", "cycles.max_bounces",
              "cycles.use_multiple_importance_sampling", "cycles.is_caustics_light"},
    "SUN": {"exposure", "normalize", "cycles.max_bounces", "cycles.use_multiple_importance_sampling",
            "cycles.is_caustics_light"},
    "SPOT": {"exposure", "normalize", "use_soft_falloff", "cycles.max_bounces",
             "cycles.use_multiple_importance_sampling", "cycles.is_caustics_light"},
    "AREA": {"exposure", "normalize", "spread", "cycles.is_portal", "cycles.max_bounces",
             "cycles.use_multiple_importance_sampling", "cycles.is_caustics_light"},
}


def _section(kind, name):
    sections, _t = ae_layout.BY_KIND[kind]
    return next((sec for _d, sec in ae_layout.walk(sections) if sec.name == name), None)


def test_cycles_section_rows():
    for kind, want in WANT.items():
        sec = _section(kind, "Cycles")
        assert sec is not None, kind
        assert not sec.open, kind                       # closed until opened, like the other extra sections
        paths = {row[2] for row in sec.rows if row[0] == "prop"}
        assert paths == want, (kind, sorted(paths ^ want))


def test_rows_reach_the_light_settings():
    for kind in WANT:
        light = bpy.data.lights.new(f"{kind.lower()}LightShape1", kind)
        for row in _section(kind, "Cycles").rows:
            owner, attr = ae_rows.resolve(light, row[2])
            assert owner is not None and hasattr(owner, attr), (kind, row)
        # an edit through the row's path lands on the light
        owner, attr = ae_rows.resolve(light, "normalize")
        setattr(owner, attr, False)
        assert light.normalize is False, kind
        owner, attr = ae_rows.resolve(light, "cycles.max_bounces")
        setattr(owner, attr, 7)
        assert light.cycles.max_bounces == 7, kind


def test_without_cycles_settings_the_row_is_left_out():
    class Bare:                                         # a light without the Cycles add-on's settings
        exposure = 0.0
    owner, attr = ae_rows.resolve(Bare(), "cycles.max_bounces")
    assert owner is None
