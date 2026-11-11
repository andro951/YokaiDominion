"""Character01 anatomical-topology authoring prototype.
CC0 MakeHuman graphical data only; no MakeHuman application code is imported.
Run with --base-data path/to/makehuman/data --out output [--preview-only].
"""
from __future__ import annotations
import argparse,hashlib,json,math,os,sys
from pathlib import Path
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_character as b

TARGETS={
 'macrodetails/caucasian-female-young.target':.6,
 'macrodetails/asian-female-young.target':.4,
 'macrodetails/universal-female-young-maxmuscle-averageweight.target':1.,
 'breast/female-young-maxmuscle-averageweight-maxcup-maxfirmness.target':2.2,
 'breast/breast-point-decr.target':.7,
 'eyes/l-eye-height2-decr.target':.25,
 'eyes/r-eye-height2-decr.target':.25,
 'eyes/l-eye-corner2-up.target':.3,
 'eyes/r-eye-corner2-up.target':.3,
}
RENAME={'root':'Pelvis','spine05':'PelvicSpine','spine04':'Spine01','spine03':'Spine02','spine02':'Chest','spine01':'UpperChest','neck01':'LowerNeck','neck02':'MidNeck','neck03':'Neck','head':'Head','jaw':'Jaw'}
for side in ['L','R']:
 for old,new in [('clavicle','Clavicle'),('upperarm01','UpperArm'),('upperarm02','UpperArmTwist'),('lowerarm01','Forearm'),('lowerarm02','ForearmTwist'),('wrist','Hand'),('upperleg01','Thigh'),('upperleg02','ThighTwist'),('lowerleg01','Shin'),('lowerleg02','ShinTwist'),('foot','Foot'),('breast','BreastSupport')]:RENAME[old+'.'+side]=new+'.'+side
 for f,label in enumerate(['Thumb','Index','Middle','Ring','Little'],1):
  for k in range(1,4):RENAME[f'finger{f}-{k}.{side}']=f'{label}{k}.{side}'
 for k in range(1,3):RENAME[f'toe1-{k}.{side}']=f'BigToe{k}.{side}'

def rename(n):return RENAME.get(n,n)
def smooth(a,c,x):
 t=np.clip((x-a)/(c-a),0,1);return t*t*(3-2*t)

def load_data(path):
 vertices=[];uv=[];faces=[];faceuv=[];group='';groups={}
 for line in (path/'3dobjs/base.obj').read_text().splitlines():
  t=line.split()
  if not t:continue
  if t[0]=='v':vertices.append(tuple(map(float,t[1:4])))
  elif t[0]=='vt':uv.append(tuple(map(float,t[1:3])))
  elif t[0]=='g':group=t[1]
  elif t[0]=='f':
   indices=[int(x.split('/')[0])-1 for x in t[1:]];groups.setdefault(group,[]).append(indices)
   if group=='body':faces.append(indices);faceuv.append([int(x.split('/')[1])-1 for x in t[1:]])
 v=np.array(vertices,dtype=float)
 for target,weight in TARGETS.items():
  for line in (path/'targets'/target).read_text().splitlines():
   t=line.split()
   if len(t)==4 and not line.startswith('#'):v[int(t[0])]+=weight*np.array(list(map(float,t[1:])))
 used=sorted({i for f in faces for i in f});miny=v[used,1].min();scale=1.96/(v[used,1].max()-miny)
 v=np.column_stack([v[:,0],-v[:,2],v[:,1]-miny])*scale
 rig=json.loads((path/'rigs/default.mhskel').read_text());weights=json.loads((path/'rigs/default_weights.mhw').read_text())['weights']
 return v,used,faces,np.array(uv),faceuv,rig,weights,groups

