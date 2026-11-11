"""Tailored contours and final feature placement, evaluated on the actual sculpt."""
from pathlib import Path
import sys,math
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import refine_likeness_surfaces as r
f=r.f;b=f.b;a=f.a;p=r.p
oldhair=f.make_hair;oldclothes=f.make_clothes;oldhorns=f.make_horns_tail;oldface_line=f.face_line

def load(path):
 for s in ['l','r']:
  a.TARGETS[f'eyes/{s}-eye-height2-decr.target']=.55
  a.TARGETS[f'eyes/{s}-eye-height1-decr.target']=.12
  a.TARGETS[f'eyes/{s}-eye-height3-decr.target']=.12
  a.TARGETS[f'cheek/{s}-cheek-bones-incr.target']=.25
  a.TARGETS[f'cheek/{s}-cheek-inner-decr.target']=.15
 a.TARGETS['mouth/mouth-angles-up.target']=.20
 a.TARGETS['mouth/mouth-lowerlip-height-decr.target']=.60
 a.TARGETS['mouth/mouth-lowerlip-volume-decr.target']=.38
 a.TARGETS['nose/nose-nostrils-angle-down.target']=.45
 a.TARGETS['nose/nose-point-down.target']=.15
 a.TARGETS['stomach/stomach-tone-incr.target']=.55
 return p.old_load(path)
a.load_data=load


def face_line(name,points,radii,material,depth=.001):
 if name.startswith('UpperEyeliner'):radii=[w*1.40 for w in radii]
 return oldface_line(name,points,radii,material,depth)
f.face_line=face_line


def hair():
 oldhair()
 for o in list(f.PARTS):
  if o.name.startswith('CrownWave'):
   f.PARTS.remove(o);bpy.data.objects.remove(o,do_unlink=True)
 for s in [-1,1]:
  for j in range(8):
   if j==0:
    pts=[(s*.001,-.205,1.935),(s*.028,-.203,1.953),(s*.063,-.184,1.978),(s*.108,-.144,1.972),(s*.132,-.099,1.925)]
   else:
    yy=-.163+(j-1)*.033;z=1.981+.015*math.sin(math.pi*j/9)
    pts=[(s*.001,yy,z-.006),(s*.028,yy+.001,z+.004),(s*.068,yy+.012,z+.001),(s*.109,yy+.040,z-.034),(s*.138,yy+.060,z-.088)]
   fitted=[]
   for point in pts:
    co=Vector(point);pos,n,_,_=f.TREE.find_nearest(co)
    if pos is not None and (co-pos).length<.08:co=pos+n*.011
    fitted.append(tuple(co))
   f.sweep(f'CrownWave.{s}.{j}',fitted,[.001,.015,.021,.022,.0001],[.001,.008,.010,.011,.0001],sides=24,steps=12)
 cap=bpy.data.objects['HairScalp'];uv=cap.data.uv_layers.new(name='UVMap')
 for face in cap.data.polygons:
  for li in face.loop_indices:
   q=cap.data.vertices[cap.data.loops[li].vertex_index].co
   uv.data[li].uv=((math.atan2(q.y+.06,q.x)/(2*math.pi))%1,f.ss(1.78,2.0,q.z))
 f.mat('BrowHair','e4e3ea',.6)
 for o in f.PARTS:
  if o.name.startswith('WhiteBrow'):
   o.data.materials.clear();o.data.materials.append(b.MATS['BrowHair'])
f.make_hair=hair


def horns_tail():
 tail=oldhorns()
 for o in f.PARTS:
  if o.name.startswith('Horn.'):
   for q in o.data.vertices:
    amount=1-f.ss(1.94,2.13,q.co.z);q.co.y-=.056*amount;q.co.z-=.017*amount
 b.MATS['Horn'].node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.57
 return tail
f.make_horns_tail=horns_tail


