"""Localized surface art for Art008. No cloth-driven body shaping."""
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
 assert np.isfinite(a).all();o.data.vertices.foreach_set('co',a.ravel());o.data.update()
def g(x,c,w):return np.exp(-((x-c)/w)**2)

def anatomy(body):
 q=read(body);p=np.empty(q.size);body.data.attributes['source_position'].data.foreach_get('vector',p);p=p.reshape(-1,3)
 x,y,z=p.T;ax=abs(x);sg=np.sign(x);front=1-smooth(-.055,-.005,y);rear=smooth(.005,.045,y)
 # Sloped outer shoulders and supported muscular neck, without widening the skeleton.
 q[:,2]-=.005*g(ax,.179,.049)*g(z,1.329,.047)
 q[:,2]+=.004*g(ax,.080,.038)*g(z,1.352,.043)*rear
 # Clavicle contour is a shallow ridge with broad transitions, not a bar.
 clav=g(z,1.321-.16*(ax-.05),.012)*g(ax,.087,.065)*front
 q[:,1]-=.0018*clav
 # Long muscle bellies and subtle separation, using anatomical source-space masks.
 for s in (-1,1):
  q[:,1]-=.0045*g(x,s*.216,.037)*g(z,1.185,.072)*front
  q[:,1]+=.0045*g(x,s*.210,.040)*g(z,1.191,.082)*rear
  q[:,1]-=.0028*g(x,s*(.300-.45*(z-.985)),.022)*g(z,1.006,.075)*front
  q[:,1]-=.0040*g(x,s*.111,.043)*g(z,.655,.124)*front
  q[:,1]-=.0025*g(x,s*.071,.026)*g(z,.510,.044)*front
  # Firm posterior thigh and upper-back planes, not extra isolated glute spheres.
  q[:,1]+=.003*g(x,s*.105,.045)*g(z,.660,.125)*rear
  q[:,1]+=.0035*g(x,s*.095,.055)*g(z,1.249,.081)*rear
 # Abdominal separations are soft recesses between existing broad sculpted forms.
 gate=front*(1-smooth(.082,.118,ax))
 q[:,1]+=.0018*g(x,0,.0065)*g(z,1.060,.105)*gate
 for zz in (1.070,1.018):q[:,1]+=.0013*g(z,zz,.006)*g(ax,.044,.038)*gate
 put(body,q)


def cloth(body):
 bvh=BVHTree.FromPolygons([v.co for v in body.data.vertices],[f.vertices[:] for f in body.data.polygons])
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  if o.name.startswith('Gathered halter ') and 'hem' not in o.name:
   a=read(o)
   if len(a)==112*31:
    rows=a.reshape(112,31,3)
    for i,row in enumerate(rows):
     t=i/111;weight=math.sin(math.pi*t)**2;cx=row[:,0].mean();side=np.sign(cx)
     row[:,0]=cx+(row[:,0]-cx)*(1-.10*weight)+side*.002*weight
     # Collision-fit cloth to the edited body without changing any body vertex.
     for v in row:
      h,n,_,_=bvh.ray_cast(Vector((v[0],-2,v[2])),Vector((0,1,0)),4)
      if h:v[1]=min(v[1],h.y-.0045)
    put(o,a)
    o['body_independent_drape']=True
  if o.name.startswith('Gathered halter hem '):
   # Existing separate border would no longer match narrowed panels: hide, not delete.
   o.hide_render=True;o.hide_viewport=True
  if o.name.startswith('Gathered ') and o.type=='MESH':
   for mod in o.modifiers:
    if mod.type=='SOLIDIFY':mod.thickness=.0010


def hair():
 for o in bpy.data.objects:
  if o.type!='MESH' or not o.name.startswith(('Back wave','Side S wave','Face wave','Crown sweep')):continue
  a=read(o)
  if len(a)!=1218:continue
  rows=a[:1216].reshape(76,16,3)
  phase=(sum(ord(c) for c in o.name)%71)*.17
  for i,row in enumerate(rows):
   t=i/75;center=row.mean(0);w=math.sin(math.pi*t)**2
   # Uneven sub-lock ridges break the identical broad ribbon surfaces.
   for j,v in enumerate(row):
    r=v-center;length=np.linalg.norm(r)
    if length>1e-9:v+=r/length*(.00045*w*(math.sin(6*math.pi*j/16+phase+.7*t)+.4*math.sin(10*math.pi*j/16-.8*t)))
  put(o,a)
  if not o.modifiers.get('Art008 hair silhouette'):
   m=o.modifiers.new('Art008 hair silhouette','SUBSURF');m.levels=m.render_levels=1


def materials():
 for m in bpy.data.materials:
  if not m.use_nodes:continue
  n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF')
  if not bs:continue
  if m.name.startswith('Skin |'):
   # Fine pores are shading detail; anatomical planes remain real geometry.
   tex=n.new('ShaderNodeTexNoise');tex.name='Art008 skin microstructure';tex.inputs['Scale'].default_value=780;tex.inputs['Detail'].default_value=2;tex.inputs['Roughness'].default_value=.62
   bump=n.new('ShaderNodeBump');bump.name='Art008 subtle pores';bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.00012
   if bs.inputs['Normal'].is_linked:l.new(bs.inputs['Normal'].links[0].from_socket,bump.inputs['Normal'])
   l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal'])
  if m.name.startswith('Cloth'):
   tex=n.new('ShaderNodeTexNoise');tex.name='Art008 woven fibre';tex.inputs['Scale'].default_value=900;tex.inputs['Detail'].default_value=2
   bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.13;bump.inputs['Distance'].default_value=.00010
   if bs.inputs['Normal'].is_linked:l.new(bs.inputs['Normal'].links[0].from_socket,bump.inputs['Normal'])
   l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal']);bs.inputs['Sheen Weight'].default_value=.28

def apply(body):
 anatomy(body);cloth(body);hair();materials()
 body['surface008']='Localized muscle planes, independent loose cloth, hair surface and material refinement'
