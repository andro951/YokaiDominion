"""Continuous rooted back groom; front framing locks and scalp remain intact."""
import math
import bpy
import numpy as np

def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)

def lock(name,points,width,depth,material):
 points=np.asarray(points);n=len(points);sides=16;vv=[];ff=[]
 for i,c in enumerate(points):
  tangent=points[min(i+1,n-1)]-points[max(0,i-1)];tangent/=np.linalg.norm(tangent)
  wide=np.array([1.,0.,0.]);wide-=tangent*np.dot(wide,tangent);wide/=np.linalg.norm(wide);normal=np.cross(tangent,wide)
  for j in range(sides):
   a=2*math.pi*j/sides;shape=1+.025*math.cos(6*a+.3*i/n)
   vv.append(c+shape*(width[i]*math.cos(a)*wide+depth[i]*math.sin(a)*normal))
  if i:
   for j in range(sides):
    k=(i-1)*sides+j;kn=(i-1)*sides+(j+1)%sides;ff.append((k,kn,kn+sides,k+sides))
 vv.extend([points[0],points[-1]])
 for j in range(sides):
  ff.append((n*sides,(j+1)%sides,j));ff.append((n*sides+1,(n-1)*sides+j,(n-1)*sides+(j+1)%sides))
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(vv,[],ff);mesh.update();obj=bpy.data.objects.new(name,mesh);bpy.data.collections['03_HAIR'].objects.link(obj);mesh.materials.append(material)
 uv=mesh.uv_layers.new(name='StrandUV')
 for f in mesh.polygons:
  f.use_smooth=True;ids=[mesh.loops[li].vertex_index for li in f.loop_indices];us=[(v%sides)/sides if v<n*sides else .5 for v in ids];seam=max(us)-min(us)>.5
  for li,v,u in zip(f.loop_indices,ids,us):uv.data[li].uv=(u+1 if seam and u<.5 else u,(v//sides)/(n-1) if v<n*sides else (0 if v==n*sides else 1))
 mod=obj.modifiers.new('Continuous flowing groom','SUBSURF');mod.levels=mod.render_levels=1
 obj['groom_description']='Rooted long S-wave; variable end length; preserved volume with strand-opacity overlay'
 return obj

def apply(body):
 for o in bpy.data.objects:
  if o.type=='MESH' and o.name.startswith(('Back wave','Art008 inner flowing lock','Continuous inner mane')):
   o.hide_render=True;o.hide_viewport=True;o['replaced_by']='Art009 continuous back groom'
 mat=bpy.data.materials.get('Hair | Art008 strand-aligned ivory') or bpy.data.materials['Hair | ivory silver']
 rng=np.random.default_rng(90091)
 # Long inner layer provides continuous mass, not a flat diamond or a fringe of spikes.
 for j,f in enumerate(np.linspace(-1,1,23)):
  t=np.linspace(0,1,76);phase=.8*f+rng.uniform(-.25,.25)
  spread=.063+.137*smooth(0,.43,t)-.020*smooth(.83,1,t)
  x=f*spread+.013*np.sin(3.2*math.pi*t+phase)*np.sin(math.pi*t)
  y=.064+.118*smooth(0,.43,t)+.045*np.sqrt(max(0,1-f*f))*smooth(0,.25,t)
  y+=.011*np.sin(3.2*math.pi*t+phase+1)*np.sin(math.pi*t)
  z0=1.934-.045*abs(f);zend=1.035+.080*abs(f)+rng.uniform(-.030,.040)
  z=z0+(zend-z0)*t
  width=(.008+.012*np.sin(math.pi*t)**.7)*(1-smooth(.78,1,t))+.00012
  depth=(.005+.005*np.sin(math.pi*t))*(1-smooth(.77,1,t))+.00008
  lock('Back wave 009.inner.%02d'%j,np.c_[x,y,z],width,depth,mat)
 # A staggered outer layer follows the same flow but breaks uniform long sections.
 for j,f in enumerate(np.linspace(-.93,.93,13)):
  t=np.linspace(0,1,76);phase=.8*f+rng.uniform(-.20,.20)
  zend=1.17+rng.uniform(-.08,.12)+.05*abs(f);z0=1.928-.035*abs(f)
  x=f*(.066+.140*smooth(0,.49,t))+.016*np.sin(3.0*math.pi*t+phase)*np.sin(math.pi*t)
  y=.077+.126*smooth(0,.43,t)+.045*np.sqrt(max(0,1-f*f))*smooth(0,.25,t)+.010*np.sin(3*math.pi*t+phase+1)*np.sin(math.pi*t)
  z=z0+(zend-z0)*t
  width=(.008+.012*np.sin(math.pi*t)**.8)*(1-smooth(.64,1,t))+.00010
  depth=(.004+.003*np.sin(math.pi*t))*(1-smooth(.65,1,t))+.00006
  lock('Back wave 009.outer.%02d'%j,np.c_[x,y,z],width,depth,mat)
 body['groom009']='36 continuous long rooted wavy locks replace stepped back filler; front face framing retained'
