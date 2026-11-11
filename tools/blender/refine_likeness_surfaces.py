"""Surface finishing: conforming cloth, sculpted hairline, detailed fibres and facial styling."""
from __future__ import annotations
from pathlib import Path
import sys,math,struct,zlib
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import polish_character_likeness as p
f=p.f;b=f.b;a=f.a
old_body=f.make_anatomy;old_face=f.make_face;old_hair=f.make_hair;old_clothes=f.make_clothes;old_stage=f.make_stage


def cat(a,b,c,d,t):return .5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)

def sweep(name,points,widths,depths=None,material='Hair',sides=20,steps=12,grooves=0.,axis=(1,0,0)):
 centers=f.spline(points,steps);depths=depths or widths;verts=[];uv=[];faces=[];u=Vector(axis)
 for i,c in enumerate(centers):
  tangent=(centers[min(i+1,len(centers)-1)]-centers[max(0,i-1)]).normalized();u-=tangent*u.dot(tangent)
  if u.length<.001:u=tangent.cross(Vector((0,1,0)))
  if u.length<.001:u=tangent.cross(Vector((1,0,0)))
  u.normalize();v=tangent.cross(u).normalized();k=min(len(points)-2,int(i/steps));t=i/steps-k
  w=max(.0001,cat(widths[max(0,k-1)],widths[k],widths[k+1],widths[min(len(widths)-1,k+2)],t));d=max(.0001,cat(depths[max(0,k-1)],depths[k],depths[k+1],depths[min(len(depths)-1,k+2)],t))
  for j in range(sides):
   th=j*2*math.pi/sides;rib=1+grooves*.35*math.cos(th*6)*math.sin(math.pi*i/(len(centers)-1))**.4
   verts.append(tuple(c+u*w*math.cos(th)*rib+v*d*math.sin(th)*rib));uv.append((j/sides,i/(len(centers)-1)))
 for i in range(len(centers)-1):
  for j in range(sides):k=i*sides+j;n=i*sides+(j+1)%sides;faces.append((k,n,n+sides,k+sides))
 for base,rev in [(0,True),((len(centers)-1)*sides,False)]:
  for j in range(1,sides-1):q=(base,base+j,base+j+1);faces.append(tuple(reversed(q)) if rev else q)
 return f.mesh(name,verts,faces,material,uv)
f.sweep=sweep


def body(path):
 obj,v,definition,weights=old_body(path)
 def facewarp(co):
  x,y,z=co
  if z>1.69:
   jaw=f.ss(1.84,1.74,z)*f.ss(1.68,1.73,z)*f.ss(.035,-.055,y)
   x*=1-.16*jaw
   if abs(x)>.10 and 1.80<z<1.92 and y>-.095:
    outer=f.ss(.10,.15,abs(x));x+=math.copysign(.065*outer,x);z+=.032*outer;y-=.055*outer
  return x,y,z
 for q in obj.data.vertices:q.co=facewarp(q.co)
 v=np.array([facewarp(q) for q in v])
 g=obj.vertex_groups.new(name='TemporarySculptRelax')
 for q in obj.data.vertices:
  x,y,z=q.co
  weight=f.ss(1.19,1.30,z)*(1-f.ss(1.61,1.72,z))*f.ss(-.08,-.19,y)*(1-f.ss(.36,.45,abs(x)))
  if weight>.001:g.add([q.index],weight,'REPLACE')
 mod=obj.modifiers.new('SculptedBreastTransitions','SMOOTH');mod.factor=.42;mod.iterations=24;mod.vertex_group=g.name;group_name=g.name;f.apply(obj,mod);obj.vertex_groups.remove(obj.vertex_groups[group_name])
 obj.data.update();f.TREE=BVHTree.FromPolygons([q.co for q in obj.data.vertices],[tuple(q.vertices) for q in obj.data.polygons])
 return obj,v,definition,weights
f.make_anatomy=body


def face_line(name,points,radii,material,depth=.001):
 points3=[(x,0,z) for x,z in points];centers=f.spline(points3,8)
 widths=[]
 for i,q in enumerate(centers):
  q.y=f.front(q.x,q.z,.0012)-depth;k=min(len(points)-2,int(i/8));t=i/8-k;widths.append(max(.00005,cat(radii[max(0,k-1)],radii[k],radii[k+1],radii[min(len(radii)-1,k+2)],t)))
 return sweep(name,[tuple(q) for q in centers],widths,[max(.00015,w*.22) for w in widths],material=material,sides=10,steps=1)
f.face_line=face_line


