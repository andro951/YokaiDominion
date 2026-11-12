"""Continuous skin marking shader, natural eye surfaces and finished hair details."""
import math,random
import bpy
import numpy as np
from mathutils import Vector
from geometry import mesh,tube
from materials import linear,base
import finish_details

def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)

def finish_skin(body,mat):
 n=len(body.data.vertices);src=np.empty(n*3);body.data.attributes['source_position'].data.foreach_get('vector',src);src=src.reshape(-1,3);x,y,z=src.T
 ca=body.data.color_attributes['Complexion'];c=np.empty(n*4);ca.data.foreach_get('color',c);c=c.reshape(-1,4)
 arm=(np.abs(x)>.13)&(z>.89)&(z<1.36);c[arm,:3]=linear((.425,.433,.520));ca.data.foreach_set('color',c.ravel())
 m=mat['skin'];nodes=m.node_tree.nodes;links=m.node_tree.links;bs=nodes.get('Principled BSDF');original=bs.inputs['Base Color'].links[0].from_socket
 attr=nodes.new('ShaderNodeAttribute');attr.attribute_name='source_position';sep=nodes.new('ShaderNodeSeparateXYZ');links.new(attr.outputs['Vector'],sep.inputs[0])
 def op(kind,a,b=None):
  o=nodes.new('ShaderNodeMath');o.operation=kind
  for i,v in enumerate([a,b] if b is not None else [a]):
   if isinstance(v,(int,float,np.floating)):o.inputs[i].default_value=float(v)
   else:links.new(v,o.inputs[i])
  return o.outputs[0]
 ax=op('ABSOLUTE',sep.outputs[0]);yy=sep.outputs[1];zz=sep.outputs[2];mask=0.
 # Leaf-shaped strokes evaluated per shading point, not jagged per-vertex blobs.
 for cx,cz,wx,wz,theta in [(.164,1.315,.012,.021,-.58),(.187,1.287,.011,.026,-.55),(.210,1.256,.010,.026,-.50),(.264,1.049,.009,.030,-.48),(.286,1.008,.008,.029,-.48),(.306,.969,.007,.026,-.48)]:
  dx=op('SUBTRACT',ax,cx);dz=op('SUBTRACT',zz,cz)
  u=op('SUBTRACT',op('MULTIPLY',dx,math.cos(theta)),op('MULTIPLY',dz,math.sin(theta)))
  v=op('ADD',op('MULTIPLY',dx,math.sin(theta)),op('MULTIPLY',dz,math.cos(theta)))
  vn=op('DIVIDE',v,wz);taper=op('MAXIMUM',.18,op('ADD',.78,op('MULTIPLY',vn,.22)))
  un=op('DIVIDE',u,op('MULTIPLY',wx,taper));r=op('ADD',op('MULTIPLY',un,un),op('MULTIPLY',vn,vn))
  leaf=op('MINIMUM',1.,op('MAXIMUM',0.,op('DIVIDE',op('SUBTRACT',1.,r),.08)))
  gate=op('MINIMUM',1.,op('MAXIMUM',0.,op('DIVIDE',op('SUBTRACT',.040,yy),.030)))
  mask=op('MAXIMUM',mask,op('MULTIPLY',leaf,gate))
 mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX';links.new(mask,mix.inputs[0]);links.new(original,mix.inputs[1]);mix.inputs[2].default_value=(*linear((.205,.20,.29)),1);links.new(mix.outputs[0],bs.inputs['Base Color'])
 noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=115;noise.inputs['Detail'].default_value=3
 ramp=nodes.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=0;ramp.inputs['From Max'].default_value=1;ramp.inputs['To Min'].default_value=.44;ramp.inputs['To Max'].default_value=.60
 links.new(noise.outputs['Fac'],ramp.inputs['Value']);links.new(ramp.outputs[0],bs.inputs['Roughness'])
 body['surface_markings']='Analytic source-space shader; bake into base color for portable exports'