def shape_data(v,rig,weights):
 # Spatial shaping on trunk/legs, locally affine limb shaping preserves digits.
 original=v.copy()
 keys=[0,.5,.85,1.,1.13,1.25,1.40,1.55,1.65,1.75,2.0]
 xs=[1.12,1.23,1.65,1.80,1.28,1.12,1.40,1.55,1.32,1.12,1.12]
 ys=[1.0,1.05,1.25,1.48,1.05,1.02,1.25,1.05,1.0,1.06,1.06]
 def warp(p):
  q=np.array(p).copy();q[...,0]*=np.interp(q[...,2],keys,xs);q[...,1]*=np.interp(q[...,2],keys,ys);return q
 shaped=warp(v)
 for side in ['L','R']:
  wrist=rig['bones']['wrist.'+side];elbow=rig['bones']['lowerarm01.'+side];shoulder=rig['bones']['upperarm01.'+side]
  old_w=original[rig['joints'][wrist['head']]].mean(0);old_e=original[rig['joints'][elbow['head']]].mean(0);old_s=original[rig['joints'][shoulder['head']]].mean(0)
  sign=1 if side=='L' else -1
  new_s=np.array([sign*.305,old_s[1],1.61]);new_e=np.array([sign*.455,-.018,1.28]);new_w=np.array([sign*.555,-.022,1.055])
  def affine(p,a,c,aa,cc,width):
   u=(c-a)/np.linalg.norm(c-a);uu=(cc-aa)/np.linalg.norm(cc-aa)
   rot=np.array(Vector(u).rotation_difference(Vector(uu)).to_matrix())
   d=p-a;parallel=np.outer(d@u,u);perp=d-parallel
   return aa+(parallel*np.linalg.norm(cc-aa)/np.linalg.norm(c-a)+perp*width)@rot.T
  acc=np.zeros_like(v);weight_sum=np.zeros(len(v))
  for name,items in weights.items():
   if not name.endswith('.'+side):continue
   if name.startswith(('finger','metacarpal','wrist')):out=affine(original,old_e,old_w,new_e,new_w,1.28)
   elif name.startswith('lowerarm'):out=affine(original,old_e,old_w,new_e,new_w,1.35)
   elif name.startswith('upperarm'):out=affine(original,old_s,old_e,new_s,new_e,1.38)
   else:continue
   for index,w in items:acc[index]+=out[index]*w;weight_sum[index]+=w
  mask=weight_sum>1e-8
  shaped[mask]=shaped[mask]*(1-np.minimum(1,weight_sum[mask,None]))+acc[mask]/weight_sum[mask,None]*np.minimum(1,weight_sum[mask,None])
  for jname,ids in rig['joints'].items():
   if not ('.'+side+'____') in jname:continue
   if jname.startswith(('finger','metacarpal','wrist')):out=affine(original[ids],old_e,old_w,new_e,new_w,1.28)
   elif jname.startswith('lowerarm'):out=affine(original[ids],old_e,old_w,new_e,new_w,1.35)
   elif jname.startswith('upperarm'):out=affine(original[ids],old_s,old_e,new_s,new_e,1.38)
   else:continue
   shaped[ids]=out
 head=smooth(1.66,1.77,shaped[:,2]);shaped[:,0]*=1+.12*head
 shaped[:,1]*=1+.10*head;shaped[:,2]+=(shaped[:,2]-1.72)*.12*head
 # Rounded surface correction follows anatomical breast weights, not a fused sphere.
 for side,sign in [('L',1),('R',-1)]:
  for index,weight in weights['breast.'+side]:
   p=shaped[index];c=np.array([sign*.195,-.19,1.425]);r=np.array([.225,.245,.235]);q=(p-c)/r;norm=np.linalg.norm(q)
   strength=.42*smooth(.08,.48,weight)*smooth(-.12,-.23,p[1])
   if norm>1e-6:shaped[index]=p*(1-strength)+(c+r*q/norm)*strength
 return shaped

