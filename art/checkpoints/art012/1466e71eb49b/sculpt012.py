"""Volumetric chest revision; surrounding anatomy is restored to the native surface.
The source Art011 mesh remains archived. This changes topology and is not a rig acceptance.
"""
import bpy,numpy as np,math,sys,json,argparse,hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
REVISION='012-continuous-volume-9'
def read(o):
 p=np.empty(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',p);return p.reshape(-1,3)
def write(o,p):
 assert np.isfinite(p).all();o.data.vertices.foreach_set('co',p.ravel());o.data.update()
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def curve(t,x,y):
 x=np.asarray(x);y=np.asarray(y);h=np.diff(x);d=np.diff(y)/h;m=np.zeros(len(x));m[0]=d[0];m[-1]=d[-1]
 for i in range(1,len(x)-1):
  if d[i-1]*d[i]>0:
   w1=2*h[i]+h[i-1];w2=h[i]+2*h[i-1];m[i]=(w1+w2)/(w1/d[i-1]+w2/d[i])
 i=int(np.clip(np.searchsorted(x,t)-1,0,len(x)-2));u=np.clip((t-x[i])/h[i],0,1)
 return (2*u**3-3*u*u+1)*y[i]+(u**3-2*u*u+u)*h[i]*m[i]+(-2*u**3+3*u*u)*y[i+1]+(u**3-u*u)*h[i]*m[i+1]
ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(args.source.resolve()))
old=bpy.data.objects['Body'];p=read(old);native=np.empty(p.size);old.data.attributes['art010_previous_position'].data.foreach_get('vector',native);native=native.reshape(-1,3)
source=old.copy();source.data=old.data.copy();bpy.context.collection.objects.link(source);source.name='Body_NATIVE_TRANSFER';write(source,native)
source.data.calc_loop_triangles();tri=np.array([t.vertices[:] for t in source.data.loop_triangles],dtype=int)
tree=BVHTree.FromPolygons([Vector(v) for v in native],tri.tolist(),all_triangles=True)
attrs={}
for name in ['Complexion','AnatomicalRoughness','source_position']:
 a=source.data.attributes.get(name)
 if a:
  prop,n={'FLOAT_COLOR':('color',4),'FLOAT':('value',1),'FLOAT_VECTOR':('vector',3)}[a.data_type]
  v=np.empty(len(native)*n);a.data.foreach_get(prop,v);attrs[name]=(a.data_type,prop,n,v.reshape(len(native),n))
old.name='Body_Art011_Archive';old.hide_render=True;old.hide_set(True)
body=source.copy();body.data=source.data.copy();bpy.context.collection.objects.link(body);body.name='Body';source.hide_render=True;source.hide_set(True)
parts=[body]
for side in [-1,1]:
 verts=[];faces=[];N=80;M=64
 for i in range(M+1):
  theta=math.pi*i/M;s=(1+math.cos(theta))/2
  z=1.252+.350*s;yc=curve(s,[0,.25,.55,.8,1],[-.178,-.191,-.150,-.090,-.035]);cx=.118
  factor=curve(s,[0,.25,.55,.8,1],[1.02,1.11,.96,.67,.28])
  rx=.111*math.sin(theta)*factor;ry=.121*math.sin(theta)*factor
  for j in range(N):
   a=2*math.pi*j/N;verts.append((side*(cx+rx*math.cos(a)),yc+ry*math.sin(a),z))
 for i in range(M):
  for j in range(N):
   a=i*N+j;b=i*N+(j+1)%N;c=(i+1)*N+(j+1)%N;d=(i+1)*N+j
   faces.append((a,b,c,d) if side>0 else (d,c,b,a))
 me=bpy.data.meshes.new('TissueVolume');me.from_pydata(verts,[],faces);me.update();obj=bpy.data.objects.new('TissueVolume',me);bpy.context.collection.objects.link(obj)
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT');parts.append(obj)
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True);o.hide_set(False)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
r=body.modifiers.new('Localized volume union','REMESH');r.mode='VOXEL';r.voxel_size=.0022;r.use_smooth_shade=True
bpy.ops.object.modifier_apply(modifier=r.name)
s=body.modifiers.new('Round volume junctions','SMOOTH');s.factor=.65;s.iterations=35;bpy.ops.object.modifier_apply(modifier=s.name)
co=read(body);print('NEW VERTICES',len(co),flush=True)
ids=np.empty((len(co),3),dtype=int);weights=np.empty((len(co),3));hits=np.empty_like(co)
for i,v in enumerate(co):
 h,n,k,d=tree.find_nearest(Vector(v));ix=tri[k];a,b,c=native[ix];u=b-a;w=c-a;q=np.array(h)-a;uu=u@u;uw=u@w;ww=w@w;den=uu*ww-uw*uw
 if abs(den)<1e-18:bc=np.array([1.,0,0])
 else:
  s=(ww*(q@u)-uw*(q@w))/den;t=(uu*(q@w)-uw*(q@u))/den;bc=np.array([1-s-t,s,t])
 ids[i]=ix;weights[i]=bc;hits[i]=h
