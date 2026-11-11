"""Reference proportions, muscular contours and tailored garment silhouettes."""
from pathlib import Path
import sys,math
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import sculpt_character_likeness as s
f=s.f;b=s.b;a=s.a;p=s.p;t=s.t;r=s.r
oldload=a.load_data;oldbody=f.make_anatomy;oldface=f.make_face;oldbind=f.bind_all


def load(path):
 a.TARGETS['macrodetails/caucasian-female-young.target']=.5
 a.TARGETS['macrodetails/asian-female-young.target']=.5
 for side in ['l','r']:
  a.TARGETS[f'eyes/{side}-eye-trans-out.target']=1.6
  a.TARGETS[f'eyes/{side}-eye-scale-incr.target']=1.6
  a.TARGETS[f'eyes/{side}-eye-corner2-up.target']=.9
  a.TARGETS[f'eyes/{side}-eye-corner1-down.target']=.20
  a.TARGETS[f'eyes/{side}-eye-height2-decr.target']=.35
  a.TARGETS[f'eyes/{side}-eye-height1-decr.target']=.05
  a.TARGETS[f'eyes/{side}-eye-height3-decr.target']=.05
  a.TARGETS[f'cheek/{side}-cheek-bones-incr.target']=.35
  a.TARGETS[f'cheek/{side}-cheek-inner-decr.target']=.10
 a.TARGETS['nose/nose-point-down.target']=.65
 a.TARGETS['nose/nose-nostrils-angle-down.target']=.90
 a.TARGETS['nose/nose-width3-decr.target']=.25
 a.TARGETS['mouth/mouth-angles-up.target']=.45
 a.TARGETS['mouth/mouth-lowerlip-height-decr.target']=.50
 a.TARGETS['mouth/mouth-lowerlip-volume-decr.target']=.30
 a.TARGETS['stomach/stomach-tone-incr.target']=.70
 return p.old_load(path)
a.load_data=load


def muscle_sculpt(o):
 for q in o.data.vertices:
  co=q.co;sign=1 if co.x>0 else -1
  groups={o.vertex_groups[g.group].name:g.weight for g in q.groups}
  armweight=sum(w for n,w in groups.items() if n.startswith(('UpperArm','Forearm')))
  if armweight<.02:continue
  shoulder=Vector((sign*.305,-.010,1.61));elbow=Vector((sign*.455,-.018,1.28));wrist=Vector((sign*.555,-.022,1.055))
  for start,end,kind in [(shoulder,elbow,'upper'),(elbow,wrist,'lower')]:
   axis=end-start;u=(co-start).dot(axis)/axis.length_squared
   if not 0<u<1:continue
   center=start+u*axis;radial=co-center;radial-=axis.normalized()*radial.dot(axis.normalized())
   if radial.length<.01:continue
   n=radial.normalized();front=max(0.,-n.y);back=max(0.,n.y)
   if kind=='upper':
    biceps=.019*math.sin(math.pi*u)**1.7*front**1.8
    triceps=.012*math.sin(math.pi*u)**1.9*back**1.4
    deltoid=.015*math.exp(-((u-.16)/.19)**2)*(1-.35*abs(n.y))
    separator=-.004*math.exp(-((u-.33)/.08)**2)*(1-.55*abs(n.y))
    d=biceps+triceps+deltoid+separator
   else:d=.011*math.exp(-((u-.30)/.27)**2)*(.5+.5*front)+.004*math.exp(-((u-.50)/.25)**2)*max(0.,sign*n.x)
   co+=n*d*min(1,armweight)