def face(v,definition):
 old_face(v,definition)
 for o in list(f.PARTS):
  if o.name.startswith('WhiteBrow'):
   f.PARTS.remove(o);bpy.data.objects.remove(o,do_unlink=True)
 for side,s in [('L',1),('R',-1)]:
  d=definition['bones']['eye.'+side];c=Vector(v[definition['joints'][d['head']]].mean(0))
  points=[(c.x+s*dx,0,c.z+dz) for dx,dz in [(-.024,.031),(-.010,.043),(.006,.053),(.027,.054)]]
  o=f.petal_mark('WhiteBrow.'+side,points,[.0001,.0040,.0040,.0001]);o.data.materials.clear();o.data.materials.append(b.MATS['Hair'])
f.make_face=face


def hair():
 old_hair()
 for o in list(f.PARTS):
  if o.name.startswith(('HairScalp','CrownWave')):
   f.PARTS.remove(o);bpy.data.objects.remove(o,do_unlink=True)
 obj=f.BODY;selected=[]
 for face in obj.data.polygons:
  c=face.center
  frontness=f.ss(.04,-.16,c.y)
  threshold=1.78+.157*frontness-.008*math.exp(-(c.x/.035)**2)*frontness
  if c.z>threshold:selected.append(face)
 used=sorted({i for q in selected for i in q.vertices});lookup={old:new for new,old in enumerate(used)}
 vertices=[tuple(obj.data.vertices[i].co+obj.data.vertices[i].normal*.004) for i in used]
 cap=f.mesh('HairScalp',vertices,[[lookup[i] for i in q.vertices] for q in selected],'Hair')
 bm=bmesh.new();bm.from_mesh(cap.data)
 for _ in range(8):
  boundary=[v for v in bm.verts if v.is_boundary];moved={}
  for q in boundary:
   neighbors=[e.other_vert(q) for e in q.link_edges if e.is_boundary]
   if len(neighbors)==2:
    c=q.co*.3+(neighbors[0].co+neighbors[1].co)*.35;hit=f.TREE.find_nearest(c)
    moved[q]=hit[0]+hit[1]*.005 if hit[0] is not None else c
  for q,c in moved.items():q.co=c
 bm.to_mesh(cap.data);bm.free();cap.data.update()
 for s in [-1,1]:
  for j in range(9):
   yy=-.161+j*.029
   z=1.969+.028*math.sin(math.pi*(j+1)/11)
   pts=[(s*.002,yy+.008,z-.008),(s*.026,yy,z+.007),(s*.062,yy+.008,z+.008),(s*.106,yy+.032,z-.028),(s*.135,yy+.05,z-.075)]
   sweep(f'CrownWave.{s}.{j}',pts,[.003,.012,.016,.016,.0001],[.002,.008,.009,.010,.0001],sides=24,steps=12,grooves=.02)
 for o in f.PARTS:
  if o.name.startswith('BackWave'):
   nums=o.name.split('.');j=int(nums[-1]);layer=int(nums[-2]);phase=j*.9+layer*1.3
   for q in o.data.vertices:
    z=q.co.z;t=f.ss(1.90,1.0,z)
    q.co.x+=.027*math.sin((z-1.0)*12+phase)*math.sin(math.pi*t)
    q.co.y+=.018*math.cos((z-1.0)*10+phase)*math.sin(math.pi*t)
 f.CFG['hair_finish']='sculpted parted roots, continuous sweep radii, layered wave fibres'
f.make_hair=hair


