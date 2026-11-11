"""Character01 likeness art pass. Actual editable geometry; no image planes.
Reuses the pinned CC0 anatomical topology and inherited weights from milestone 002.
Blender 4.5.3: --background --python-exit-code 1 --python this.py --
  --base-data path/to/makehuman/data --out path [--views portrait,front,three-quarter,side,back]
"""
from __future__ import annotations
import argparse, hashlib, json, math, sys
from pathlib import Path
import bpy, bmesh, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_character as b
import build_character_anatomy as a

CFG={
 'skin':'777a90','mark':'393d55','hair':'e7e6ec','horn':'252532',
 'cloth':'d8d0c0','sash':'25252d','iris':'8f9cbd',
 'eye_scale':1.5,'nose_scale':.55,'jaw_narrow':.3,'bust_round':.80,
 'bust_depth':.285,'bust_width':.238,'bust_height':.241,
 'body_subdivision':1,'render_samples':40,
}
PARTS=b.PARTS
BODY=None
TREE=None


def ss(lo,hi,x):
 t=max(0.,min(1.,(x-lo)/(hi-lo)));return t*t*(3.-2.*t)


def mat(name,hexcode,rough=.5,subsurface=0.):
 m=b.material(name,hexcode,rough);p=m.node_tree.nodes.get('Principled BSDF')
 p.inputs['Specular IOR Level'].default_value=.30
 p.inputs['Subsurface Weight'].default_value=subsurface
 if subsurface:p.inputs['Subsurface Radius'].default_value=(.7,.38,.25)
 return m


def mesh(name,vertices,faces,material,uv=None):
 o=b.mesh_object(name,vertices,faces,material)
 if uv:
  layer=o.data.uv_layers.new(name='UVMap')
  for poly in o.data.polygons:
   for li in poly.loop_indices:layer.data[li].uv=uv[o.data.loops[li].vertex_index]
 return o


def apply(o,mod):
 bpy.context.view_layer.objects.active=o
 bpy.ops.object.modifier_apply(modifier=mod.name)


def subdiv(o,level=1):
 m=o.modifiers.new('AuthoredSurfaceRefinement','SUBSURF');m.levels=level;apply(o,m)


def sphere(name,center,scale,material):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=28,location=center)
 o=bpy.context.object;o.name=name;o.scale=scale
 bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 o.data.materials.append(b.MATS[material]);PARTS.append(o)
 for p in o.data.polygons:p.use_smooth=True
 return o


def spline(points,samples=10):
 pts=[Vector(p) for p in points];out=[]
 for i in range(len(pts)-1):
  p0,p1,p2,p3=pts[max(0,i-1)],pts[i],pts[i+1],pts[min(i+2,len(pts)-1)]
  for j in range(samples):
   t=j/samples
   out.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
 out.append(pts[-1]);return out


def sweep(name,points,widths,depths=None,material='Hair',sides=16,steps=10,grooves=0.,axis=(1,0,0)):
 centers=spline(points,steps);depths=depths or widths
 vertices=[];uv=[];faces=[];u=Vector(axis)
 for i,p in enumerate(centers):
  tangent=(centers[min(i+1,len(centers)-1)]-centers[max(i-1,0)]).normalized()
  u=u-tangent*u.dot(tangent)
  if u.length<.001:u=tangent.cross(Vector((0,1,0)))
  if u.length<.001:u=tangent.cross(Vector((1,0,0)))
  u.normalize();v=tangent.cross(u).normalized()
  t=i/(len(centers)-1);k=min(len(points)-2,int(i/steps));f=(i/steps)-k
  w=max(.0001,widths[k]*(1-f)+widths[k+1]*f);d=max(.0001,depths[k]*(1-f)+depths[k+1]*f)
  for j in range(sides):
   theta=2*math.pi*j/sides
   rib=1+grooves*math.cos(theta*6+.15*math.sin(t*7))*math.sin(math.pi*t)**.3
   vertices.append(tuple(p+u*(w*math.cos(theta)*rib)+v*(d*math.sin(theta)*rib)))
   uv.append((j/sides,t))
 for i in range(len(centers)-1):
  for j in range(sides):
   k=i*sides+j;n=i*sides+(j+1)%sides;faces.append((k,n,n+sides,k+sides))
 for base,reverse in [(0,True),((len(centers)-1)*sides,False)]:
  for j in range(1,sides-1):
   f=(base,base+j,base+j+1);faces.append(tuple(reversed(f)) if reverse else f)
 return mesh(name,vertices,faces,material,uv)


