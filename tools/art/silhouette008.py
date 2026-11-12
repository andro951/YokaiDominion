"""Repair actual back-view art defects; preserve old components hidden for edit history."""
import math
import bpy,bmesh
import numpy as np
from mathutils import Vector

def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)

def tube(name,points,width,depth,material,sides=12):
 p=np.array(points);w=np.broadcast_to(width,(len(p),));d=np.broadcast_to(depth,(len(p),));verts=[];faces=[]
 for i,c in enumerate(p):
  t=p[min(i+1,len(p)-1)]-p[max(0,i-1)];t/=max(np.linalg.norm(t),1e-12)
  a=np.cross([0.,1.,0.],t)
  if np.linalg.norm(a)<1e-8:a=np.cross([1.,0.,0.],t)
  a/=np.linalg.norm(a);b=np.cross(t,a)
  for j in range(sides):
   th=2*math.pi*j/sides;ridge=1+.035*math.cos(6*th+i*.04)
   verts.append(c+ridge*(w[i]*math.cos(th)*a+d[i]*math.sin(th)*b))
  if i:
   for j in range(sides):
    k=(i-1)*sides+j;kn=(i-1)*sides+(j+1)%sides;faces.append((k,kn,kn+sides,k+sides))
 faces.append(tuple(reversed(range(sides))));faces.append(tuple((len(p)-1)*sides+j for j in range(sides)))
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);mesh.materials.append(material)
 uv=mesh.uv_layers.new(name='StrandUV')
 for f in mesh.polygons:
  ids=[mesh.loops[li].vertex_index for li in f.loop_indices];us=[(j%sides)/sides for j in ids];seam=max(us)-min(us)>.5
  for li,j,u in zip(f.loop_indices,ids,us):uv.data[li].uv=(u+1 if seam and u<.5 else u,(j//sides)/(len(p)-1))
  f.use_smooth=True
 mod=o.modifiers.new('Flowing silhouette','SUBSURF');mod.levels=mod.render_levels=1
 return o

def fill_mane():
 core=bpy.data.objects.get('Continuous inner mane')
 if core:core.hide_render=True;core.hide_viewport=True;core['replaced_by']='Art008 layered inner locks'
 mat=bpy.data.materials.get('Hair | Art008 strand-aligned ivory') or bpy.data.materials['Hair | ivory silver']
 for j in range(-7,8):
  phase=.63*j;t=np.linspace(0,1,74);f=j/7
  # Attached to scalp at the root; broad overlapping locks cover the old diamond plate.
  x=f*(.065+.105*smooth(0,.38,t))+.012*np.sin(3*math.pi*t+phase)*np.sin(math.pi*t)
  y=.076+.170*smooth(0,.46,t)+.012*np.sin(3.3*math.pi*t+phase)*np.sin(math.pi*t)
  end=1.025+.11*abs(f)+.024*math.sin(phase+1)
  z=1.86+(end-1.86)*t
  taper=np.maximum(.008,(1-smooth(.68,1,t)))
  width=(.014+.012*np.sin(math.pi*t))*taper
  depth=(.010+.004*np.sin(math.pi*t))*taper
  tube('Art008 inner flowing lock %02d'%(j+7),np.c_[x,y,z],width,depth,mat)


def finish_tail_opening():
 cloth=bpy.data.objects.get('Gathered rear skirt');tail=bpy.data.objects.get('Tail')
 if not cloth or not tail:return
 bm=bmesh.new();bm.from_mesh(cloth.data)
 boundary=[v for v in bm.verts if v.is_boundary and abs(v.co.x-.031)<.065 and .92<v.co.z<1.07]
 if len(boundary)<6:bm.free();return
 mean_y=sum(v.co.y for v in boundary)/len(boundary)
 p=np.array([v.co[:] for v in tail.data.vertices]);count=(len(p)-2)//20
 if count*20+2!=len(p):bm.free();return
 rings=p[:count*20].reshape(count,20,3);centers=rings.mean(1)
 # Find the actual intersection with the garment's rear plane.
 i=int(np.argmin(abs(centers[:,1]-mean_y)));center=centers[i]
 radius=float(np.mean(np.linalg.norm(rings[i]-center,axis=1)))
 rx=max(.018,radius+.004);rz=rx*1.30
 old=np.mean([tuple(v.co) for v in boundary],axis=0)
 for v in boundary:
  theta=math.atan2((v.co.z-old[2])/.039,(v.co.x-old[0])/.034)
  v.co.x=center[0]+rx*math.cos(theta);v.co.z=center[2]+rz*math.sin(theta)
 bm.to_mesh(cloth.data);bm.free();cloth.data.update()
 material=cloth.data.materials[0]
 t=np.linspace(0,2*math.pi,65);pts=np.c_[center[0]+rx*np.cos(t),np.full(len(t),mean_y+.0010),center[2]+rz*np.sin(t)]
 tube('Art008 tailored tail opening hem',pts,.0011,.0011,material,sides=8)
 cloth['tail_opening']='Rounded to actual tail intersection, with cloth hem; not a punched polygon hole'


def markings():
 mat=bpy.data.materials.get('Skin | cool slate')
 if not mat or not mat.use_nodes:return
 n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n.get('Principled BSDF')
 mix=bs.inputs['Base Color'].links[0].from_node
 if mix.type!='MIX_RGB':return
 attr=n.new('ShaderNodeAttribute');attr.attribute_name='source_position';sep=n.new('ShaderNodeSeparateXYZ');l.new(attr.outputs['Vector'],sep.inputs[0])
 def op(kind,a,b=None):
  nd=n.new('ShaderNodeMath');nd.operation=kind
  for i,v in enumerate([a] if b is None else [a,b]):
   if isinstance(v,(int,float,np.floating)):nd.inputs[i].default_value=float(v)
   else:l.new(v,nd.inputs[i])
  return nd.outputs[0]
 ax=op('ABSOLUTE',sep.outputs[0]);yy=sep.outputs[1];zz=sep.outputs[2];mask=0.
 for cx,cz,wx,wz,angle in [(.164,1.315,.011,.022,-.57),(.187,1.287,.010,.026,-.55),(.210,1.256,.0085,.026,-.50),(.264,1.049,.0085,.032,-.48),(.286,1.008,.007,.029,-.48),(.306,.969,.006,.025,-.48)]:
  dx=op('SUBTRACT',ax,cx);dz=op('SUBTRACT',zz,cz)
  u=op('SUBTRACT',op('MULTIPLY',dx,math.cos(angle)),op('MULTIPLY',dz,math.sin(angle)))
  v=op('DIVIDE',op('ADD',op('MULTIPLY',dx,math.sin(angle)),op('MULTIPLY',dz,math.cos(angle))),wz)
  av=op('ABSOLUTE',v);profile=op('MAXIMUM',.0001,op('SUBTRACT',1.,av));width=op('MULTIPLY',wx,op('POWER',profile,.72))
  curve=op('MULTIPLY',.003,op('MULTIPLY',v,v));un=op('DIVIDE',op('ABSOLUTE',op('SUBTRACT',u,curve)),width)
  leaf=op('MINIMUM',1.,op('MAXIMUM',0.,op('MULTIPLY',18.,op('SUBTRACT',1.,un))))
  leaf=op('MULTIPLY',leaf,op('LESS_THAN',av,1.));gate=op('MINIMUM',1.,op('MAXIMUM',0.,op('DIVIDE',op('SUBTRACT',.040,yy),.030)))
  mask=op('MAXIMUM',mask,op('MULTIPLY',leaf,gate))
 l.new(mask,mix.inputs[0])


def apply(body):
 fill_mane();finish_tail_opening();markings()
 body['silhouette008']='Back hair filler replaced; rounded and fitted tail opening; pointed markings'
