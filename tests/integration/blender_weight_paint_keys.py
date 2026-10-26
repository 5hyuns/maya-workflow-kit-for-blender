"""Run Blender --factory-startup --enable-event-simulate --python this_file.py.
Uses actual key events in an isolated factory window, then exits that process.
"""
import runpy
import traceback
from pathlib import Path
import os

OUTPUT = Path(os.environ.get("ALLSET_INTEGRATION_OUTPUT",
                             str(Path(__file__).resolve().parents[2] / "tmp" / "integration_artifacts")))
OUTPUT.mkdir(parents=True, exist_ok=True)

import bpy
from bl_keymap_utils.io import keymap_init_from_data

ns = runpy.run_path(str(Path(__file__).with_name('blender_weight_paint_exit.py')))
bpy.context.preferences.view.show_splash = False
km = next(k for k in ns['data'] if k[0] == 'Weight Paint')
keymap_init_from_data(bpy.context.window_manager.keyconfigs.addon.keymaps.new(
    name='Weight Paint', space_type='EMPTY', region_type='WINDOW'), km[2]['items'])
area, region = ns['area'], ns['region']
steps = [('Q', 'builtin.select_box'), ('W', 'builtin.move'),
         ('E', 'builtin.rotate'), ('R', 'builtin.scale')]
phase = 0

def tick():
    global phase
    try:
        if phase >= len(steps) * 3:
            (OUTPUT / 'allset-paint-key-result.txt').write_text('PASS: real Q/W/E/R key events exit Weight Paint, activate Object tools, preserve all vertex weights')
            bpy.ops.wm.quit_blender()
            return None
        key, tool = steps[phase // 3]
        with bpy.context.temp_override(area=area, region=region):
            if phase % 3 == 0:
                ns['enter']()
            elif phase % 3 == 1:
                win = bpy.context.window
                xy = dict(x=region.x + region.width // 2, y=region.y + region.height // 2)
                win.event_simulate(type='MOUSEMOVE', value='NOTHING', **xy)
                win.event_simulate(type=key, value='PRESS', **xy)
                win.event_simulate(type=key, value='RELEASE', **xy)
            else:
                ns['check'](tool)
                print('PASS: key', key)
        phase += 1
        return 0.4
    except Exception:
        (OUTPUT / 'allset-paint-key-result.txt').write_text(traceback.format_exc())
        bpy.ops.wm.quit_blender()
        return None

bpy.app.timers.register(tick, first_interval=1)