def front(x,z,offset=0.,fallback=-.15):
 hit=TREE.ray_cast(Vector((x,-2,z)),Vector((0,1,0)),3.)
 return (hit[0].y-offset) if hit[0] is not None else fallback-offset


def face_line(name,points,radii,material,depth=.001):
 ps=[(x,front(x,z,.0015)-depth,z) for x,z in points]
 return sweep(name,ps,radii,material=material,sides=10,steps=6)


def make_materials():
 mat('Skin',CFG['skin'],.50,.10);mat('PlainSkin',CFG['skin'],.50,.10)
 mat('Markings',CFG['mark'],.55);mat('Hair',CFG['hair'],.43)
 mat('HairShadow','b7b4c4',.54);mat('Horn',CFG['horn'],.42)
 mat('Cloth',CFG['cloth'],.84);mat('Sash',CFG['sash'],.72)
 mat('Ink','171a27',.55);mat('EyeWhite','c9cdd7',.22)
 mat('Iris',CFG['iris'],.22);mat('IrisRim','3f4866',.26)
 mat('Pupil','10131f',.17);mat('Fang','dddacf',.28)
 mat('Lip','626478',.47);mat('Nail','343448',.33)
 mat('Stage','30313b',.78)
 b.MATS['Hair'].node_tree.nodes.get('Principled BSDF').inputs['Anisotropic'].default_value=.35
 b.MATS['Cloth'].node_tree.nodes.get('Principled BSDF').inputs['Sheen Weight'].default_value=.24


