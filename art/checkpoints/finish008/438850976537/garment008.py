"""Continuous garment construction on the fixed body; body vertices are never edited."""
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def read(o):
 p=np.empty(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',p);return p.reshape(-1,3)
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)

def halter(body):
 panelL=bpy.data.objects['Gathered halter -1.0'];panelR=bpy.data.objects['Gathered halter 1.0']
 neckL=bpy.data.objects['Gathered soft neck passage -1.0'];neckR=bpy.data.objects['Gathered soft neck passage 1.0']
 L=read(panelL).reshape(112,31,3);R=read(panelR).reshape(112,31,3);NL=read(neckL).reshape(60,31,3);NR=read(neckR).reshape(60,31,3)
 def orient(a,b):
  return b[:,::-1].copy() if np.linalg.norm(a[-1]-b[0,::-1])<np.linalg.norm(a[-1]-b[0]) else b.copy()
 def join(a,b):
  b=orient(a,b);seam=(a[-1]+b[0])*.5
  return np.concatenate([a[:-1],seam[None],b[1:]])
 a=join(L[::-1],NL);a=join(a,NR[::-1]);a=join(a,R)
 n,m,_=a.shape
 # Smooth joins over a short span, retaining the flowing panel silhouette.
 for seam in (111,170,229):
  for _ in range(14):
   old=a.copy()
   for i in range(max(1,seam-7),min(n-1,seam+8)):
    w=.22*np.exp(-((i-seam)/4.5)**2)
    a[i]=(1-w)*old[i]+.5*w*(old[i-1]+old[i+1])
 bvh=BVHTree.FromPolygons([v.co for v in body.data.vertices],[f.vertices[:] for f in body.data.polygons])
 # Fix only actual near-body intersections; do not shrinkwrap away loose folds.
 for row in a:
  for p in row:
   hit,normal,_,distance=bvh.find_nearest(Vector(p))
   if hit and distance<.015:
    signed=float((Vector(p)-hit).dot(normal))
    if signed<.003:p[:]=np.array(hit)+np.array(normal)*.003
 vertices=a.reshape(-1,3);faces=[]
 for i in range(n-1):
  for j in range(m-1):
   k=i*m+j;faces.append((k,k+1,k+1+m,k+m))
 mesh=bpy.data.meshes.new('ContinuousHalterSurface');mesh.from_pydata(vertices,[],faces);mesh.update()
 obj=bpy.data.objects.new('Continuous loose neck-to-waist halter',mesh)
 bpy.data.collections['04_GARMENT'].objects.link(obj);mesh.materials.append(panelL.data.materials[0])
 uv=mesh.uv_layers.new(name='GarmentUV')
 for f in mesh.polygons:
  f.use_smooth=True
  for li in f.loop_indices:
   v=mesh.loops[li].vertex_index;uv.data[li].uv=((v%m)/(m-1),(v//m)/(n-1))
 sub=obj.modifiers.new('Soft continuous fabric','SUBSURF');sub.levels=sub.render_levels=1
 solid=obj.modifiers.new('Actual fabric thickness','SOLIDIFY');solid.thickness=.0010;solid.offset=0
 obj['construction']='Single continuous loose halter from left waist over neck to right waist. No cups, underband, body modification or simulated breast lift.'
 obj['rows']=n;obj['columns']=m
 for o in (panelL,panelR,neckL,neckR):
  o.hide_render=True;o.hide_viewport=True;o['replaced_by']=obj.name
  for c in list(o.users_collection):c.objects.unlink(o)
  bpy.data.collections['99_ARCHIVED_PARTS'].objects.link(o)
 # Reject missing joins rather than silently saving disconnected patches.
 edges=np.linalg.norm(np.diff(a,axis=0),axis=2)
 if edges.max()>.08:raise RuntimeError('Unexpected halter join discontinuity')


def crown():
 for o in bpy.data.objects:
  if o.type!='MESH' or not o.name.startswith('Crown sweep'):continue
  p=read(o)
  if len(p)!=1218:continue
  rings=p[:1216].reshape(76,16,3)
  for i,row in enumerate(rings):
   center=row.mean(0);t=i/75
   row[:,2]=center[2]+(row[:,2]-center[2])*(.72+.28*abs(2*t-1))
  o.data.vertices.foreach_set('co',p.ravel());o.data.update()


def apply(body):
 halter(body);crown();body['garment008']='Continuous loose halter; original body untouched by garment construction'
