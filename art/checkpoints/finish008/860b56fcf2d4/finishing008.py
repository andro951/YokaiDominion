"""Final contour and usability pass; no change to unsupported chest form."""
import bpy
import numpy as np
from mathutils import Vector

def coords(o):
 a=np.empty(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',a);return a.reshape(-1,3)
def put(o,a):
 assert np.isfinite(a).all();o.data.vertices.foreach_set('co',a.ravel());o.data.update()
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def face(p):
 x,y,z=p.T;front=1-smooth(-.11,-.035,y);region=smooth(1.651,1.690,z)*(1-smooth(1.782,1.815,z))*front
 q=p.copy();q[:,2]+=.115*np.maximum(0,1.80-z)*region
 q[:,0]-=x*.045*np.exp(-((z-1.725)/.042)**2)*smooth(.025,.060,abs(x))*front
 return q

def lower_garment(p):
 x,y,z=p.T;t=np.clip((1.197-z)/.785,0,1);u=np.clip(x/(.151-.048*t**1.4+.011*np.sin(np.pi*t)),-1,1);q=p.copy()
 q[:,2]-=.025*t**5*(1-u*u)+.009*u*t**5
 q[:,0]+=.004*np.sin(np.pi*t)*np.sin(2*t)
 q[:,1]+=.0035*np.exp(-((t-.16)/.14)**2)*np.sin(5.5*np.pi*u+2.8*t)+.0025*t*np.sin(2.8*np.pi*u+2*t)
 return q

def organize():
 scene=bpy.context.scene
 categories=['01_BODY','02_FACE','03_HAIR','04_GARMENT','05_HORNS_AND_TAIL','90_STUDIO','99_ARCHIVED_PARTS']
 cols={}
 for name in categories:
  c=bpy.data.collections.get(name) or bpy.data.collections.new(name)
  if c.name not in scene.collection.children:scene.collection.children.link(c)
  cols[name]=c
 for o in list(scene.objects):
  name=o.name
  if o.type in {'CAMERA','LIGHT'} or name.startswith('STUDIO'):key='90_STUDIO'
  elif o.hide_render:key='99_ARCHIVED_PARTS'
  elif name=='Body':key='01_BODY'
  elif name.startswith(('Eye','Iris','Brow','Upper liner','Outer eyelash','Canine')):key='02_FACE'
  elif any('Hair' in m.name for m in o.data.materials if m) if o.type=='MESH' else False:key='03_HAIR'
  elif name.startswith(('Horn','Tail')):key='05_HORNS_AND_TAIL'
  else:key='04_GARMENT'
  for c in list(o.users_collection):c.objects.unlink(o)
  cols[key].objects.link(o)
 c=scene.camera;c.location=(3,-6,2.1);c.rotation_euler=(Vector((0,0,1.06))-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=2.35
 scene.render.resolution_x=1000;scene.render.resolution_y=1300;scene.render.resolution_percentage=100
 scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1.0
 bpy.ops.object.select_all(action='DESELECT');body=bpy.data.objects['Body'];body.select_set(True);bpy.context.view_layer.objects.active=body
 for screen in bpy.data.screens:
  for area in screen.areas:
   if area.type=='VIEW_3D':
    area.spaces.active.clip_end=100;area.spaces.active.region_3d.view_distance=3.1;area.spaces.active.region_3d.view_location=(0,0,1.07)
    area.spaces.active.shading.color_type='MATERIAL'


def apply(body):
 put(body,face(coords(body)))
 for o in bpy.data.objects:
  if o.type!='MESH' or o==body:continue
  if o.name.startswith(('Canine','Brow','Upper liner','Outer eyelash')):put(o,face(coords(o)))
  if o.name.startswith(('Gathered front skirt','Gathered rear skirt','Gathered skirt edge','Gathered skirt hem','Art008 tailored tail')):put(o,lower_garment(coords(o)))
 for mat in bpy.data.materials:
  if mat.name.startswith('Nails') and mat.use_nodes:
   bs=mat.node_tree.nodes.get('Principled BSDF')
   if bs:bs.inputs['Roughness'].default_value=.35;bs.inputs['Coat Weight'].default_value=.16
 organize();body['finishing008']='Lower-face contour, asymmetrical cloth hem and organized editable source'
