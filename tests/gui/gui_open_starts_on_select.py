"""Opening a file starts the 3D View on the Select tool, like Maya after File > Open: a file saved with the Move tool
(in the Maya layout or in another workspace) comes back on Select; a tool picked after opening stays."""
import bpy,os,sys
from importlib import import_module
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE,setup,step,run,view3d,win,check
import sim
C={}
def override():
 a,r=view3d();return bpy.context.temp_override(window=win(),area=a,region=r)
def tool():return win().workspace.tools.from_space_view3d_mode('OBJECT').idname
def maya_ws():return import_module(MODULE+'.switch').is_maya_workspace(win().workspace)
def wait_layout():
 if not maya_ws() and C.setdefault('w',0)<50:
  C['w']+=1;sim._steps.insert(0,wait_layout)
def settle(n):
 # the load timer runs for about a second (0.1 s ticks); give it time to finish
 for _ in range(n):sim._steps.insert(0,lambda:None)
@step
def prepare():
 setup()
 C['save']=os.path.join(os.path.dirname(os.path.abspath(sys.argv[-1])),'open-starts-on-select.blend')
 C['other_ws']=win().workspace.name
 with override():bpy.ops.wm.tool_set_by_id(name='builtin.move')
 check('Move picked before saving',tool()=='builtin.move')
 bpy.ops.wm.save_as_mainfile(filepath=C['save'])
@step
def reopen_other():bpy.ops.wm.open_mainfile(filepath=C['save'],use_scripts=False)
@step
def layout1():wait_layout()
@step
def wait1():settle(15)
@step
def opened_from_other_workspace():
 check('a file saved in another workspace opens in the Maya layout on Select',maya_ws() and tool()=='builtin.select_box')
 with override():bpy.ops.wm.tool_set_by_id(name='builtin.move')
 check('Move picked in the Maya layout',tool()=='builtin.move')
 bpy.ops.wm.save_as_mainfile(filepath=C['save'])
@step
def reopen_maya():bpy.ops.wm.open_mainfile(filepath=C['save'],use_scripts=False)
@step
def layout2():wait_layout()
@step
def wait2():settle(15)
@step
def opened_from_maya_layout():
 check('a file saved in the Maya layout with Move opens on Select',maya_ws() and tool()=='builtin.select_box')
 with override():bpy.ops.wm.tool_set_by_id(name='builtin.rotate')
@step
def wait3():settle(15)
@step
def picked_tool_stays():
 check('a tool picked after opening stays',tool()=='builtin.rotate')
run()