def clothes():
 old_clothes()
 for o in list(f.PARTS):
  if o.name.startswith('ChestDrape'):
   f.PARTS.remove(o);bpy.data.objects.remove(o,do_unlink=True)
 obj=f.BODY
 badprefix=('UpperArm','Forearm','Hand','Thumb','Index','Middle','Ring','Little','metacarpal')
 keep=[]
 for poly in obj.data.polygons:
  score=0.
  for vi in poly.vertices:
   score+=sum(g.weight for g in obj.data.vertices[vi].groups if obj.vertex_groups[g.group].name.startswith(badprefix))
  if score/len(poly.vertices)<.35:keep.append(tuple(poly.vertices))
 tree=BVHTree.FromPolygons([q.co for q in obj.data.vertices],keep)
 levels=[1.195,1.245,1.33,1.42,1.51,1.59,1.66,1.725]
 origins=[.03,.12,.18,.18,.17,.12,.06,0.]
 amin=[.1,-.12,.06,.10,.12,.14,.22,.40]
 amax=[.9,1.1,1.38,1.47,1.28,.82,.62,.82]
 for s in [-1,1]:
  verts=[];uv=[];faces=[];nx=32;ny=96
  for i in range(ny+1):
   t=i/ny;z=1.725-(1.725-1.195)*t;cx=float(np.interp(z,levels,origins));lo=float(np.interp(z,levels,amin));hi=float(np.interp(z,levels,amax))
   for j in range(nx+1):
    u=j/nx;ang=lo+(hi-lo)*u;origin=Vector((s*cx,-.025,z));direction=Vector((s*math.sin(ang),-math.cos(ang),0))
    pos,normal,idx,dist=tree.ray_cast(origin,direction,1.)
    if pos is None:
     guess=Vector((s*(.10+.05*(u-.5)),-.08,z));pos,normal,_,_=tree.find_nearest(guess)
    q=pos+normal*.008
    wrinkle=.0018*math.cos(u*math.pi*7+t*3)*math.sin(math.pi*t)**2+.002*math.cos(u*math.pi*11+t*9)*f.ss(.75,1,t)
    q+=normal*wrinkle
    verts.append(tuple(q));uv.append((u,t))
  for i in range(ny):
   for j in range(nx):
    k=i*(nx+1)+j;fc=(k,k+1,k+nx+2,k+nx+1);faces.append(fc if s==1 else tuple(reversed(fc)))
  o=f.mesh('ChestDrape.'+str(s),verts,faces,'Cloth',uv)
  original=np.array([tuple(q.co) for q in o.data.vertices]);vertices=original.reshape((ny+1,nx+1,3)).copy()
  for _ in range(4):
   n=vertices.copy();n[1:-1,1:-1]=vertices[1:-1,1:-1]*.4+.15*(vertices[:-2,1:-1]+vertices[2:,1:-1]+vertices[1:-1,:-2]+vertices[1:-1,2:]);vertices=n
  for q,new in zip(o.data.vertices,vertices.reshape((-1,3))):
   point=Vector(new);pos,nor,_,_=tree.find_nearest(point)
   if pos is not None and (point-pos).dot(nor)<.004:point=pos+nor*.004
   q.co=point
  solid=o.modifiers.new('SewnFabricThickness','SOLIDIFY');solid.thickness=.0025;solid.offset=0;f.apply(o,solid)
f.make_clothes=clothes


def png(path,pixels):
 data=np.clip(pixels*255+.5,0,255).astype(np.uint8);h,w,_=data.shape
 def chunk(kind,body):return struct.pack('>I',len(body))+kind+body+struct.pack('>I',zlib.crc32(kind+body)&0xffffffff)
 raw=b''.join(b'\0'+row.tobytes() for row in data)
 path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw,6))+chunk(b'IEND',b''))


def textures():
 out=Path(sys.argv[sys.argv.index('--out')+1]).resolve()/'textures';out.mkdir(exist_ok=True,parents=True)
 u=np.linspace(0,1,1024)[None,:];t=np.linspace(0,1,512)[:,None]
 wave=.007*np.cos(2*math.pi*28*u+.14*np.sin(t*7))+.004*np.cos(2*math.pi*85*u+.3*np.cos(t*9))
 shade=.84+.14*(1-np.exp(-t*6))+wave
 color=shade[:,:,None]*np.array([.88,.88,.92])[None,None,:]
 png(out/'hair-fibres.png',color)
 nx=.035*np.sin(2*math.pi*28*u+.14*np.sin(t*7));ny=np.zeros_like(nx);nz=np.sqrt(1-nx*nx)
 png(out/'hair-normal.png',np.stack([nx,ny,nz],axis=2)*.5+.5)
 material=b.MATS['Hair'];nodes=material.node_tree.nodes;links=material.node_tree.links;principled=nodes.get('Principled BSDF')
 tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(out/'hair-fibres.png'));tex.image.pack();links.new(tex.outputs['Color'],principled.inputs['Base Color'])
 norm=nodes.new('ShaderNodeTexImage');norm.image=bpy.data.images.load(str(out/'hair-normal.png'));norm.image.colorspace_settings.name='Non-Color';norm.image.pack();nm=nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.30;links.new(norm.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],principled.inputs['Normal'])
 u=np.linspace(0,1,1024)[None,:];v=np.linspace(0,1,1024)[:,None]
 nx=np.sin(u*2*math.pi*140)*np.ones_like(v)*.12;ny=np.sin(v*2*math.pi*180)*np.ones_like(u)*.12;nz=np.sqrt(1-nx*nx-ny*ny)
 png(out/'cloth-weave-normal.png',np.stack([nx,ny,nz],axis=2)*.5+.5)
 material=b.MATS['Cloth'];nodes=material.node_tree.nodes;links=material.node_tree.links
 tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(out/'cloth-weave-normal.png'));tex.image.colorspace_settings.name='Non-Color';tex.image.pack();nm=nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.13;links.new(tex.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],nodes.get('Principled BSDF').inputs['Normal'])


def stage():
 textures();cam=old_stage();bpy.context.scene.cycles.samples=24
 return cam
f.make_stage=stage
if __name__=='__main__':f.main()
