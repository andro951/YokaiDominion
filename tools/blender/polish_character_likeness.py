"""Reference-led finishing corrections over the saved likeness construction.
These replace, rather than decorate, the preliminary eye, hair and cloth surfaces.
"""
from __future__ import annotations
from pathlib import Path
import sys, math
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import finish_character_likeness as f
b=f.b;a=f.a
f.CFG.update({'bust_round':0.,'eye_scale':1.25,'hair':'dad9e3','iris':'7e89aa','bust_center_z':1.487,'bust_depth':.288,'render_samples':32})
old_load=a.load_data
old_body=f.make_anatomy
old_stage=f.make_stage

def load(path):
 for s in ['l','r']:
  a.TARGETS[f'eyes/{s}-eye-height2-decr.target']=.90
  a.TARGETS[f'eyes/{s}-eye-height1-decr.target']=.25
  a.TARGETS[f'eyes/{s}-eye-height3-decr.target']=.20
 a.TARGETS['mouth/mouth-angles-up.target']=.22
 return old_load(path)
a.load_data=load

def warp_point(point):
 x,y,z=point;oldz=z
 if 1.12<z<1.68 and y<-.075 and abs(x)<.435:
  lift=.108*f.ss(-.075,-.20,y)*math.exp(-((z-1.385)/.225)**6)
  z+=lift
  cx=.195 if x>0 else -.195
  q=((x-cx)/.240)**2+((z-1.487)/.245)**2
  if q<.985:
   front=-.170-.288*math.sqrt(max(0,1-q))
   mask=f.ss(-.10,-.20,y)*f.ss(.985,.55,q)*.82
   y=y*(1-mask)+front*mask
 return x,y,z

def body(path):
 obj,v,definition,weights=old_body(path)
 for p in obj.data.vertices:p.co=warp_point(p.co)
 v=np.array([warp_point(p) for p in v]);obj.data.update()
 f.TREE=BVHTree.FromPolygons([p.co for p in obj.data.vertices],[tuple(p.vertices) for p in obj.data.polygons])
 return obj,v,definition,weights
f.make_anatomy=body

def face(v,definition):
 for side,s in [('L',1),('R',-1)]:
  eb=definition['bones']['eye.'+side];c=Vector(v[definition['joints'][eb['head']]].mean(0))
  # The sclera is behind the eyelids rather than in front of the lower lid.
  c.y+=.0035
  f.sphere('EyeWhite.'+side,c,(.0270,.0220,.0220),'EyeWhite')
  c.y-=.021
  f.sphere('IrisRim.'+side,c,(.0135,.002,.0140),'IrisRim')
  f.sphere('Iris.'+side,c+Vector((0,-.0015,0)),(.0114,.0018,.0122),'Iris')
  f.sphere('Pupil.'+side,c+Vector((0,-.003,0)),(.0051,.001,.0076),'Pupil')
  f.sphere('EyeGlint.'+side,c+Vector((-.0033,-.0042,.0045)),(.0023,.0007,.0024),'Fang')
  x,z=c.x,c.z
  f.face_line('UpperEyeliner.'+side,[(x+s*dx,z+dz) for dx,dz in [(-.028,.001),(-.012,.008),(.010,.010),(.027,.010),(.039,.017)]],[.0005,.0017,.0024,.0028,.0001],'Ink')
  f.face_line('LowerEyeliner.'+side,[(x+s*dx,z+dz) for dx,dz in [(-.027,.001),(-.010,-.005),(.012,-.003),(.029,.010)]],[.0002,.00045,.00065,.0009],'Ink')
  for j in range(3):
   xx=x+s*(.024+.0035*j);zz=z+.011+.001*j
   f.face_line('Lash.'+side+str(j),[(xx,zz),(xx+s*(.008+.0015*j),zz+.005+.001*j)],[.0012,.00005],'Ink')
  f.face_line('WhiteBrow.'+side,[(x+s*dx,z+dz) for dx,dz in [(-.030,.032),(-.012,.046),(.011,.045),(.035,.034)]],[.0004,.0047,.0040,.0001],'Hair')
 for s in [-1,1]:
  x=s*.026;z=1.753+.001*(s>0);y=f.front(x,z,.004)
  f.sweep('Fang.'+str(s),[(x,y,z+.004),(x,y-.001,z-.003),(x+s*.0005,y,z-.006)],[.0030,.0017,.0001],material='Fang',sides=12,steps=6)
f.make_face=face

