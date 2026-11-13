import sys
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, addon_utils
addon_utils.enable("io_scene_fbx")
import fbxfix
from mathutils import Vector
def render(path, views, res=600, objs=None):
    sc=bpy.context.scene
    sc.render.engine='CYCLES'; sc.cycles.samples=8; sc.cycles.device='CPU'
    sc.render.resolution_x=res; sc.render.resolution_y=res
    if not sc.world: sc.world=bpy.data.worlds.new('W')
    sc.world.use_nodes=True; sc.world.node_tree.nodes['Background'].inputs[1].default_value=1.0
    sc.world.node_tree.nodes['Background'].inputs[0].default_value=(0.8,0.8,0.8,1)
    cam=bpy.data.objects.get('CAM')
    if not cam:
        cam=bpy.data.objects.new('CAM',bpy.data.cameras.new('CAM')); sc.collection.objects.link(cam)
    cam.data.type='ORTHO'; sc.camera=cam
    for i,(loc,rot,scale) in enumerate(views):
        cam.location=loc; cam.rotation_euler=rot; cam.data.ortho_scale=scale
        sc.render.filepath=path%i; bpy.ops.render.render(write_still=True)