def clothes():
 oldclothes()
 for o in list(f.PARTS):
  if o.name.startswith(('ChestDrape','BackStrap')):
   f.PARTS.remove(o);bpy.data.objects.remove(o,do_unlink=True)
 obj=f.BODY;bad=('UpperArm','Forearm','Hand','Thumb','Index','Middle','Ring','Little','metacarpal');keep=[]
 for poly in obj.data.polygons:
  score=sum(sum(g.weight for g in obj.data.vertices[vi].groups if obj.vertex_groups[g.group].name.startswith(bad)) for vi in poly.vertices)/len(poly.vertices)
  if score<.15:keep.append(tuple(poly.vertices))
 tree=BVHTree.FromPolygons([v.co for v in obj.data.vertices],keep)
 zs=np.linspace(1.715,1.195,105);xs=np.linspace(0,.455,257);field=np.full((len(zs),len(xs)),np.nan)
 for i,z in enumerate(zs):
  for j,x in enumerate(xs):
   pos,n,_,_=tree.ray_cast(Vector((x,-2,z)),Vector((0,1,0)),3.)
   if pos is not None and pos.y<.13:field[i,j]=pos.y
  valid=np.flatnonzero(np.isfinite(field[i]))
  if len(valid)<2:raise ValueError(f'No usable torso surface at {z}')
  last=valid[-1];field[i,:last+1]=np.interp(np.arange(last+1),valid,field[i,valid]);field[i,last+1:]=field[i,last]
 widths=[]
 for z in zs:
  hits=[]
  for x in xs:
   hit=tree.ray_cast(Vector((x,-2,z)),Vector((0,1,0)),3.)
   if hit[0] is not None and hit[0].y<.13:hits.append(x)
  widths.append(max(hits))
 widths=np.array(widths)
 for _ in range(3):widths[1:-1]=.5*widths[1:-1]+.25*(widths[:-2]+widths[2:])
 levels=[1.195,1.24,1.31,1.40,1.49,1.58,1.65,1.715]
 left=[.24,.29,.49,.59,.61,.54,.48,.53]
 right=[.77,.91,.98,.98,.96,.79,.66,.82]
 for s in [-1,1]:
  verts=[];faces=[];uv=[];nx=40
  for i,z in enumerate(zs):
   t=i/(len(zs)-1);lo=float(np.interp(z,levels,left));hi=float(np.interp(z,levels,right))
   for j in range(nx+1):
    u=j/nx;x=widths[i]*(lo+(hi-lo)*u)
    y=float(np.interp(x,xs,field[i]))-.009
    y-=.0014*math.sin(6*math.pi*u+t*4)*math.sin(math.pi*t)**2
    y-=.0022*math.cos(10*math.pi*u+t*6)*f.ss(.7,1,t)
    verts.append((s*x,y,float(z)));uv.append((u,t))
  for i in range(len(zs)-1):
   for j in range(nx):
    k=i*(nx+1)+j;fc=(k,k+1,k+nx+2,k+nx+1);faces.append(fc if s>0 else tuple(reversed(fc)))
  o=f.mesh('ChestDrape.'+str(s),verts,faces,'Cloth',uv)
  grid=np.array(verts).reshape((len(zs),nx+1,3))
  for _ in range(10):
   new=grid.copy();new[1:-1]=grid[1:-1]*.5+(grid[:-2]+grid[2:])*.25;grid=new
  for q,co in zip(o.data.vertices,grid.reshape((-1,3))):
   hit=tree.ray_cast(Vector((abs(co[0]),-2,co[2])),Vector((0,1,0)),3.)
   if hit[0] is not None:co[1]=min(co[1],hit[0].y-.005)
   q.co=co
  solid=o.modifiers.new('FinishedFabricThickness','SOLIDIFY');solid.thickness=.0025;solid.offset=0;f.apply(o,solid)
  start=Vector(verts[nx//2]);points=[tuple(start),(s*.075,-.030,1.724),(s*.082,.055,1.68),(s*.10,.080,1.52),(s*.11,.100,1.30),(s*.11,.136,1.215)]
  f.sweep(f'BackStrap.{s}',points,[.014,.017,.021,.026,.032,.035],[.0018]*6,material='Cloth',sides=12,steps=12)
 for o in f.PARTS:
  if not o.data.uv_layers:continue
  layer=o.data.uv_layers.active
  for poly in o.data.polygons:
   us=[layer.data[li].uv.x for li in poly.loop_indices]
   if max(us)-min(us)>.8:
    for li in poly.loop_indices:
     if layer.data[li].uv.x<.2:layer.data[li].uv.x+=1
f.make_clothes=clothes

if __name__=='__main__':f.main()