def make_anatomy(basepath):
 global BODY,TREE
 a.TARGETS={
  'macrodetails/caucasian-female-young.target':.35,
  'macrodetails/asian-female-young.target':.65,
  'macrodetails/universal-female-young-maxmuscle-averageweight.target':1.,
  'breast/female-young-maxmuscle-averageweight-maxcup-maxfirmness.target':2.25,
  'breast/breast-point-decr.target':.9,
  'chin/chin-width-decr.target':CFG['jaw_narrow'],
  'chin/chin-triangle.target':.28,
  'chin/chin-height-decr.target':.12,
  'nose/nose-scale-horiz-decr.target':CFG['nose_scale'],
  'nose/nose-scale-depth-decr.target':.3,
  'nose/nose-nostrils-width-decr.target':.5,
  'nose/nose-flaring-decr.target':.5,
  'mouth/mouth-angles-up.target':.55,
  'mouth/mouth-scale-horiz-incr.target':.16,
  'mouth/mouth-upperlip-height-decr.target':.35,
  'mouth/mouth-lowerlip-height-decr.target':.2,
  'mouth/mouth-scale-depth-decr.target':.25,
  'buttocks/buttocks-volume-incr.target':.20,
  'stomach/stomach-muscular-incr.target':.35,
 }
 # Only load existing, explicit adult graphical morphs.
 a.TARGETS={k:w for k,w in a.TARGETS.items() if (basepath/'targets'/k).is_file()}
 for s in ['l','r']:
  a.TARGETS.update({
   f'eyes/{s}-eye-scale-incr.target':CFG['eye_scale'],
   f'eyes/{s}-eye-height2-decr.target':.35,
   f'eyes/{s}-eye-corner2-up.target':.50,
   f'eyes/{s}-eye-bag-decr.target':.50,
   f'ears/{s}-ear-shape-pointed.target':1.45,
   f'ears/{s}-ear-scale-incr.target':.25,
   f'ears/{s}-ear-lobe-decr.target':.6,
   f'armslegs/{s}-upperarm-muscle-incr.target':.6,
   f'armslegs/{s}-upperarm-shoulder-muscle-incr.target':.5,
   f'armslegs/{s}-lowerarm-muscle-incr.target':.40,
   f'armslegs/{s}-upperleg-muscle-incr.target':.45,
   f'armslegs/{s}-lowerleg-muscle-incr.target':.30,
  })
 v,used,faces,uv,faceuv,definition,weights,groups=a.load_data(basepath)
 v=a.shape_data(v,definition,weights)
 # Preserve the exaggerated hourglass; no normalization to the secondary sheet.
 for i in used:
  x,y,z=v[i];ax=abs(x)
  hip=math.exp(-((z-.93)/.16)**4)*ss(.10,.25,ax)*(1-ss(.40,.49,ax))
  v[i,0]*=1+.10*hip
  # Round upper breast surface, remove the pointed preliminary morphology.
  if 1.17<z<1.69 and y<-.10:
   cx=.195 if x>0 else -.195
   q=((x-cx)/CFG['bust_width'])**2+((z-1.432)/CFG['bust_height'])**2
   if q<.99:
    desired=-.17-CFG['bust_depth']*math.sqrt(max(0,1-q))
    mask=ss(-.10,-.19,y)*ss(.99,.60,q)*CFG['bust_round']
    v[i,1]=y*(1-mask)+desired*mask
  # A softly defined abdominal wall, not individual spheres attached to the skin.
  if 1.17<z<1.39 and y<-.08 and ax<.14:
   ridge=math.exp(-((ax-.050)/.033)**2)*(.004+.003*math.cos((z-1.23)*80))
   v[i,1]-=ridge*ss(-.08,-.13,y)
 body=a.create_body(v,used,faces,uv,faceuv,weights)
 # The original body's UVs and deformation weights are retained.
 subdiv(body,CFG['body_subdivision'])
 body.data.update();BODY=body
 TREE=BVHTree.FromPolygons([p.co for p in body.data.vertices],[tuple(p.vertices) for p in body.data.polygons])
 # Replace the preliminary sinusoidal tattoo with separate authored leaf motifs.
 if body.data.color_attributes.get('SkinPalette'):
  col=body.data.color_attributes['SkinPalette'];skin=b.MATS['Skin'].diffuse_color
  for d in col.data:d.color=skin
 return body,v,definition,weights


def make_face(v,definition):
 for side,s in [('L',1),('R',-1)]:
  eb=definition['bones']['eye.'+side];c=Vector(v[definition['joints'][eb['head']]].mean(0))
  # Sized to the enlarged sculpted socket, with a dark limbal ring and small catchlight.
  sphere('EyeWhite.'+side,c,(.029,.026,.025),'EyeWhite')
  c.y-=.0245
  sphere('IrisRim.'+side,c,(.0160,.003,.0162),'IrisRim')
  sphere('Iris.'+side,c+Vector((0,-.002,0)),(.0135,.0025,.0142),'Iris')
  sphere('Pupil.'+side,c+Vector((0,-.004,0)),(.0063,.0015,.0095),'Pupil')
  sphere('EyeGlint.'+side,c+Vector((-.004,-.0058,.006)),(.0031,.001,.0034),'Fang')
  # Eyeliner follows the sculpted face, not a floating billboard.
  x=c.x;z=c.z
  ps=[(x+s*dx,z+dz) for dx,dz in [(-.028,.003),(-.017,.012),(.005,.013),(.025,.008),(.038,.016)]]
  face_line('UpperEyeliner.'+side,ps,[.0007,.0021,.0032,.0033,.0001],'Ink')
  face_line('LowerEyeliner.'+side,[(x+s*dx,z+dz) for dx,dz in [(-.027,.001),(-.011,-.007),(.012,-.007),(.029,.007)]],[.0003,.0006,.0010,.0012],'Ink')
  for j in range(3):
   xx=x+s*(.020+.004*j);zz=z+.010+.001*j
   face_line('Lash.'+side+str(j),[(xx,zz),(xx+s*(.010+.002*j),zz+.007+.002*j)],[.0014,.00005],'Ink')
  face_line('WhiteBrow.'+side,[(x+s*dx,z+dz) for dx,dz in [(-.030,.032),(-.012,.046),(.011,.045),(.035,.034)]],[.0004,.0047,.0040,.0001],'Hair')
  # Small fangs and a controlled, slight smirk.
 for s in [-1,1]:
  z=1.753+.004*(s>0);x=s*.026;y=front(x,z,.003)
  sweep('Fang.'+str(s),[(x,y,z+.002),(x+s*.0005,y-.001,z-.005),(x+s*.001,y+.0005,z-.009)],[.0037,.0022,.0001],material='Fang',sides=12,steps=5)
 face_line('MouthCrease',[(-.036,1.755),(-.018,1.751),(0,1.749),(.020,1.753),(.038,1.762)],[.0003,.0011,.001,.0012,.0002],'Ink',.0005)


