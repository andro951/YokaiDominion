"""Facial finishing on coherent anatomy: restrained soft planes and actual eyebrow hairs."""
import math
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def read(o):
 a=np.empty(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',a);return a.reshape(-1,3)
def put(o,a):
 if not np.isfinite(a).all():raise RuntimeError('Non-finite face geometry')
 o.data.vertices.foreach_set('co',a.ravel());o.data.update()
def linear(c):
 c=np.asarray(c);return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)

def face_planes(body):
 p=read(body);x,y,z=p.T;ax=abs(x);front=1-smooth(-.10,-.045,y);q=p.copy()
 cheek=np.exp(-((ax-.046)/.029)**2-((z-1.780)/.030)**2)*front;q[:,1]-=.0026*cheek
 chin=np.exp(-(x/.036)**2-((z-1.722)/.018)**2)*front;q[:,1]-=.0011*chin
 nose=np.exp(-((ax-.019)/.015)**2-((z-1.777)/.017)**2)*(1-smooth(-.168,-.138,y));q[:,0]-=np.sign(x)*.0012*nose
 lip=np.exp(-(x/.031)**4-((z-1.748)/.009)**2)*front;q[:,1]-=.0009*lip;put(body,q)

def eyebrow_hairs(body):
 bvh=BVHTree.FromPolygons([v.co for v in body.data.vertices],[f.vertices[:] for f in body.data.polygons if all(body.data.vertices[i].co.z>1.70 for i in f.vertices)])
 under=bpy.data.materials.new('Brow | soft ivory undercoat');under.use_nodes=True
 bs=under.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*linear((.68,.69,.72)),1);bs.inputs['Roughness'].default_value=.80
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  if o.name.startswith('Brow.'):
   # Preserve design readability at game-camera scale, but remove the raised strip.
   p=read(o)
   if len(p)==482:
    a=p[:480].reshape(48,10,3)
    for row in a:
     c=row.mean(0);row[:,2]=c[2]+.70*(row[:,2]-c[2])
     for v in row:
      hit,_,_,_=bvh.ray_cast(Vector((v[0],-1,v[2])),Vector((0,1,0)),2)
      if hit:v[1]=hit.y-.00015+.18*(v[1]-c[1])
    p[-2]=a[0].mean(0);p[-1]=a[-1].mean(0)
    put(o,p)
   o.hide_render=False;o.hide_viewport=False;o.data.materials.clear();o.data.materials.append(under)
  elif o.name.startswith('Brow hair'):o.hide_render=True;o.hide_viewport=True
 rng=np.random.default_rng(9009);verts=[];faces=[];colors=[]
 for side in (-1,1):
  for strand in range(180):
   t=np.clip((strand+rng.uniform(-.35,.35))/179,0,1)
   x=side*(.018+.043*t);z=1.850+.008*np.sin(t*math.pi*.58)+rng.uniform(-.0014,.0009)*(1-.65*t)
   length=rng.uniform(.0018,.0033)*(1-.45*t);radius=rng.uniform(.00009,.00015);center=[]
   for u in np.linspace(0,1,6):
    xx=x+side*length*.85*u;zz=z+length*(.70-.9*t)*u+.0004*math.sin(math.pi*u)
    hit,normal,_,_=bvh.ray_cast(Vector((xx,-1,zz)),Vector((0,1,0)),2)
    if hit is None:break
    center.append(np.array(hit)+np.array(normal)*(.00028+.00012*math.sin(math.pi*u)))
   if len(center)!=6:continue
   start=len(verts);shade=rng.uniform(.64,.88)
   for i,c in enumerate(center):
    direction=center[min(i+1,5)]-center[max(0,i-1)];direction/=np.linalg.norm(direction)
    a=np.cross(direction,[0,1,0]);a/=np.linalg.norm(a);b=np.cross(direction,a);r=radius*(1-.92*(i/5)**1.5)
    for k in range(4):
     angle=k*math.pi/2;verts.append(c+r*(a*math.cos(angle)+b*math.sin(angle)));colors.append((*linear((shade*.97,shade*.98,shade)),1))
    if i:
     for k in range(4):
      j=start+(i-1)*4+k;jn=start+(i-1)*4+(k+1)%4;faces.append((j,jn,jn+4,j+4))
 mesh=bpy.data.meshes.new('IndividualEyebrowHairs');mesh.from_pydata(verts,[],faces);mesh.update()
 obj=bpy.data.objects.new('Art009 individual eyebrow hairs',mesh);bpy.data.collections['02_FACE'].objects.link(obj)
 ca=mesh.color_attributes.new(name='BrowColour',type='FLOAT_COLOR',domain='POINT');ca.data.foreach_set('color',np.array(colors).ravel())
 mat=bpy.data.materials.new('Brow | individual ivory fibres');mat.use_nodes=True;node=mat.node_tree.nodes.new('ShaderNodeVertexColor');node.layer_name='BrowColour';bs=mat.node_tree.nodes.get('Principled BSDF');mat.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.55;mesh.materials.append(mat)
 for f in mesh.polygons:f.use_smooth=True

def fangs():
 for o in bpy.data.objects:
  if o.type!='MESH' or not o.name.startswith('Canine'):continue
  p=read(o);c=p.mean(0);top=p[:,2].max();p[:,0]=c[0]+(p[:,0]-c[0])*.68;p[:,1]=c[1]+(p[:,1]-c[1])*.78+.0004;p[:,2]=top+(p[:,2]-top)*.86+.00025;put(o,p)

def apply(body):
 face_planes(body);eyebrow_hairs(body);fangs();body['face009']='Continuous cheek/lip planes, restrained nose refinement, surface-fitted ivory brows with individual hairs'
