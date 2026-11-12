"""Portrait finishing for the anatomical art master; preserves editable source meshes."""
import math
import bpy
import numpy as np

def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def coords(o):
 a=np.empty(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',a);return a.reshape(-1,3)
def put(o,a):
 assert np.isfinite(a).all();o.data.vertices.foreach_set('co',a.ravel());o.data.update()
def linear(c):
 c=np.array(c);return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)

def face_transform(p):
 x,y,z=p.T;ax=abs(x);sg=np.sign(x);q=p.copy();front=1-smooth(-.09,-.025,y)
 # Preserve a strong adult jaw, soften the broad square lower-face silhouette.
 jaw=np.exp(-((z-1.728)/.038)**2)*smooth(.026,.065,ax)*front
 q[:,0]-=x*.065*jaw
 # A little more horizontal eye opening, not cartoonishly enlarged eyeballs.
 eye=np.exp(-((ax-.0415)/.030)**4-((z-1.824)/.021)**4)*front
 q[:,0]+=sg*(ax-.0415)*.075*eye
 q[:,2]+=.0007*smooth(.035,.065,ax)*eye
 return q

def facial_detail(body):
 put(body,face_transform(coords(body)))
 for o in bpy.data.objects:
  if o.type=='MESH' and o!=body and o.name.startswith(('Eye.','Iris.','Brow','Upper liner','Outer eyelash','Canine')):
   put(o,face_transform(coords(o)))
 for eye in [o for o in bpy.data.objects if o.name.startswith('Eye.') and o.type=='MESH']:
  iris=bpy.data.objects.get('Iris.'+eye.name)
  if iris is None:continue
  a=coords(eye);center=(a.min(0)+a.max(0))*.5;radius=np.median(np.ptp(a,axis=0))*.5
  p=coords(iris);gaze=p.mean(0)-center;gaze/=np.linalg.norm(gaze)
  radial=p-center;radial-=np.outer(radial@gaze,gaze);radial*=1.13
  h=np.sqrt(np.maximum(1e-10,radius*radius-np.sum(radial*radial,axis=1)))+.00020
  put(iris,center+radial+np.outer(h,gaze))
 ca=body.data.color_attributes.get('Complexion')
 src=body.data.attributes.get('source_position')
 if ca and src:
  p=np.empty(len(body.data.vertices)*3);src.data.foreach_get('vector',p);p=p.reshape(-1,3);x,y,z=p.T
  c=np.empty(len(p)*4);ca.data.foreach_get('color',c);c=c.reshape(-1,4)
  lip=np.exp(-((z-1.468)/.0075)**4-((x)/.026)**6)*(1-smooth(-.090,-.065,y))*.40
  c[:,:3]=c[:,:3]*(1-lip[:,None])+linear((.335,.285,.405))*lip[:,None]
  lid=np.exp(-((abs(x)-.033)/.025)**4-((z-1.542)/.012)**2)*(1-smooth(-.073,-.045,y))*.22
  c[:,:3]*=(1-lid[:,None]);ca.data.foreach_set('color',c.ravel())


def hair_finish():
 locks=[]
 for o in bpy.data.objects:
  if o.type!='MESH' or not o.name.startswith(('Back wave','Side S wave','Face wave','Crown sweep')):continue
  a=coords(o)
  if len(a)!=1218:continue
  if o.name.startswith('Crown sweep'):
   # Reduce the paired bow-like crest while preserving scalp coverage at the part.
   ax=abs(a[:,0]);w=np.exp(-((a[:,2]-1.965)/.022)**2-((ax-.059)/.047)**2)
   a[:,2]-=.009*w;put(o,a)
  uv=o.data.uv_layers.get('StrandUV') or o.data.uv_layers.new(name='StrandUV')
  o.data.uv_layers.active=uv
  for poly in o.data.polygons:
   ids=[o.data.loops[i].vertex_index for i in poly.loop_indices];us=[(j%16)/16 if j<1216 else .5 for j in ids];seam=max(us)-min(us)>.5
   for li,j,u in zip(poly.loop_indices,ids,us):
    if seam and u<.5:u+=1
    uv.data[li].uv=(u, min(1,(j//16)/75) if j<1216 else (0 if j==1216 else 1))
  locks.append(o)
 hair=bpy.data.materials.get('Hair | ivory silver')
 if hair and hair.use_nodes:
  m=hair.copy();m.name='Hair | Art008 strand-aligned ivory';n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF')
  uv=n.new('ShaderNodeUVMap');uv.uv_map='StrandUV'
  scale=n.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(100,1.6,1);l.new(uv.outputs['UV'],scale.inputs[0])
  tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=1;tex.inputs['Detail'].default_value=2;l.new(scale.outputs[0],tex.inputs['Vector'])
  ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.20;ramp.color_ramp.elements[0].color=(*linear((.55,.58,.64)),1);ramp.color_ramp.elements[1].position=.80;ramp.color_ramp.elements[1].color=(*linear((.89,.90,.92)),1)
  l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs['Color'],bs.inputs['Base Color'])
  bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.00017;l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal'])
  tan=n.new('ShaderNodeTangent');tan.direction_type='UV_MAP';tan.uv_map='StrandUV';l.new(tan.outputs[0],bs.inputs['Tangent'])
  bs.inputs['Roughness'].default_value=.43;bs.inputs['Anisotropic'].default_value=.48
  for o in locks:o.data.materials.clear();o.data.materials.append(m)


def apply(body):
 facial_detail(body);hair_finish()
 body['portrait008']='Refined lower face, larger iris presence, eyelid/lip complexion and strand-aligned hair UVs'