def make_hair():
 # Scalp shell, with a centre part and no exposed white spherical cap.
 verts=[];faces=[];uv=[];n=64;m=18
 for j in range(m+1):
  for k in range(n):
   phi=2*math.pi*k/n;frontness=max(0,-math.sin(phi));angle=(2.04-.99*frontness)*(j/m)
   x=.122*math.sin(angle)*math.cos(phi);y=-.065+.131*math.sin(angle)*math.sin(phi);z=1.860+.150*math.cos(angle)
   verts.append((x,y,z));uv.append((k/n,j/m))
 for j in range(m):
  for k in range(n):
   p=j*n+k;q=j*n+(k+1)%n;faces.append((p,q,q+n,p+n))
 cap=mesh('HairScalp',verts,faces,'HairShadow',uv)
 # Layered swept roots form a readable centre part.
 for s in [-1,1]:
  for j in range(6):
   f=j/5
   points=[(s*.004,-.16+.024*j,1.983-.009*j),(s*.052,-.166+.022*j,2.009-.005*j),(s*.110,-.124+.018*j,1.983-.016*j),(s*(.139+.007*f),-.064+.025*j,1.918-.047*j)]
   sweep('CrownWave.%s.%s'%(s,j),points,[.016,.024,.026,.013],[.010,.017,.019,.007],grooves=.055,steps=10,sides=18)
  # Principal locks framing the cheek and jaw. Separated ends flare away from the face.
  paths=[
   ([(s*.077,-.152,1.970),(s*.116,-.162,1.923),(s*.121,-.172,1.830),(s*.127,-.161,1.754),(s*.170,-.127,1.728)], [.025,.032,.027,.021,.0005]),
   ([(s*.110,-.104,1.953),(s*.153,-.106,1.868),(s*.163,-.109,1.762),(s*.206,-.075,1.708),(s*.254,-.024,1.731)], [.022,.033,.040,.030,.0005]),
   ([(s*.116,-.050,1.900),(s*.175,-.036,1.805),(s*.187,-.020,1.704),(s*.256,.015,1.650),(s*.309,.045,1.673)], [.021,.035,.043,.035,.0005]),
   ([(s*.125,.005,1.861),(s*.194,.044,1.729),(s*.235,.074,1.613),(s*.322,.099,1.577),(s*.352,.102,1.601)], [.020,.041,.047,.035,.0004]),
  ]
  for j,(points,w) in enumerate(paths):sweep(f'FaceWave.{s}.{j}',points,w,[q*.43 for q in w],grooves=.07,sides=20,steps=12)
 # Back falls in individual thick, wavy locks, with layered outward curls.
 for layer in range(3):
  count=[9,9,7][layer]
  for j in range(count):
   u=2*j/(count-1)-1;sgn=1 if u>=0 else -1
   x=u*(.085+.018*layer);z=1.97-layer*.08
   end=1.00+.14*abs(u)+layer*.11
   points=[(x,.035+.035*layer,z),(u*.155,.15+.034*layer,z-.17),(u*.255+.017*math.sin(j),.19+.040*layer,z-.37),(u*.315-.027*math.sin(j),.19+.038*layer,end+.18),(u*.335+sgn*.040,.16+.04*layer,end+.065),(u*.325+sgn*.070,.145+.04*layer,end+.075)]
   width=.040 if layer!=2 else .046
   sweep(f'BackWave.{layer}.{j}',points,[.019,width,width*1.17,width,.021,.0003],[.013,.027,.032,.024,.012,.0002],grooves=.06,sides=18,steps=10)