x,y,z=co.T;ax=abs(x)
region=smooth(.001,.014,ax)*(1-smooth(.225,.275,ax))*smooth(1.205,1.24,z)*(1-smooth(1.57,1.635,z))*(1-smooth(-.055,-.025,y))
co=hits*(1-region[:,None])+co*region[:,None];write(body,co)
for name,(typ,prop,n,v) in attrs.items():
 if name in body.data.attributes:body.data.attributes.remove(body.data.attributes[name])
 a=body.data.attributes.new(name,typ,'POINT');vals=np.sum(v[ids]*weights[:,:,None],axis=1);a.data.foreach_set(prop,vals.ravel())
for name in ['art010_previous_position','art011_previous_position','art011_delta']:
 if name in body.data.attributes:body.data.attributes.remove(body.data.attributes[name])
mask=smooth(.003,.018,np.linalg.norm(co-hits,axis=1))*region
attribute=body.data.attributes.new('Art012TissueAlbedo','FLOAT','POINT');attribute.data.foreach_set('value',mask)
mat=body.data.materials[0].copy();mat.name='Skin | Art012 continuous tissue';body.data.materials[0]=mat
nodes=mat.node_tree.nodes;links=mat.node_tree.links;bsdf=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
original=bsdf.inputs['Base Color'].links[0].from_socket
attribute=nodes.new('ShaderNodeAttribute');attribute.attribute_name='Art012TissueAlbedo'
mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[2].default_value=(.15103497,.15714701,.23297073,1)
links.new(attribute.outputs['Fac'],mix.inputs[0]);links.new(original,mix.inputs[1]);links.new(mix.outputs[0],bsdf.inputs['Base Color'])
rough=nodes.new('ShaderNodeMixRGB');rough.inputs[2].default_value=(.52,.52,.52,1)
links.new(attribute.outputs['Fac'],rough.inputs[0])
if bsdf.inputs['Roughness'].is_linked:links.new(bsdf.inputs['Roughness'].links[0].from_socket,rough.inputs[1])
else:rough.inputs[1].default_value=(.52,.52,.52,1)
links.new(rough.outputs[0],bsdf.inputs['Roughness'])
for f in body.data.polygons:f.use_smooth=True
body['art012']=REVISION;body['clothing_shapes_body']=False;body['retopology_required']=True
bpy.context.scene['art_checkpoint']=REVISION
bpy.data.objects.remove(source,do_unlink=True)
bodytree=BVHTree.FromPolygons([Vector(v) for v in co],[f.vertices[:] for f in body.data.polygons])
for side in ['L','R']:
 o=bpy.data.objects['Loose over-trapezius panel '+side];g=read(o).reshape(242,33,3);sg=1 if side=='L' else -1
 knots=[1.197,1.24,1.28,1.34,1.42,1.50,1.56,1.6003]
 inner=[.021,.040,.073,.108,.115,.105,.088,.084];outer=[.149,.155,.187,.228,.225,.179,.145,.132]
 first=g[0].copy();last=g[99].copy()
 for i in range(1,99):
  t=i/99;zz=1.197+(1.6003-1.197)*t;lo=curve(zz,knots,inner);hi=curve(zz,knots,outer)
  for j,u in enumerate(np.linspace(0,1,33)):
   xx=sg*(lo*(1-u)+hi*u);h,_,_,_=bodytree.ray_cast(Vector((xx,-2,zz)),Vector((0,1,0)),4)
   yy=(h.y if h is not None else -.12)-.0045;g[i,j]=[xx,yy,zz]
 g[0]=first;g[99]=last
 for j in range(33):
  k=int(np.argmin(g[:100,j,1]));t=np.linspace(0,1,k+1)
  bridge=g[0,j,1]*(1-t)+g[k,j,1]*t-.008*np.sin(math.pi*t)
  g[:k+1,j,1]=np.minimum(g[:k+1,j,1],bridge)
 for i in range(1,98):
  t=i/99
  for j,u in enumerate(np.linspace(-1,1,33)):
   g[i,j,1]-=(.0018+.0025*math.sin(math.pi*t)**2)*(1+math.sin(2.2*math.pi*u+1.8*t+.2*sg))*math.sin(math.pi*t)
 write(o,g.reshape(-1,3));o['art012']=REVISION
bpy.ops.outliner.orphans_purge(do_local_ids=True,do_linked_ids=False,do_recursive=True)
bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0
f=out/'Character01_Art012.blend';bpy.ops.wm.save_as_mainfile(filepath=str(f),compress=True)
report={'revision':REVISION,'bodyVertices':len(co),'method':'Volumetric union, smooth attachment, projection back to native anatomy outside chest','newTopology':True,'staticVisualAsset':True,'rigUpdated':False,'physicsUpdated':False,'userApproved':False,'sourceSha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),'files':{f.name:{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}}}
bpy.ops.wm.open_mainfile(filepath=str(f));assert bpy.data.objects['Body'].get('art012')==REVISION;report['savedBlendReopened']=True
(out/'manifest.json').write_text(json.dumps(report,indent=2));print('ART012_SAVED_REOPENED',flush=True)