def create_body(v,used,faces,uv,faceuv,weights):
 mapping={old:new for new,old in enumerate(used)}
 body=b.mesh_object('Body',[tuple(v[i]) for i in used],[[mapping[i] for i in f] for f in faces])
 tex=body.data.uv_layers.new(name='UVMap')
 for poly,inds in zip(body.data.polygons,faceuv):
  for loop,ui in zip(poly.loop_indices,inds):tex.data[loop].uv=uv[ui]
 groups={name:body.vertex_groups.new(name=rename(name)) for name in weights};pervertex=[[] for _ in used]
 for name,items in weights.items():
  for index,w in items:
   if index in mapping:pervertex[mapping[index]].append((name,w))
 for i,items in enumerate(pervertex):
  chosen=sorted(items,key=lambda a:a[1],reverse=True)[:4];total=sum(w for n,w in chosen)
  if total<=0:raise ValueError(f'No inherited skin weights at {used[i]}')
  for name,w in chosen:groups[name].add([i],w/total,'REPLACE')
 colors=body.data.color_attributes.new(name='SkinPalette',type='FLOAT_COLOR',domain='POINT')
 skin=b.MATS['Skin'].diffuse_color;mark=b.MATS['Markings'].diffuse_color
 for p in body.data.vertices:
  x,y,z=p.co;ax=abs(x);dark=False
  if .28<ax<.48 and 1.32<z<1.65:dark=y<-.025 and math.sin(32*z+12*ax)>.72
  if .44<ax<.61 and 1.08<z<1.32:dark=y<-.025 and math.sin(42*z+18*ax)>.82
  colors.data[p.index].color=mark if dark else skin
 attr=b.MATS['Skin'].node_tree.nodes.new('ShaderNodeVertexColor');attr.layer_name='SkinPalette';b.MATS['Skin'].node_tree.links.new(attr.outputs['Color'],b.MATS['Skin'].node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
 return body

def create_rig(v,definition,tailpts):
 b.BONES.clear();b.bone('Root',(0,0,0),(0,0,.15),None,False);remaining=dict(definition['bones'])
 while remaining:
  progress=False
  for name,data in list(remaining.items()):
   parent=rename(data['parent']) if data['parent'] else 'Root'
   if parent not in b.BONES:continue
   a=v[definition['joints'][data['head']]].mean(0);c=v[definition['joints'][data['tail']]].mean(0)
   if np.linalg.norm(c-a)<1e-5:c=a+np.array([0,0,.005])
   b.bone(rename(name),tuple(a),tuple(c),parent);del remaining[name];progress=True
  if not progress:raise ValueError('Cyclic or unresolved rig parents')
 for i in range(len(tailpts)-1):b.bone(f'Tail{i:02d}',tailpts[i],tailpts[i+1],'Pelvis' if i==0 else f'Tail{i-1:02d}')
 b.bone('Tail05',tailpts[-1],(.75,.16,1.39),'Tail04')
 for side,s in [('L',1),('R',-1)]:
  for k in range(3):b.bone(f'Hair{k}.{side}',(s*.15,.15,1.83-k*.24),(s*.20,.21,1.59-k*.24),'Head' if k==0 else f'Hair{k-1}.{side}')
 data=bpy.data.armatures.new('Character01Rig');rig=bpy.data.objects.new('YokaiRig',data);bpy.context.collection.objects.link(rig);b.RIG=rig
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
 for name,(a,c,parent,deform) in b.BONES.items():
  eb=data.edit_bones.new(name);eb.head=a;eb.tail=c;eb.use_deform=deform;eb.parent=data.edit_bones.get(parent) if parent else None
  eb.align_roll(Vector((0,1,0)) if name.endswith(('.L','.R')) else Vector((0,-1,0)))
 bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True;return rig

def details(v,definition):
 tail=b.make_details()
 for o in list(b.PARTS):
  if o.name.startswith(('EyeWhite','Iris','Pupil','EyeGlint','UpperLid','Brow','Mouth','Fang','CheekMark')):
   b.PARTS.remove(o);bpy.data.objects.remove(o,do_unlink=True)
  elif o.name.startswith(('BackLock','FaceLock','HairCrown','Horn','Ear')):
   for p in o.data.vertices:
    p.co.y-=.035
    if p.co.z>1.70:p.co.x*=1.12;p.co.y*=1.10;p.co.z=1.72+(p.co.z-1.72)*1.12
 for side,s in [('L',1),('R',-1)]:
  e=definition['bones']['eye.'+side];c=Vector(v[definition['joints'][e['head']]].mean(0))
  b.ellipsoid('EyeWhite_'+side,c,(.020,.019,.016),'EyeWhite')
  b.ellipsoid('Iris_'+side,c+Vector((0,-.018,0)),(.010,.002,.010),'Iris')
  b.ellipsoid('Pupil_'+side,c+Vector((0,-.020,0)),(.0045,.001,.007),'Ink')
  b.ellipsoid('EyeGlint_'+side,c+Vector((-.003,-.021,.003)),(.003,.001,.003),'Hair')
  b.tube('Eyeliner_'+side,[tuple(c+Vector((s*dx,dy,dz))) for dx,dy,dz in [(-.021,-.011,.002),(0,-.020,.010),(.023,-.009,.008),(.029,-.004,.011)]],[.0012,.0020,.0020,.0006],mat='Ink',sides=8)
  b.tube('Brow_'+side,[tuple(c+Vector((s*dx,dy,dz))) for dx,dy,dz in [(-.023,-.016,.027),(0,-.021,.034),(.026,-.012,.026)]],[.002,.004,.001],mat='Hair',sides=8)
 return tail

def outfit(body):
 # Fitted patches share the body's topology/weights. Free-hanging cloth is still provisional.
 prior=len(b.PARTS);b.make_outfit()
 for o in list(b.PARTS[prior:]):
  if o.name.startswith('ChestDrape'):b.PARTS.remove(o);bpy.data.objects.remove(o,do_unlink=True)
 body.data.update();heights=[1.18,1.27,1.39,1.49,1.60,1.68];centers=[.13,.20,.29,.28,.21,.10];widths=[.09,.10,.082,.067,.048,.030]
 for sign in [-1,1]:
  selected=[]
  for face in body.data.polygons:
   p=face.center;cx=np.interp(p.z,heights,centers);w=np.interp(p.z,heights,widths)
   if 1.18<p.z<1.68 and p.y<-.015 and abs(sign*p.x-cx)<w:selected.append(face)
  used=sorted({i for f in selected for i in f.vertices});indices={old:new for new,old in enumerate(used)}
  positions=[tuple(body.data.vertices[i].co+body.data.vertices[i].normal*.018) for i in used]
  garment=b.mesh_object('ChestDrape_'+str(sign),positions,[[indices[i] for i in f.vertices] for f in selected],'Cloth')
  groups={g.index:garment.vertex_groups.new(name=g.name) for g in body.vertex_groups}
  for new,old in enumerate(used):
   for g in body.data.vertices[old].groups:groups[g.group].add([new],g.weight,'REPLACE')
  bpy.context.view_layer.objects.active=garment
  import bmesh
  bm=bmesh.new();bm.from_mesh(garment.data);boundary=[p for p in bm.verts if p.is_boundary]
  tree=BVHTree.FromPolygons([p.co for p in body.data.vertices],[tuple(p.vertices) for p in body.data.polygons])
  for iteration in range(18):
   moved={}
   for p in boundary:
    neighbors=[e.other_vert(p) for e in p.link_edges if e.is_boundary]
    if len(neighbors)==2:
     q=p.co*.35+(neighbors[0].co+neighbors[1].co)*.325;hit=tree.find_nearest(q)
     if hit[0] is not None:q=hit[0]+hit[1]*.018
     moved[p]=q
   for p,q in moved.items():p.co=q
  bm.to_mesh(garment.data);bm.free();garment.data.update()
  sub=garment.modifiers.new('GarmentEdgeSmoothing','SUBSURF');sub.levels=2;bpy.ops.object.modifier_apply(modifier=sub.name)
  solid=garment.modifiers.new('FabricThickness','SOLIDIFY');solid.thickness=.003;bpy.ops.object.modifier_apply(modifier=solid.name)
 for o in b.PARTS:
  if o.name.startswith(('WaistSash','Sash')):
   for p in o.data.vertices:p.co.z-=.02
  if o.name=='FrontDrape':
   for p in o.data.vertices:p.co.y=float(np.interp(p.co.z,[.3,.6,.85,1.02,1.19],[-.245,-.255,-.26,-.24,-.18]))-.005*math.cos(p.co.x*60)
  if o.name.startswith('BackStrap'):
   for p in o.data.vertices:
    t=smooth(1.59,1.712,p.co.z);p.co.x*=1-.62*t;p.co.z-=.032*t

def bind_details(body):
 for o in b.PARTS:
  if o is body or o.name.startswith('ChestDrape'):
   for vertex in o.data.vertices:
    pairs=sorted([(g.group,g.weight) for g in vertex.groups],key=lambda p:p[1],reverse=True)[:4];total=sum(w for _,w in pairs)
    for group in list(vertex.groups):o.vertex_groups[group.group].remove([vertex.index])
    for index,weight in pairs:o.vertex_groups[index].add([vertex.index],weight/total,'REPLACE')
   o.parent=b.RIG;mod=o.modifiers.new('DeformationSkin','ARMATURE');mod.object=b.RIG;continue
  if not o.data.uv_layers:
   bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.01);bpy.ops.object.mode_set(mode='OBJECT')
  groups={n:o.vertex_groups.new(name=n) for n in b.BONES if b.BONES[n][3]}
  for p in o.data.vertices:
   if o.name.startswith('BackLock'):names=['Head']+[f'Hair{k}.{"L" if p.co.x>0 else "R"}' for k in range(3)]
   elif o.name.startswith('Tail'):names=[f'Tail{k:02d}' for k in range(6)]
   elif o.name.startswith(('Sash','Waist','FrontDrape','RearDrape')):names=['Pelvis']
   elif o.name.startswith(('ChestDrape','BackStrap')):names=['Spine01','Spine02','Chest','UpperChest']
   else:names=['Head']
   pairs=sorted([(b.segment_distance(p.co,b.BONES[n][0],b.BONES[n][1]),n) for n in names])[:4];raw=[1/(d+.03)**4 for d,n in pairs];total=sum(raw)
   for (d,n),w in zip(pairs,raw):groups[n].add([p.index],w/total,'REPLACE')
  o.parent=b.RIG;mod=o.modifiers.new('DeformationSkin','ARMATURE');mod.object=b.RIG

