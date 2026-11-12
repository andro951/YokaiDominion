"""Final portrait and marking contours. No body-proportion changes."""
import math
import bpy
import numpy as np

def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def read(o):
 p=np.empty(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',p);return p.reshape(-1,3)
def put(o,p):
 assert np.isfinite(p).all();o.data.vertices.foreach_set('co',p.ravel());o.data.update()
def face_shape(p):
 x,y,z=p.T;ax=abs(x);q=p.copy()
 jaw=np.exp(-((z-1.730)/.034)**2)*smooth(.024,.060,ax)*(1-smooth(.025,.080,y))
 q[:,0]-=.11*x*jaw
 chin=np.exp(-(x/.034)**2-((z-1.720)/.018)**2)*(1-smooth(-.100,-.045,y))
 q[:,1]+=.0011*chin
 lid=np.exp(-((ax-.0415)/.027)**4-((z-1.834)/.0078)**2)*(1-smooth(-.130,-.100,y))
 q[:,2]-=.0015*lid
 return q

def teeth():
 for o in [o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Canine')]:
  p=read(o);c=p.mean(0);side=np.sign(c[0]);verts=[];faces=[]
  root=c+np.array([0.,.003,.002]);mid=c+np.array([side*.0002,-.0007,-.001]);tip=c+np.array([side*.00035,.0001,-.004])
  for i,t in enumerate(np.linspace(0,1,12)):
   center=(1-t)**2*root+2*t*(1-t)*mid+t*t*tip;r=.00125*max(.025,(1-t)**.8)
   for k in range(10):
    a=2*math.pi*k/10;verts.append(center+[r*math.cos(a),.8*r*math.sin(a),0])
    if i:
     j=(i-1)*10+k;jn=(i-1)*10+(k+1)%10;faces.append((j,jn,jn+10,j+10))
  faces.append(tuple(reversed(range(10))));faces.append(tuple(110+k for k in range(10)))
  m=bpy.data.meshes.new('Seated canine');m.from_pydata(verts,[],faces);m.update()
  for mat in o.data.materials:m.materials.append(mat)
  o.data=m
  for f in m.polygons:f.use_smooth=True

def markings():
 m=bpy.data.materials['Skin | cool slate'];n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF')
 attr=n.new('ShaderNodeAttribute');attr.attribute_name='source_position';sep=n.new('ShaderNodeSeparateXYZ');l.new(attr.outputs['Vector'],sep.inputs[0])
 def op(kind,a,b=None):
  nd=n.new('ShaderNodeMath');nd.operation=kind
  for i,v in enumerate([a] if b is None else [a,b]):
   if isinstance(v,(int,float,np.floating)):nd.inputs[i].default_value=float(v)
   else:l.new(v,nd.inputs[i])
  return nd.outputs[0]
 ax=op('ABSOLUTE',sep.outputs[0]);yy=sep.outputs[1];zz=sep.outputs[2];mask=0.
 for cx,cz,wx,wz,theta in [(.164,1.315,.007,.024,.70),(.187,1.279,.006,.025,.78),(.208,1.245,.005,.023,.80),(.264,1.049,.006,.028,.62),(.286,1.008,.0055,.025,.65),(.306,.969,.0045,.021,.70)]:
  dx=op('SUBTRACT',ax,cx);dz=op('SUBTRACT',zz,cz)
  u=op('SUBTRACT',op('MULTIPLY',dx,math.cos(theta)),op('MULTIPLY',dz,math.sin(theta)))
  v=op('DIVIDE',op('ADD',op('MULTIPLY',dx,math.sin(theta)),op('MULTIPLY',dz,math.cos(theta))),wz)
  av=op('ABSOLUTE',v);width=op('MULTIPLY',wx,op('POWER',op('MAXIMUM',.0001,op('SUBTRACT',1.,av)),.72))
  un=op('DIVIDE',op('ABSOLUTE',op('SUBTRACT',u,op('MULTIPLY',.0025,op('MULTIPLY',v,v)))),width)
  leaf=op('MINIMUM',1.,op('MAXIMUM',0.,op('MULTIPLY',15.,op('SUBTRACT',1.,un))))
  gate=op('MINIMUM',1.,op('MAXIMUM',0.,op('DIVIDE',op('SUBTRACT',.040,yy),.030)))
  mask=op('MAXIMUM',mask,op('MULTIPLY',op('MULTIPLY',leaf,op('LESS_THAN',av,1.)),gate))
 color=n.new('ShaderNodeVertexColor');color.layer_name='Complexion';mix=n.new('ShaderNodeMixRGB');l.new(color.outputs['Color'],mix.inputs[1]);l.new(mask,mix.inputs[0]);mix.inputs[2].default_value=(.040,.034,.068,1);l.new(mix.outputs[0],bs.inputs['Base Color'])

def apply(body):
 put(body,face_shape(read(body)))
 for o in bpy.data.objects:
  if o.type=='MESH' and o.name.startswith(('Upper liner','Outer eyelash')):put(o,face_shape(read(o)))
 teeth();markings();body['detail009']='Whole mandibular contour, relaxed eyelids, seated canine roots, separate transverse markings'
