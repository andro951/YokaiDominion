"""Transfer Art011 delta to existing textured mesh, preserving UVs and materials."""
from pathlib import Path
import argparse,hashlib,json,struct,sys
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from refine011 import read,write,render

def digest(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def uvhash(o):
 a=np.empty(len(o.data.uv_layers.active.data)*2);o.data.uv_layers.active.data.foreach_get('uv',a);return hashlib.sha256(a.tobytes()).hexdigest()
def export(master,portable,out):
 bpy.ops.wm.open_mainfile(filepath=str(master));body=bpy.data.objects['Body'];new=read(body)
 old=np.empty(new.size);body.data.attributes['art011_previous_position'].data.foreach_get('vector',old);old=old.reshape(-1,3);delta=new-old;revision=body['art011']
 names=['Loose over-trapezius panel L','Loose over-trapezius panel R']
 bpy.ops.wm.open_mainfile(filepath=str(portable));high=bpy.data.objects['Body_SculptSource'];hp=read(high)
 assert hp.shape==old.shape and np.allclose(hp,old,rtol=0,atol=1e-7),'Wrong PBR baseline'
 high.data.calc_loop_triangles();tri=np.empty(len(high.data.loop_triangles)*3,dtype=np.int32);high.data.loop_triangles.foreach_get('vertices',tri);tri=tri.reshape(-1,3)
 bvh=BVHTree.FromPolygons([Vector(v) for v in hp],tri.tolist(),all_triangles=True)
 low=bpy.data.objects['Body'];p=read(low);q=p.copy();uv_before=uvhash(low);x,y,z=p.T
 ids=np.flatnonzero((z>1.25)&(z<1.60)&(abs(x)<.28)&(y<.02));distances=[]
 for i in ids:
  hit,normal,index,distance=bvh.find_nearest(Vector(p[i]));distances.append(distance)
  if index is None:raise ValueError('Source mapping missing')
  ix=tri[index];a,b,c=hp[ix];u=b-a;v=c-a;w=np.array(hit)-a;uu=u@u;uv=u@v;vv=v@v;den=uu*vv-uv*uv
  if abs(den)<1e-18:weights=np.array([1.,0,0])
  else:
   s=(vv*(w@u)-uv*(w@v))/den;t=(uu*(w@v)-uv*(w@u))/den;weights=np.array([1-s-t,s,t])
  q[i]+=weights@delta[ix]
 protected=(z>=1.60)|(z<=1.25)|(abs(x)>=.28)|(y>=.02)
 assert np.array_equal(q[protected],p[protected])
 write(low,q);write(high,new);low['art011']=revision;low['runtimePhysicsIntegrated']=False
 assert uv_before==uvhash(low),'UV coordinates changed'
 cloth=bpy.data.objects[names[0]].data.materials[0]
 for name in names:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
 with bpy.data.libraries.load(str(master),link=False) as (src,dst):dst.objects=names
 for o in dst.objects:
  assert o is not None
  bpy.data.collections['04_GARMENT'].objects.link(o);o.data.materials.clear();o.data.materials.append(cloth)
 objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render and not o.name.startswith('STUDIO')]
 bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0;pbr=out/'Character01_PBR011.blend';bpy.ops.wm.save_as_mainfile(filepath=str(pbr),compress=True)
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.hide_set(False);o.select_set(True)
 bpy.context.view_layer.objects.active=low;glb=out/'Character01_Visual011.glb'
 bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_texcoords=True,export_normals=True,export_tangents=True,export_materials='EXPORT',export_vertex_color='MATERIAL',export_animations=False,export_skins=False,export_morph=False,export_cameras=False,export_lights=False,export_extras=True)
 data=glb.read_bytes();magic,version,size=struct.unpack_from('<III',data);assert magic==0x46546c67 and version==2 and size==len(data)
 length,kind=struct.unpack_from('<II',data,12);doc=json.loads(data[20:20+length]);tail=data[20+length:]
 for mat in doc.get('materials',[]):
  if mat.get('name','').startswith('Hair008'):mat['alphaMode']='MASK';mat['alphaCutoff']=.30;mat['doubleSided']=True
 payload=json.dumps(doc,separators=(',',':')).encode();payload+=b' '*((-len(payload))%4)
 glb.write_bytes(struct.pack('<III',magic,2,20+len(payload)+len(tail))+struct.pack('<II',len(payload),kind)+payload+tail)
 assert not doc.get('skins') and all('bufferView' in image for image in doc['images'])
 report={'revision':revision,'masterSha256':digest(master)['sha256'],'portableBaselineSha256':digest(portable)['sha256'],'staticVisualAsset':True,'rigged':False,'physicsIntegrated':False,'bodyVertices':len(q),'mappedVertices':len(ids),'protectedVerticesUnchanged':int(np.count_nonzero(protected)),'uvUnchanged':True,'uvSha256':uv_before,'maximumMappingErrorMetres':float(max(distances)),'triangles':sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives'] if 'indices' in p),'files':{p.name:digest(p) for p in (pbr,glb)}}
 (out/'portable-manifest.json').write_text(json.dumps(report,indent=2));print('ART011_PORTABLE_PASS',flush=True)

def review(out):
 bpy.ops.wm.open_mainfile(filepath=str(out/'Character01_PBR011.blend'))
 for o in list(bpy.data.objects):
  if o.type=='MESH' and not o.name.startswith('STUDIO'):bpy.data.objects.remove(o,do_unlink=True)
 bpy.ops.import_scene.gltf(filepath=str(out/'Character01_Visual011.glb'))
 assert any(o.name.startswith('Loose over-trapezius panel') for o in bpy.context.scene.objects)
 dst=out/'reimport';dst.mkdir(exist_ok=True);render(dst,'three-quarter,torso',900,32)
 (out/'reimport.json').write_text(json.dumps({'actualGlbReimported':True,'rendered':True}));print('ART011_REIMPORT_PASS',flush=True)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--master',type=Path);ap.add_argument('--portable',type=Path);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--review',action='store_true');a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
 if a.review:review(out)
 else:export(a.master.resolve(),a.portable.resolve(),out)
if __name__=='__main__':main()