def finish_eyes(eyes):
 for o in list(bpy.data.objects):
  if o.name.startswith('Iris.'):bpy.data.objects.remove(o,do_unlink=True)
 for eye in eyes:
  co=np.array([v.co[:] for v in eye.data.vertices]);center=(co.min(0)+co.max(0))*.5;radius=float(np.median(np.ptp(co,axis=0)*.5))
  ri=.0065;rp=.0028;gaze=np.array((-.010 if center[0]>0 else .010,-1.,.08));gaze/=np.linalg.norm(gaze)
  right=np.cross(gaze,[0.,0.,1.]);right/=np.linalg.norm(right);up=np.cross(right,gaze);vv=[];ff=[];cc=[];uv=[];rings=40;segments=128
  for j in range(rings):
   r=.000005+(ri-.000005)*j/(rings-1);h=math.sqrt(max(1e-9,radius*radius-r*r))+.00018+.00015*(1-r/ri)**2
   for k in range(segments):
    a=2*math.pi*k/segments;t=r/ri
    vv.append(center+gaze*h+r*(math.cos(a)*right+math.sin(a)*up));uv.append((.5+.5*t*math.cos(a),.5+.5*t*math.sin(a)))
    f=(math.sin(a*71+r*1900)+.48*math.sin(a*123-r*3600)+.25*math.sin(a*197+r*1200))/1.73
    c=np.array((.38,.33,.57))*(.88+.19*f)
    c+=np.array((.055,.035,.05))*math.exp(-((t-.53)/.09)**2)
    if r<rp:c=np.array((.012,.009,.024))
    elif r<rp+.00028:c*=.48
    if t>.86:c*=max(.10,(1-t)/.14)
    cc.append(linear(c))
    if j:
     p=(j-1)*segments+k;q=(j-1)*segments+(k+1)%segments;ff.append((p,q,q+segments,p+segments))
  o=mesh('Iris.'+eye.name,vv,ff,uvs=uv);m,bs=base('Iris | layered violet '+eye.name,(1,1,1),.16);bs.inputs['Coat Weight'].default_value=.55;bs.inputs['Coat Roughness'].default_value=.07
  colors=o.data.color_attributes.new(name='IrisColour',type='FLOAT_COLOR',domain='POINT');colors.data.foreach_set('color',np.c_[np.array(cc),np.ones(len(cc))].ravel())
  a=m.node_tree.nodes.new('ShaderNodeVertexColor');a.layer_name='IrisColour';m.node_tree.links.new(a.outputs['Color'],bs.inputs['Base Color']);o.data.materials.append(m)
  for m in eye.data.materials:
   bs=m.node_tree.nodes.get('Principled BSDF')
   if bs:
    bs.inputs['Base Color'].default_value=(*linear((.67,.70,.73)),1);bs.inputs['Roughness'].default_value=.12;bs.inputs['Coat Weight'].default_value=.30

def finish_hair(mat):
 # Break the bilateral wig symmetry without moving attachment roots.
 rng=random.Random(606)
 locks=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('Back wave','Side S wave','Face wave','Crown sweep'))]
 for o in locks:
  verts=np.array([v.co[:] for v in o.data.vertices]);rings=76;sides=16
  if len(verts)!=rings*sides+2:continue
  a=verts[:rings*sides].reshape(rings,sides,3);centers=a.mean(1);f=rng.uniform(-1,1)
  for i,t in enumerate(np.linspace(0,1,rings)):
   w=math.sin(math.pi*t)**2;delta=np.array([.0045*f*w,.003*f*w,.0035*f*w])
   a[i]+=delta
  # A few fine silhouette hairs follow, rather than cross through, each lock.
  if o.name.startswith(('Side S wave','Face wave')):
   for j in (2,6,10):
    points=[]
    for i in range(6,rings-2):
     c=a[i].mean(0);p=a[i,j];d=p-c;d/=max(np.linalg.norm(d),1e-9)
     points.append(p+d*(.00035+.0014*math.sin(math.pi*(i-6)/(rings-8))**2))
    tube('Hair fine silhouette',points,[.00017,.00013,.000035],mat['hair'],n=58,sides=4)
  o.data.vertices.foreach_set('co',verts.ravel());o.data.update()
 m=mat['hair'];nodes=m.node_tree.nodes;bs=nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.44;bs.inputs['Anisotropic'].default_value=.48
 for n in nodes:
  if n.type=='VALTORGB':
   n.color_ramp.elements[0].color=(*linear((.57,.60,.67)),1);n.color_ramp.elements[-1].color=(*linear((.85,.87,.90)),1)
  if n.type=='BUMP':n.inputs['Strength'].default_value=.12;n.inputs['Distance'].default_value=.00012
  if n.type=='VECT_MATH' and n.operation=='MULTIPLY':n.inputs[1].default_value=(170,2,1)
 # Finish the tail-tip silhouette without increasing the body's geometric density.
 o=bpy.data.objects.get('Tail spade')
 if o:
  mod=o.modifiers.new('Tail tip smooth silhouette','SUBSURF');mod.levels=mod.render_levels=1

def install():
 previous=finish_details.build
 def build(body,eyes,mat,bvh,front):
  previous(body,eyes,mat,bvh,front);finish_skin(body,mat);finish_eyes(eyes);finish_hair(mat)
 finish_details.build=build