def make_horns_tail():
 for s in [-1,1]:
  pts=[(s*.074,-.112,1.962),(s*.113,-.100,2.020),(s*.131,-.065,2.094),(s*.113,-.027,2.151),(s*.090,-.012,2.175)]
  sweep(f'Horn.{s}',pts,[.045,.042,.029,.014,.0001],[.039,.037,.026,.013,.0001],material='Horn',sides=24,steps=12,grooves=.025)
 # Tail exits the sacral region, with a dark, broad spade tip as in the illustration.
 tail=[(0,.14,1.03),(0,.28,.95),(.13,.37,.72),(.40,.33,.69),(.62,.23,.93),(.69,.13,1.22)]
 sweep('Tail',tail,[.034,.030,.025,.021,.018,.013],material='Horn',sides=20,steps=12)
 sweep('TailSpade',[(.687,.133,1.19),(.696,.125,1.27),(.727,.12,1.35),(.735,.12,1.42)],[.017,.047,.036,.0001],[.009,.017,.014,.0001],material='Horn',sides=18,steps=10,grooves=.02)
 return tail


def petal_mark(name,points,widths):
 # Flat, precisely edged ink shape projected onto the skin; no thick floating tubes.
 centers=spline(points,8);verts=[];faces=[]
 for i,p in enumerate(centers):
  k=min(len(points)-2,int(i/8));t=i/8-k;w=widths[k]*(1-t)+widths[k+1]*t
  delta=centers[min(i+1,len(centers)-1)]-centers[max(0,i-1)];norm=Vector((-delta.z,0,delta.x)).normalized()
  for sg in [-1,1]:
   q=p+norm*(w*sg);q.y=front(q.x,q.z,.00065);verts.append(tuple(q))
 for i in range(len(centers)-1):faces.append((2*i,2*i+1,2*i+3,2*i+2))
 return mesh(name,verts,faces,'Markings')


def make_markings():
 for s in [-1,1]:
  specs=[
   ([(s*.290,0,1.622),(s*.332,0,1.604),(s*.351,0,1.574)],[.0003,.013,.0003]),
   ([(s*.346,0,1.638),(s*.376,0,1.614),(s*.377,0,1.584)],[.0003,.011,.0003]),
   ([(s*.315,0,1.581),(s*.344,0,1.553),(s*.349,0,1.525)],[.0003,.010,.0003]),
   ([(s*.368,0,1.525),(s*.384,0,1.482),(s*.378,0,1.450)],[.0003,.009,.0003]),
   ([(s*.447,0,1.299),(s*.479,0,1.270),(s*.488,0,1.243)],[.0003,.012,.0003]),
   ([(s*.468,0,1.246),(s*.493,0,1.216),(s*.497,0,1.189)],[.0003,.010,.0003]),
   ([(s*.501,0,1.193),(s*.520,0,1.167),(s*.519,0,1.149)],[.0003,.007,.0003]),
  ]
  for j,(p,w) in enumerate(specs):petal_mark(f'SkinMark.{s}.{j}',p,w)