def body(path):
 obj,v,d,w=oldbody(path);muscle_sculpt(obj)
 g=obj.vertex_groups.new(name='FinishChestBlend')
 for q in obj.data.vertices:
  x,y,z=q.co
  amount=f.ss(1.18,1.25,z)*(1-f.ss(1.62,1.70,z))*f.ss(-.08,-.18,y)*(1-f.ss(.34,.42,abs(x)))
  if amount>.001:g.add([q.index],amount,'REPLACE')
 mod=obj.modifiers.new('HandFinishedContourRelax','SMOOTH');mod.factor=.35;mod.iterations=10;mod.vertex_group=g.name;f.apply(obj,mod);obj.vertex_groups.remove(obj.vertex_groups['FinishChestBlend'])
 col=obj.data.color_attributes['SkinPalette'];base=Vector(b.MATS['Skin'].diffuse_color[:3]);ink=Vector(b.MATS['Ink'].diffuse_color[:3]);lip=Vector(b.MATS['Lip'].diffuse_color[:3])
 eye_centers=[Vector(v[d['joints'][d['bones']['eye.'+side]['head']]].mean(0)) for side in ['L','R']]
 for q in obj.data.vertices:
  x,y,z=q.co;color=base.copy()
  if z>1.70 and y<-.13:
   for ec in eye_centers:
    dx=(x-ec.x)/.039;dz=(z-ec.z-.010)/.019
    makeup=.33*math.exp(-(dx*dx+dz*dz)*2)*f.ss(ec.z-.001,ec.z+.009,z)
    color=color.lerp(ink,makeup)
   lips=.24*math.exp(-((x/.040)**4+((z-1.750)/.009)**4))
   color=color.lerp(lip,lips)
  col.data[q.index].color=(*color,1)
 s.update_tree(obj);return obj,v,d,w
f.make_anatomy=body


def face(v,definition):
 oldface(v,definition)
 for o in f.PARTS:
  if o.name.startswith('Fang.'):
   for q in o.data.vertices:q.co.z=1.755+(q.co.z-1.755)*.70
 for side in ['L','R']:
  for i,label in enumerate(['Thumb','Index','Middle','Ring','Little'],1):
   name=f'finger{i}-3.{side}';data=definition['bones'][name]
   aa=Vector(v[definition['joints'][data['head']]].mean(0));cc=Vector(v[definition['joints'][data['tail']]].mean(0))
   axis=(cc-aa).normalized();center=aa.lerp(cc,.65);front=Vector((0,-1,0));front-=axis*front.dot(axis);front.normalize();center+=front*.007
   o=f.sphere(f'Nail.{label}3.{side}',center,(.0048,.0018,max(.0055,(cc-aa).length*.27)),'Nail')
   rot=Vector((0,0,1)).rotation_difference(axis)
   for q in o.data.vertices:q.co=center+rot@(q.co-center)
 for o in f.PARTS:
  if o.name.startswith('Fang.'):o['bind_bone']='Jaw'
f.make_face=face