def hair():
 # Close-fitting scalp; opposite winding to the original open shell.
 verts=[];faces=[];uv=[];n=80;m=24
 for j in range(m+1):
  for k in range(n):
   phi=2*math.pi*k/n;frontness=max(0,-math.sin(phi))
   angle=(2.12-1.10*frontness)*(j/m)
   verts.append((.123*math.sin(angle)*math.cos(phi),-.066+.136*math.sin(angle)*math.sin(phi),1.858+.151*math.cos(angle)))
   uv.append((k/n,j/m))
 for j in range(m):
  for k in range(n):
   p=j*n+k;q=j*n+(k+1)%n;faces.append((q,p,p+n,q+n))
 f.mesh('HairScalp',verts,faces,'Hair',uv)
 for s in [-1,1]:
  # Roots are buried, with no visible circular root caps or floating crown wedges.
  for j in range(8):
   yy=-.151+j*.031
   pts=[(s*.001,yy+.014,1.975-j*.003),(s*.029,yy,2.005-j*.003),(s*.072,yy-.004,1.994-j*.008),(s*.113,yy+.012,1.958-j*.018),(s*.139,yy+.025,1.889-j*.030)]
   f.sweep(f'CrownWave.{s}.{j}',pts,[.003,.014,.022,.024,.0001],[.003,.010,.015,.017,.0001],grooves=.045,sides=24,steps=12)
  paths=[
   ([(s*.055,-.135,1.989),(s*.092,-.167,1.952),(s*.114,-.185,1.868),(s*.117,-.175,1.787),(s*.139,-.149,1.742),(s*.166,-.119,1.752)],[.003,.022,.027,.024,.016,.0002]),
   ([(s*.092,-.084,1.955),(s*.142,-.109,1.888),(s*.157,-.113,1.783),(s*.188,-.073,1.716),(s*.229,-.025,1.700),(s*.258,.008,1.718)],[.003,.021,.031,.034,.019,.0002]),
   ([(s*.105,-.010,1.911),(s*.163,.005,1.803),(s*.184,.020,1.709),(s*.235,.053,1.648),(s*.288,.085,1.647),(s*.310,.09,1.665)],[.003,.022,.034,.037,.022,.0002]),
  ]
  for j,(pts,w) in enumerate(paths):f.sweep(f'FaceWave.{s}.{j}',pts,w,[r*.48 for r in w],grooves=.050,sides=24,steps=12)
 # Alternating waves, with tips that fan outward at different heights.
 for layer in range(3):
  count=[11,9,7][layer]
  for j in range(count):
   u=2*j/(count-1)-1;sgn=1 if u>=0 else -1
   end=.96+.15*abs(u)+.15*layer;z=1.97-.075*layer
   phase=math.sin(j*1.7+layer)
   pts=[(u*.078,.040+.032*layer,z),(u*.141,.152+.025*layer,z-.15),(u*.223+.012*phase,.205+.033*layer,z-.34),(u*.286-.014*phase,.211+.038*layer,end+.24),(u*.315+.019*phase,.19+.035*layer,end+.10),(u*.352+sgn*.033,.16+.03*layer,end+.035),(u*.361+sgn*.055,.147+.025*layer,end+.060)]
   w=.032+.006*layer
   f.sweep(f'BackWave.{layer}.{j}',pts,[.004,w,w*1.15,w*1.2,w,.017,.0002],[.003,.020,.027,.025,.020,.010,.0002],grooves=.07,sides=24,steps=10)
f.make_hair=hair

def petal(name,points,widths):
 centers=f.spline(points,10);verts=[];faces=[];n=8
 for i,p in enumerate(centers):
  k=min(len(points)-2,int(i/10));t=i/10-k;w=widths[k]*(1-t)+widths[k+1]*t
  d=centers[min(i+1,len(centers)-1)]-centers[max(0,i-1)];normal=Vector((-d.z,0,d.x)).normalized()
  for j in range(n+1):
   q=p+normal*(w*(2*j/n-1));q.y=f.front(q.x,q.z,.0011);verts.append(tuple(q))
 for i in range(len(centers)-1):
  for j in range(n):p=i*(n+1)+j;faces.append((p,p+1,p+n+2,p+n+1))
 return f.mesh(name,verts,faces,'Markings')
f.petal_mark=petal

old_clothes=f.make_clothes

def clothes():
 # Keep the sash/skirt construction, replace the entire breast ribbon surface.
 before=len(f.PARTS);old_clothes()
 for o in list(f.PARTS[before:]):
  if o.name.startswith('ChestDrape'):
   f.PARTS.remove(o);bpy.data.objects.remove(o,do_unlink=True)
 for s in [-1,1]:
  verts=[];faces=[];uv=[];nr=92;nc=32
  for i in range(nr+1):
   t=i/nr
   for j in range(nc+1):
    u=j/nc
    if t<.20:
     k=f.ss(0,.20,t);beta=1.13
     angle=.12+1.28*u;xx=.195+.247*math.sin(angle)*math.cos(beta);yy=-.170-.296*math.cos(angle)*math.cos(beta);zz=1.487+.247*math.sin(beta)
     x=(.100+.048*(u-.5))*(1-k)+xx*k;y=(-.080)*(1-k)+yy*k;z=1.729*(1-k)+zz*k
    elif t<.88:
     k=(t-.20)/.68;beta=1.13-2.43*k
     angle=.12+1.28*u
     x=.195+.247*math.sin(angle)*math.cos(beta);y=-.170-.296*math.cos(angle)*math.cos(beta);z=1.487+.247*math.sin(beta)
    else:
     k=f.ss(.88,1,t);beta=-1.30;angle=.12+1.28*u
     xx=.195+.247*math.sin(angle)*math.cos(beta);yy=-.170-.296*math.cos(angle)*math.cos(beta);zz=1.487+.247*math.sin(beta)
     x=xx*(1-k)+(.105+.10*(u-.5))*k;y=yy*(1-k)+(-.190)*k;z=zz*(1-k)+1.211*k
    x*=s
    sy=f.front(x,z,.006,fallback=y)
    if abs(sy-y)<.10:y=min(y,sy)
    fold=.0018*math.cos(u*math.pi*6+3*t)*math.sin(math.pi*t)**1.3
    fold+=.0028*math.cos(u*math.pi*10+t*8)*f.ss(.67,1,t)
    y-=fold
    verts.append((x,y,z));uv.append((u,t))
  for i in range(nr):
   for j in range(nc):
    p=i*(nc+1)+j;face=(p,p+1,p+nc+2,p+nc+1);faces.append(face if s==1 else tuple(reversed(face)))
  o=f.mesh('ChestDrape.'+str(s),verts,faces,'Cloth',uv)
  sol=o.modifiers.new('SewnFabricThickness','SOLIDIFY');sol.thickness=.0025;sol.offset=0;f.apply(o,sol)
f.make_clothes=clothes

def stage():
 cam=old_stage();bpy.context.scene.view_settings.exposure=-.50
 return cam
f.make_stage=stage

if __name__=='__main__':f.main()