def make_clothes():
 # Clean, continuous draped panels. Grid parameterization avoids jagged face-selection edges.
 for s in [-1,1]:
  zs=[1.72,1.66,1.59,1.51,1.42,1.33,1.25,1.19]
  xs=[.095,.155,.205,.272,.315,.279,.200,.110]
  ws=[.024,.033,.043,.068,.097,.105,.083,.065]
  verts=[];uv=[];faces=[];nr=72;nc=32
  for i in range(nr+1):
   t=i/nr;z=zs[0]+(zs[-1]-zs[0])*t
   cx=float(np.interp(-z,[-q for q in zs],xs));w=float(np.interp(-z,[-q for q in zs],ws))
   for j in range(nc+1):
    u=2*j/nc-1;x=s*(cx+w*u)
    y=front(x,z,.006,fallback=-.115)
    if z>1.64:
     f=ss(1.64,1.72,z);y=y*(1-f)+(-.070)*f
    # Tension folds converge toward the sash and shoulder, not a corrugated cylinder.
    fold=.0030*math.sin((u+1)*math.pi*3.4+t*4)*math.sin(math.pi*t)**1.6
    fold+=.0025*math.sin((u+1)*math.pi*6-t*3)*ss(.55,1,t)
    y-=fold
    verts.append((x,y,z));uv.append(((u+1)/2,t))
  for i in range(nr):
   for j in range(nc):
    p=i*(nc+1)+j;faces.append((p,p+1,p+nc+2,p+nc+1) if s==1 else (p+1,p,p+nc+1,p+nc+2))
  o=mesh('ChestDrape.'+str(s),verts,faces,'Cloth',uv)
  solid=o.modifiers.new('FoldedFabricEdge','SOLIDIFY');solid.thickness=.0025;solid.offset=0;apply(o,solid)
  # Over-shoulder back strap, joined visually beneath the hair to the waist.
  points=[(s*.095,-.07,1.72),(s*.090,.005,1.728),(s*.092,.088,1.67),(s*.11,.106,1.48),(s*.12,.105,1.25),(s*.10,.13,1.19)]
  sweep(f'BackStrap.{s}',points,[.024,.025,.026,.028,.033,.035],[.002]*6,material='Cloth',sides=8,steps=8)
 # Wrapped sash, individually modelled overlapping folds and cord knot.
 n=128;m=8;verts=[];uv=[];faces=[]
 for j in range(m+1):
  h=j/m
  for k in range(n):
   th=2*math.pi*k/n;z=1.174+.070*h+.006*math.sin(th+.4)*(2*h-1)
   rx=.241+.004*math.sin(h*math.pi*4+th*3);ry=.185+.003*math.cos(h*math.pi*5+th*2)
   verts.append((rx*math.cos(th),-.009+ry*math.sin(th),z));uv.append((k/n,h))
 for j in range(m):
  for k in range(n):
   p=j*n+k;q=j*n+(k+1)%n;faces.append((p,q,q+n,p+n))
 o=mesh('WaistSash',verts,faces,'Sash',uv);solid=o.modifiers.new('SashThickness','SOLIDIFY');solid.thickness=.004;apply(o,solid)
 for j in range(3):
  points=[]
  for k in range(17):
   th=2*math.pi*k/16;points.append((.244*math.cos(th),-.009+.188*math.sin(th),1.185+j*.019+.004*math.sin(th*2+j)))
  sweep('SashFold.'+str(j),points,[.003]*len(points),[.002]*len(points),material='Sash',sides=8,steps=4)
 knot=Vector((.100,-.190,1.210))
 sphere('SashKnot',knot,(.020,.014,.023),'Sash')
 for s in [-1,1]:
  points=[tuple(knot+Vector((0,-.009,0))),tuple(knot+Vector((s*.040,-.018,.020))),tuple(knot+Vector((s*.045,-.019,-.004))),tuple(knot+Vector((s*.010,-.009,-.008)))]
  sweep(f'SashLoop.{s}',points,[.006,.005,.005,.006],material='Sash',sides=12,steps=10)
 for j in range(2):
  sweep('SashTie.'+str(j),[(.10+j*.013,-.202,1.205),(.102+j*.014,-.218,1.145),(.090+j*.020,-.240,1.070),(.08+j*.022,-.249,1.044+j*.026)],[.007,.006,.005,.004],material='Sash',sides=12,steps=12)
 # Below-waist cloth: broad diagonal swag and smaller longitudinal folds.
 for back in [False,True]:
  verts=[];faces=[];uv=[];nx=56;ny=72
  for i in range(ny+1):
   t=i/ny
   w=float(np.interp(t,[0,.20,.55,1],[.225,.205,.193,.175]));basez=1.185-.86*t
   for j in range(nx+1):
    u=2*j/nx-1;x=w*u
    z=basez+(.075*abs(u)**1.5+.020*u)*ss(.82,1,t)
    y=float(np.interp(t,[0,.15,.40,1],[-.183,-.245,-.253,-.230]))
    y-=.012*math.cos(3.5*math.pi*u+t*1.7)*math.sin(math.pi*t)**.4
    y-=.005*math.cos(7.5*math.pi*u-t*2)*ss(.08,.3,t)
    y-=.015*math.exp(-((t-(.14+.13*u))/.065)**2)
    if back:y=-y-.045;z+=.04*t
    verts.append((x,y,z));uv.append(((u+1)/2,t))
  for i in range(ny):
   for j in range(nx):
    p=i*(nx+1)+j;f=(p,p+1,p+nx+2,p+nx+1);faces.append(tuple(reversed(f)) if back else f)
  o=mesh('RearDrape' if back else 'FrontDrape',verts,faces,'Cloth',uv)
  solid=o.modifiers.new('TailoredDoubleSidedFabric','SOLIDIFY');solid.thickness=.0025;solid.offset=0;apply(o,solid)