def pose_study(keys):
 for name,frame in b.POSES:
  for p in b.RIG.pose.bones:p.rotation_mode='XYZ';p.rotation_euler=(0,0,0);p.location=(0,0,0)
  def rotate(n,x=0,y=0,z=0):b.RIG.pose.bones[n].rotation_euler=tuple(math.radians(a) for a in (x,y,z))
  if name=='overhead':rotate('UpperArm.L',z=-135);rotate('UpperArm.R',z=135)
  elif name=='crouch':
   for side in ['L','R']:rotate('Thigh.'+side,x=-70);rotate('Shin.'+side,x=115);rotate('Foot.'+side,x=-45)
   rotate('Spine01',x=12);rotate('Spine02',x=12)
  elif name=='high_kick':rotate('Thigh.L',x=-105);rotate('Shin.L',x=8);rotate('Spine01',x=-10)
  elif name=='torso_twist':rotate('Spine01',y=12);rotate('Spine02',y=18);rotate('Chest',y=20);rotate('UpperChest',y=10)
  elif name=='jump':
   for side in ['L','R']:rotate('Thigh.'+side,x=-30);rotate('Shin.'+side,x=60)
   rotate('UpperArm.L',z=-65);rotate('UpperArm.R',z=65)
  elif name=='knockdown':rotate('Root',x=86);rotate('Thigh.L',x=-10);rotate('Forearm.R',x=-35)
  delta=(0,0,-.36) if name=='crouch' else (0,0,.40) if name=='jump' else (0,-.4,.21) if name=='knockdown' else (0,0,0)
  b.RIG.pose.bones['Root'].location=b.RIG.data.bones['Root'].matrix_local.to_3x3().inverted()@Vector(delta)
  for p in b.RIG.pose.bones:p.keyframe_insert(data_path='rotation_euler',frame=frame,group=p.name);p.keyframe_insert(data_path='location',frame=frame,group=p.name)
  for key in keys.key_blocks:
   if key.name!='Basis':key.value=0;key.keyframe_insert(data_path='value',frame=frame)