def garment():
 f.original_clothing_builder()
 for o in list(f.PARTS):
  if o.name.startswith(('ChestDrape','BackStrap')):
   f.PARTS.remove(o);bpy.data.objects.remove(o,do_unlink=True)
 obj=f.BODY;bad=('UpperArm','Forearm','Hand','Thumb','Index','Middle','Ring','Little','metacarpal')
 faces=[tuple(poly.vertices) for poly in obj.data.polygons if sum(sum(g.weight for g in obj.data.vertices[vi].groups if obj.vertex_groups[g.group].name.startswith(bad)) for vi in poly.vertices)/len(poly.vertices)<.20]
 tree=BVHTree.FromPolygons([q.co for q in obj.data.vertices],faces)
 levels=[1.195,1.225,1.28,1.36,1.445,1.53,1.61,1.675]
 inner=[.058,.072,.112,.170,.199,.184,.145,.118]
 outer=[.147,.192,.302,.365,.385,.326,.222,.171]
 def curve(z,values):
  k=max(0,min(len(levels)-2,np.searchsorted(levels,z)-1));t=(z-levels[k])/(levels[k+1]-levels[k]);return r.cat(values[max(0,k-1)],values[k],values[k+1],values[min(len(values)-1,k+2)],t)
 for sign in [-1,1]:
  nx,ny=48,104;verts=[];uv=[];faces=[]
  for i in range(ny+1):
   t=i/ny;z=1.675-(1.675-1.195)*t;left,right=curve(z,inner),curve(z,outer)
   for j in range(nx+1):
    u=j/nx;x=left+(right-left)*u
    hit,n,_,_=tree.ray_cast(Vector((x,-2,z)),Vector((0,1,0)),3.)
    if hit is None:hit,n,_,_=tree.find_nearest(Vector((x,-.15,z)))
    point=Vector((x,hit.y-.008,z)) if abs(hit.x-x)<.015 else hit+n*.008
    fold=.0022*math.sin(4.5*math.pi*u+t*3)*math.sin(math.pi*t)**1.4
    fold+=.0038*math.sin(7*math.pi*u+t*2)*math.exp(-((t-.82)/.14)**2)*math.sin(math.pi*t)
    point.y-=fold;point.x*=sign;verts.append(tuple(point));uv.append((u,t))
  for i in range(ny):
   for j in range(nx):
    p=i*(nx+1)+j;face=(p,p+1,p+nx+2,p+nx+1);faces.append(tuple(reversed(face)) if sign>0 else face)
  o=f.mesh('ChestDrape.'+str(sign),verts,faces,'Cloth',uv)
  points=np.array(verts).reshape((ny+1,nx+1,3))
  for _ in range(10):
   new=points.copy();new[1:-1]=points[1:-1]*.6+(points[:-2]+points[2:])*.2;points=new
  for q,co in zip(o.data.vertices,points.reshape((-1,3))):
   hit,n,_,_=tree.ray_cast(Vector((abs(co[0]),-2,co[2])),Vector((0,1,0)),3.)
   if hit is not None:co[1]=min(co[1],hit.y-.005)
   q.co=co
  solid=o.modifiers.new('HemmedFabric','SOLIDIFY');solid.thickness=.0025;solid.offset=0;f.apply(o,solid)
  start=Vector(verts[nx//2]);pts=[tuple(start),(sign*.147,-.025,1.684),(sign*.144,.038,1.674),(sign*.137,.093,1.59),(sign*.13,.115,1.40),(sign*.11,.15,1.21)]
  f.sweep('BackStrap.'+str(sign),pts,[.025,.025,.024,.027,.032,.035],[.0017]*6,material='Cloth',sides=12,steps=12)
 for o in f.PARTS:
  if o.name=='WaistSash' or o.name.startswith('SashFold'):
   for q in o.data.vertices:
    x,y,z=q.co;direction=Vector((x,y+.009,0)).normalized();hit,n,_,_=tree.ray_cast(Vector((0,-.009,z)),direction,1.)
    if hit is not None:
     radius=(Vector((x,y,z))-Vector((0,-.009,z))).length;target=(hit-Vector((0,-.009,z))).length+.010
     scale=target/max(.0001,radius);q.co.x*=scale;q.co.y=(q.co.y+.009)*scale-.009
 for o in f.PARTS:
  if o.name in ['FrontDrape','RearDrape']:
   back=o.name=='RearDrape'
   for q in o.data.vertices:
    x,y,z=q.co;t=(1.185-z)/.86;u=x/.21
    folds=.012*math.exp(-((t-(.14+.12*u))/.045)**2)+.015*math.exp(-((t-(.31-.09*u))/.060)**2)
    q.co.y+=folds*(1 if back else -1)
 for o in f.PARTS:
  if o.data.uv_layers:
   layer=o.data.uv_layers.active
   for poly in o.data.polygons:
    us=[layer.data[li].uv.x for li in poly.loop_indices]
    if max(us)-min(us)>.8:
     for li in poly.loop_indices:
      if layer.data[li].uv.x<.2:layer.data[li].uv.x+=1
f.original_clothing_builder=p.old_clothes;f.make_clothes=garment


def bind(body):
 oldbind(body)
 for o in f.PARTS:
  bone=None
  if o.name.startswith(('EyeWhite.','Iris.','IrisRim.','Pupil.','EyeGlint.')):bone='eye.'+o.name[-1]
  elif o.name.startswith('Nail.'):bone=o.name[5:]
  elif o.name.startswith('Fang.'):bone='Jaw'
  if bone and bone in b.BONES:
   o.vertex_groups.clear();g=o.vertex_groups.new(name=bone);g.add(list(range(len(o.data.vertices))),1,'REPLACE')
f.bind_all=bind

if __name__=='__main__':f.main()