def bind_all(body):
 # Preserve the body's inherited anatomical weighting; new fitted surfaces transfer it.
 body.parent=b.RIG;mod=body.modifiers.new('DeformationSkin','ARMATURE');mod.object=b.RIG
 skin_tree=BVHTree.FromPolygons([p.co for p in body.data.vertices],[tuple(p.vertices) for p in body.data.polygons])
 for o in PARTS:
  if o is body:continue
  o.parent=b.RIG;vg={name:o.vertex_groups.new(name=name) for name in b.BONES if b.BONES[name][3]}
  for p in o.data.vertices:
   if o.name.startswith(('ChestDrape','SkinMark')):
    pos,normal,face,distance=skin_tree.find_nearest(p.co)
    verts=body.data.polygons[face].vertices
    weighted={};den=0.
    for vi in verts:
     vv=body.data.vertices[vi];w=1/max(.0001,(vv.co-p.co).length)**2;den+=w
     for g in vv.groups:
      name=body.vertex_groups[g.group].name
      weighted[name]=weighted.get(name,0)+g.weight*w
    chosen=sorted(weighted.items(),key=lambda t:t[1],reverse=True)[:4];total=sum(w for _,w in chosen)
    for name,w in chosen:vg[name].add([p.index],w/total,'REPLACE')
   else:
    if o.name.startswith('BackWave'):
     side='L' if p.co.x>=0 else 'R';names=['Head']+[f'Hair{k}.{side}' for k in range(3)]
    elif o.name.startswith('Tail'):names=[f'Tail{k:02d}' for k in range(6)]
    elif o.name.startswith(('Sash','Waist','FrontDrape','RearDrape')):names=['Pelvis']
    elif o.name.startswith('BackStrap'):names=['Neck','UpperChest','Chest','Spine02']
    else:names=['Head']
    weights=sorted([(b.segment_distance(p.co,b.BONES[n][0],b.BONES[n][1]),n) for n in names])[:4]
    raw=[1/(d+.025)**4 for d,n in weights];total=sum(raw)
    for (_,n),w in zip(weights,raw):vg[n].add([p.index],w/total,'REPLACE')
  mod=o.modifiers.new('DeformationSkin','ARMATURE');mod.object=b.RIG
 # Keep four normalized influences per vertex for portable export.
 for o in PARTS:
  for p in o.data.vertices:
   values=sorted([(g.group,g.weight) for g in p.groups],key=lambda x:x[1],reverse=True)[:4];total=sum(w for _,w in values)
   for g in list(p.groups):o.vertex_groups[g.group].remove([p.index])
   for gi,w in values:o.vertex_groups[gi].add([p.index],w/total,'REPLACE')