def export_tissue(out):
 doc=b.export_regions(out)
 for r in doc['regions']:
  breast=r['name'].startswith('breast');sign=1 if r['center'][0]>0 else -1
  old_c=r['center'];old_r=r['radii'];center=[sign*.195,1.425,.19] if breast else [sign*.18,.99,-.10];radii=[.265,.285,.28] if breast else [.28,.28,.27]
  r['nodes']=[[center[k]+(p[k]-old_c[k])*radii[k]/old_r[k] for k in range(3)] for p in r['nodes']];r['center']=center;r['radii']=radii
  r['youngModulus']=45000 if breast else 70000;r['poissonRatio']=.4999;r['solverSubsteps']=16;r['solverIterations']=16;r['velocityDrag']=4.0
 (out/'tissue-regions.json').write_text(json.dumps(doc,separators=(',',':')));return doc

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--base-data',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--preview-only',action='store_true');ap.add_argument('--views',default='front,three-quarter,side,back,overhead,crouch,high-kick');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);b.PARTS.clear();b.BONES.clear()
 scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1;scene.frame_start=1;scene.frame_end=211;scene.render.fps=30
 for name,color,rough in [('Skin','777b91',.62),('PlainSkin','777b91',.62),('Markings','44475e',.68),('Hair','eee9ef',.55),('Horn','292839',.48),('Cloth','d8ccb8',.90),('Ink','24232a',.80),('EyeWhite','c9cbd9',.35),('Iris','777fb3',.38),('Stage','414552',.85)]:b.material(name,color,rough)
 v,used,faces,uv,faceuv,definition,weights,groups=load_data(args.base_data);v=shape_data(v,definition,weights);body=create_body(v,used,faces,uv,faceuv,weights);tail=details(v,definition);outfit(body);create_rig(v,definition,tail);bind_details(body)
 body.shape_key_add(name='Basis');body.shape_key_add(name='ShoulderVolume');body.shape_key_add(name='HipFlexionVolume');keys=body.data.shape_keys;pose_study(keys);scene.frame_set(1)
 export_tissue(out);camera=b.build_stage();scene.view_settings.exposure=-.60;camera.data.ortho_scale=2.50;scene.cycles.samples=16;scene.render.resolution_x=800;scene.render.resolution_y=1000
 if not args.preview_only:
  bpy.ops.wm.save_as_mainfile(filepath=str(out/'character-blockout.blend'))
  bpy.ops.object.select_all(action='DESELECT');b.RIG.select_set(True)
  for o in b.PARTS:o.select_set(True)
  bpy.context.view_layer.objects.active=b.RIG
  bpy.ops.export_scene.gltf(filepath=str(out/'character-blockout.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=False,export_texcoords=True,export_normals=True,export_tangents=True,export_animations=True,export_animation_mode='SCENE',export_anim_scene_split_object=False,export_nla_strips_merged_animation_name='ValidationPoses',export_frame_range=True,export_force_sampling=True,export_skins=True,export_morph=True,export_morph_animation=True,export_cameras=False,export_lights=False)
 views=[('front',(0,-5,1.16),1),('three-quarter',(3,-5,1.8),1),('side',(5,0,1.17),1),('back',(0,5,1.17),1),('overhead',(3,-5,1.8),31),('crouch',(3,-5,1.8),61),('high-kick',(3,-5,1.8),91)]
 for name,loc,frame in views:
  if name not in args.views.split(','):continue
  scene.frame_set(frame);camera.location=loc;camera.rotation_euler=(Vector((0,0,1.08))-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
 scene.frame_set(1)
 if not args.preview_only:bpy.ops.wm.save_as_mainfile(filepath=str(out/'character-blockout.blend'))
 manifest={'status':'anatomical-topology prototype; not finished visual/deformation acceptance','sourceCommit':os.getenv('GITHUB_SHA'),'baseSource':'makehumancommunity/makehuman@a8bc2d54ff0ac92e78ff71431b1023eda42bf482','assetLicense':'CC0-1.0; no application code reused','blender':bpy.app.version_string,'bodyVertices':len(body.data.vertices),'bodyFaces':len(body.data.polygons),'bones':len(b.BONES),'upstreamFiles':{str(p.relative_to(args.base_data)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [args.base_data/'3dobjs/base.obj',args.base_data/'rigs/default.mhskel',args.base_data/'rigs/default_weights.mhw']+[args.base_data/'targets'/t for t in TARGETS]},'targetWeights':TARGETS,'limitations':['Not final silhouette or material approval.','Diagnostic poses only; no IK/locomotion/ragdoll controller.','Corrective shape placeholders intentionally zero pending anatomy-specific authoring.','No cloth/hair runtime simulation or complete contact.']}
 (out/'character-manifest.json').write_text(json.dumps(manifest,indent=2));print('YOKAI_ANATOMY_AUTHOR_PASS')
if __name__=='__main__':main()
