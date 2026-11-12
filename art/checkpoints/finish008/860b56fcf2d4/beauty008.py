"""Final identity refinement, operating on complete anatomy rather than separate spheres."""
import math
import bpy
import numpy as np

def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def coords(o):
 p=np.empty(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',p);return p.reshape(-1,3)
def put(o,p):
 assert np.isfinite(p).all();o.data.vertices.foreach_set('co',p.ravel());o.data.update()
def linear(c):
 c=np.array(c);return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)

def transform(p):
 x,y,z=p.T;ax=abs(x);sg=np.sign(x);q=p.copy()
 face=1-smooth(-.035,.035,y)
 jaw=np.exp(-((z-1.735)/.038)**2)*smooth(.022,.055,ax)*face
 q[:,0]-=x*.10*jaw
 chin=np.exp(-((z-1.711)/.023)**2-(x/.040)**2)*face
 q[:,2]+=.0035*chin
 eye=np.exp(-((ax-.0415)/.031)**4-((z-1.824)/.026)**4)*(1-smooth(-.075,-.035,y))
 q[:,0]+=sg*(ax-.0415)*.12*eye;q[:,2]+=(z-1.824)*.15*eye
 nose=np.exp(-((z-1.777)/.020)**4-(x/.029)**4)*(1-smooth(-.162,-.125,y))
 q[:,0]-=x*.10*nose;q[:,1]+=.0013*nose;q[:,2]-=.0018*nose
 return q

def apply(body):
 put(body,transform(coords(body)))
 for o in bpy.data.objects:
  if o.type!='MESH' or o==body:continue
  if o.name.startswith(('Eye.','Iris.','Brow','Upper liner','Outer eyelash','Canine')):put(o,transform(coords(o)))
  if o.name.startswith('Gathered soft neck passage'):
   a=coords(o)
   if len(a)==60*31:
    rows=a.reshape(60,31,3)
    for i,row in enumerate(rows):
     t=i/59;center=row.mean(0);w=float(smooth(.03,.26,t))
     row[:]=center+(row-center)*(1-.18*w)
     radial=np.array([center[0],center[1]-.012,0]);radial/=max(np.linalg.norm(radial),1e-9)
     for j,u in enumerate(np.linspace(-1,1,31)):
      row[j]+=radial*(.0008*w*math.sin(2.3*math.pi*u+4*t))
    put(o,a)
  if o.name.startswith('Crown sweep'):
   a=coords(o);w=np.exp(-((a[:,2]-1.965)/.028)**2-((abs(a[:,0])-.060)/.045)**2);a[:,2]-=.0055*w;put(o,a)
 for mat in bpy.data.materials:
  if not mat.use_nodes:continue
  bs=mat.node_tree.nodes.get('Principled BSDF')
  if not bs:continue
  if mat.name.startswith('Hair | Art008'):
   for n in mat.node_tree.nodes:
    if n.type=='VALTORGB':
     n.color_ramp.elements[0].color=(*linear((.47,.50,.56)),1);n.color_ramp.elements[-1].color=(*linear((.84,.86,.89)),1)
   bs.inputs['Roughness'].default_value=.46
  if mat.name.startswith('Nails'):
   bs.inputs['Base Color'].default_value=(*linear((.28,.255,.36)),1);bs.inputs['Roughness'].default_value=.34
  if mat.name.startswith('Horns'):
   bs.inputs['Roughness'].default_value=.45;bs.inputs['Coat Weight'].default_value=.06
 body['beauty008']='Coherent lower jaw, larger eyelid/eye region, tapered nose, soft narrow neck drape and balanced ivory hair'