def make_stage():
 scene=bpy.context.scene
 world=bpy.data.worlds.new('NeutralStudioWorld');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.11,.12,.15,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35;scene.world=world
 def area(name,loc,energy,size,color,target):
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.data.color=color;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
 area('Key',( -3,-4,5),500,3.0,(1.,.95,.90),(0,0,1.2))
 area('Fill',(3,-2,2.3),240,2.8,(.83,.89,1.),(0,0,1.3))
 area('Rim',(1.2,2.5,3.4),650,2.2,(.91,.90,1.),(0,0,1.4))
 bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.005));floor=bpy.context.object;floor.name='StudioFloor';floor.data.materials.append(b.MATS['Stage'])
 bpy.ops.object.camera_add(location=(3,-6,2.2));cam=bpy.context.object;cam.name='ReviewCamera';cam.data.type='ORTHO';cam.data.ortho_scale=2.60;scene.camera=cam
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=CFG['render_samples'];scene.cycles.use_denoising=True
 scene.render.resolution_x=1050;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
 scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=0.;scene.render.image_settings.file_format='PNG'
 return cam


def render_views(out,cam,names):
 scene=bpy.context.scene
 views={
  'front':((0,-6,1.17),(0,0,1.08),2.58,(1050,1400)),
  'three-quarter':((3,-6,2.05),(0,-.015,1.10),2.58,(1200,1500)),
  'side':((6,-.02,1.2),(0,-.02,1.1),2.58,(1050,1400)),
  'back':((0,6,1.3),(0,0,1.1),2.58,(1050,1400)),
  'portrait':((.35,-6,2.00),(0,-.10,1.85),.60,(1000,1100)),
  'reference':((.9,-6,2.0),(0,-.06,1.49),1.40,(1250,1400)),
 }
 for name in names:
  loc,target,scale,size=views[name];cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
  scene.render.resolution_x,scene.render.resolution_y=size;scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--base-data',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--views',default='portrait,front,three-quarter,side,back,reference');ap.add_argument('--config',type=Path);ap.add_argument('--no-export',action='store_true');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
 if args.config:CFG.update(json.loads(args.config.read_text()))
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);PARTS.clear();b.BONES.clear();b.MATS.clear()
 scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1;scene.frame_start=1;scene.frame_end=211;scene.render.fps=30
 make_materials();body,v,definition,weights=make_anatomy(args.base_data);make_face(v,definition);make_hair();tail=make_horns_tail();make_markings();make_clothes()
 a.create_rig(v,definition,tail);bind_all(body)
 # Retain native poses as diagnostics, not as finished locomotion animations.
 body.shape_key_add(name='Basis');body.shape_key_add(name='ShoulderVolume');body.shape_key_add(name='HipFlexionVolume');a.pose_study(body.data.shape_keys);scene.frame_set(1)
 camera=make_stage();a.export_tissue(out)
 bpy.ops.wm.save_as_mainfile(filepath=str(out/'character-likeness.blend'))
 if not args.no_export:
  bpy.ops.object.select_all(action='DESELECT');b.RIG.select_set(True)
  for o in PARTS:o.select_set(True)
  bpy.context.view_layer.objects.active=b.RIG
  bpy.ops.export_scene.gltf(filepath=str(out/'character-likeness.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=False,export_texcoords=True,export_normals=True,export_tangents=True,export_animations=True,export_animation_mode='SCENE',export_anim_scene_split_object=False,export_nla_strips_merged_animation_name='ValidationPoses',export_frame_range=True,export_force_sampling=True,export_skins=True,export_morph=True,export_morph_animation=True,export_cameras=False,export_lights=False)
 render_views(out,camera,[x for x in args.views.split(',') if x]);scene.frame_set(1)
 bpy.ops.wm.save_as_mainfile(filepath=str(out/'character-likeness.blend'))
 manifest={'status':'likeness iteration awaiting visual acceptance','config':CFG,'bodyVertices':len(body.data.vertices),'meshes':len(PARTS),'totalTriangles':sum(sum(len(f.vertices)-2 for f in o.data.polygons) for o in PARTS),'bones':len(b.RIG.data.bones),'morphTargets':a.TARGETS,'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()}}
 (out/'likeness-manifest.json').write_text(json.dumps(manifest,indent=2));print('LIKENESS_BUILD_COMPLETED')

if __name__=='__main__':main()
