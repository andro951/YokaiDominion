"""Art finishing: coherent face, relaxed neck fabric, separated markings and hair tips."""
import math
import bpy
import numpy as np
from mathutils.bvhtree import BVHTree
from geometry import tube
import finish_details

SCALE=1.95/1.641334056854248

def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)

def facial_delta(p):
 x,y,z=p.T;ax=np.abs(x);sg=np.sign(x);front=1-smooth(-.075,-.04,y);d=np.zeros_like(p)
 jaw=np.exp(-((z-1.452)/.026)**2-((ax-.046)/.029)**2)*front
 cheek=np.exp(-((z-1.506)/.020)**2-((ax-.048)/.026)**2)*front
 d[:,0]-=sg*.0024*jaw;d[:,0]+=sg*.0013*cheek;d[:,1]-=.0016*cheek
 nose=np.exp(-((z-1.492)/.014)**2-((ax-.015)/.015)**2)*(1-smooth(-.108,-.083,y))
 d[:,0]-=sg*.0012*nose;d[:,1]+=.0007*nose
 corners=np.exp(-((ax-.022)/.009)**2-((z-1.467)/.007)**2)*front
 d[:,2]+=(.00045+.001*(x>0))*corners
 return d*SCALE

def polish(body,eyes,mat):
 n=len(body.data.vertices);p=np.empty(n*3);q=np.empty(n*3);body.data.attributes['source_position'].data.foreach_get('vector',p);body.data.vertices.foreach_get('co',q);p=p.reshape(-1,3);q=q.reshape(-1,3)
 q+=facial_delta(p)
 # Blend the upper glute into the sacrum rather than retaining an isolated mound.
 x,y,z=p.T;glute=np.exp(-((z-.855)/.072)**2)*smooth(.015,.085,y)*(1-smooth(.12,.19,np.abs(x)))
 q[:,1]-=.0045*glute
 body.data.vertices.foreach_set('co',q.ravel());body.data.update()
 for o in bpy.data.objects:
  if o.type=='MESH' and o.name.startswith(('Canine.','Brow.','Brow hair','Upper liner','Outer eyelash')):
   a=np.array([v.co[:] for v in o.data.vertices]);a+=facial_delta(a/SCALE);o.data.vertices.foreach_set('co',a.ravel());o.data.update()
 # Retain loose fabric around the sides/nape, not a shrinkwrapped standing collar.
 bvh=BVHTree.FromPolygons([v.co for v in body.data.vertices],[f.vertices[:] for f in body.data.polygons])
 for o in bpy.data.objects:
  if o.type=='MESH' and o.name.startswith('Gathered soft neck passage'):
   a=np.array([v.co[:] for v in o.data.vertices]);rows=a.reshape(60,31,3)
   for i,row in enumerate(rows):
    t=i/59;w=float(smooth(0,.22,t));c=row.mean(0);rad=np.array([c[0],c[1]-.012,0.]);rad/=max(np.linalg.norm(rad),1e-8)
    row+=w*(.0045*rad+np.array([0.,0.,-.0025*math.sin(math.pi*t)]))
   o.data.vertices.foreach_set('co',a.ravel());o.data.update()
  if o.type=='MESH' and o.name.startswith('Face wave'):
   a=np.array([v.co[:] for v in o.data.vertices]);rings=76;sides=16
   if len(a)==rings*sides+2:
    for i,t in enumerate(np.linspace(0,1,rings)):
     w=float(smooth(.62,1,t));side=np.sign(a[i*sides:(i+1)*sides,0].mean())
     a[i*sides:(i+1)*sides,2]-=.012*w;a[i*sides:(i+1)*sides,0]+=side*.006*w
    a[-1,2]-=.012;a[-1,0]+=np.sign(a[-1,0])*.006
    o.data.vertices.foreach_set('co',a.ravel());o.data.update()
 # Make the markings read as separate tapered strokes rather than linked spots.
 material=mat['skin']
 for node in material.node_tree.nodes:
  if node.type=='MATH' and node.operation=='DIVIDE' and not node.inputs[1].is_linked:
   value=node.inputs[1].default_value
   for old,new in [(.021,.016),(.026,.019),(.030,.023),(.029,.022)]:
    if abs(value-old)<1e-6:node.inputs[1].default_value=new;break
 # State what this file actually is; rig/solver assets are a separate refit.
 body['asset_kind']='Completed visual-art revision; not runtime-rig acceptance'
 body['supported_pose']='Neutral A-pose; neck fabric and body surface are independently editable'
 for o in bpy.data.objects:
  if o.type=='MESH' and not o.name.startswith('STUDIO'):
   for f in o.data.polygons:f.use_smooth=True

def install():
 previous=finish_details.build
 def build(body,eyes,mat,bvh,front):
  previous(body,eyes,mat,bvh,front);polish(body,eyes,mat)
 finish_details.build=build
