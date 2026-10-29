"""Restart a real GUI Blender with saved Maya preferences, without --factory-startup."""
import json
import os
from pathlib import Path
import subprocess
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, run, setup, step


@step
def s_save_maya_preferences():
    setup()
    from importlib import import_module
    import_module(MODULE+'.first_start').make(bpy.context, open_layout=False)
    assert '/tmp/' in Path(bpy.utils.user_resource('CONFIG')).as_posix()
    bpy.ops.wm.save_userpref()


@step
def s_restart():
    folder = Path(bpy.utils.user_resource('CONFIG')).parent
    result = folder/'saved_maya_restart.json'
    script = folder/'saved_maya_restart.py'
    script.write_text('''import addon_utils, bpy, json, os
from importlib import import_module
from pathlib import Path
def inspect():
    module = os.environ['ALLSET_MODULE']
    sw = import_module(module+'.switch')
    prefs = bpy.context.preferences.addons[module].preferences
    window = bpy.context.window_manager.windows[0]
    data = dict(enabled=addon_utils.check(module)[1], maya_mode=prefs.maya_mode,
                registered=sw._registered[0] and hasattr(bpy.types, 'ALLSET_OT_make_live'),
                layout=sw.is_maya_workspace(window.workspace))
    Path(os.environ['ALLSET_STARTUP_RESULT']).write_text(json.dumps(data))
    shots = os.environ.get('ALLSET_GUI_SHOTS')
    if shots:
        with bpy.context.temp_override(window=window):
            bpy.ops.screen.screenshot(filepath=os.path.join(shots, 'maya_saved_restart.png'))
    bpy.ops.wm.quit_blender()
bpy.app.timers.register(inspect, first_interval=3.0, persistent=True)
''', encoding='utf-8')
    env = dict(os.environ, ALLSET_STARTUP_RESULT=str(result))
    child = subprocess.run([bpy.app.binary_path, '--enable-event-simulate',
                            '--window-geometry', '0', '0', '1600', '900',
                            '--python', str(script)], env=env, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
    log = child.stdout+child.stderr
    (folder/'logs'/'saved_maya_restart.log').write_text(log, encoding='utf-8')
    check('saved Maya mode restarts without an addon registration exception',
          child.returncode == 0 and 'Exception in module register' not in log and result.exists())
    data = json.loads(result.read_text()) if result.exists() else {}
    for key, description in (('enabled', 'addon stays enabled after restarting'),
                             ('maya_mode', 'saved Maya preference is retained'),
                             ('registered', 'Maya operators register during startup'),
                             ('layout', 'Blender opens directly in the Maya layout')):
        check(description, data.get(key, False))


run()
