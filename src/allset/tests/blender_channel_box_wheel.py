"""Real wheel events over Channel Box labels/fields in an isolated factory GUI.
Blender --factory-startup --enable-event-simulate --python this_file.py
"""
import importlib
from pathlib import Path
import traceback
import bpy

bpy.context.preferences.view.show_splash=False
bpy.ops.preferences.addon_enable(module='bl_ext.user_default.allset')
addon=importlib.import_module('bl_ext.user_default.allset')
prefs=bpy.context.preferences.addons[addon.__name__].preferences
prefs.welcome_done=True
addon.switch.set_mode(True,layout=False)
cb=addon.ui.channel_box
dock=addon.ui.maya_dock
bpy.ops.mesh.primitive_uv_sphere_add()
mesh=bpy.context.object
for i in range(50): mesh[f'extra_{i:02d}']=float(i)
cb.rebuild_rows(bpy.context)
area=next(a for a in bpy.context.screen.areas if a.type=='PROPERTIES')
region=next(r for r in area.regions if r.type=='WINDOW')
view=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
vr=next(r for r in view.regions if r.type=='WINDOW')
phase=0
baseline=None
position=None
layer=None
model_state=(tuple(mesh.location),tuple(mesh.rotation_euler),tuple(mesh.scale),dict(mesh.items()))

def emit(kind,x,y,count=1):
    window=bpy.context.window
    window.event_simulate(type='MOUSEMOVE',value='NOTHING',x=int(x),y=int(y))
    for i in range(count):
        window.event_simulate(type=kind,value='PRESS',x=int(x),y=int(y))


def run():
    global phase,baseline,position,layer
    try:
        ptr=area.as_pointer()
        if phase==0:
            assert dock.set_role(area,'CHANNEL_BOX',bpy.context.window)
            area.spaces.active.context='TOOL'
            area.tag_redraw()
        elif phase==1:
            assert cb._last.get(ptr,(0,0,None))[2] is not None,cb._last
            assert cb._wheel_windows.get(bpy.context.window.as_pointer())==cb._wheel_generation
            baseline=region.view2d.region_to_view(0,0)
            # Translate/rotate value fields, not blank background.
            emit('WHEELDOWNMOUSE',region.x+region.width*.72,region.y+region.height-150,5)
        elif phase==2:
            assert cb._scroll.get(ptr,0)==5,cb._scroll
            assert region.view2d.region_to_view(0,0)==baseline,'The whole dock moved'
            emit('WHEELUPMOUSE',region.x+region.width*.3,region.y+region.height-160,2)
        elif phase==3:
            assert cb._scroll.get(ptr,0)==3,cb._scroll
            emit('WHEELDOWNMOUSE',region.x+region.width*.72,region.y+region.height-150,100)
        elif phase==4:
            first,total,limit=cb._last[ptr]
            assert cb._scroll[ptr]==total-limit,(cb._scroll,cb._last)
            assert region.view2d.region_to_view(0,0)==baseline,'Channel wheel moved the whole dock'
            position=cb._scroll[ptr]
            emit('WHEELDOWNMOUSE',region.x+region.width*.5,region.y+40,3)
        elif phase==5:
            assert cb._scroll[ptr]==position,'Wheel over Layer Editor changed Channel Box'
            baseline=region.view2d.region_to_view(0,0)
            emit('WHEELUPMOUSE',vr.x+vr.width*.5,vr.y+vr.height*.5,2)
        elif phase==6:
            assert cb._scroll[ptr]==position,'Wheel over viewport changed Channel Box'
            x=region.x+region.width*.72
            y=region.y+region.height-150
            with bpy.context.temp_override(area=area,region=region):
                distance=cb.row_pitch(bpy.context)*1.25
            bpy.context.window.event_simulate(type='MOUSEMOVE',value='NOTHING',x=int(x),y=int(y))
            bpy.context.window.event_simulate(type='TRACKPADPAN',value='NOTHING',x=int(x),y=int(y+distance))
        elif phase==7:
            assert cb._scroll[ptr]==position-1,('Trackpad pan',cb._scroll[ptr],position)
            emit('WHEELUPMOUSE',region.x+region.width*.72,region.y+region.height-150,100)
        elif phase==8:
            assert cb._scroll[ptr]==0,cb._scroll
            assert model_state==(tuple(mesh.location),tuple(mesh.rotation_euler),tuple(mesh.scale),dict(mesh.items())), 'Wheel edited channel values'
            assert region.view2d.region_to_view(0,0)==baseline,'Layer split/dock moved'
            addon.switch.set_mode(False,layout=False)
            assert not bpy.app.timers.is_registered(cb._ensure_wheel_watch)
            assert not cb._wheel_windows
            emit('WHEELUPMOUSE',vr.x+vr.width*.5,vr.y+vr.height*.5)
        else:
            Path('/tmp/allset-channel-wheel-result.txt').write_text('PASS: wheel over fields and labels, one-row steps, limits, fixed Layer Editor, viewport pass-through, unchanged values, cleanup')
            bpy.ops.wm.quit_blender()
            return None
        phase+=1
        return .5
    except Exception:
        Path('/tmp/allset-channel-wheel-result.txt').write_text(traceback.format_exc())
        bpy.ops.wm.quit_blender()
        return None
bpy.app.timers.register(run,first_interval=1)
