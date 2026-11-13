"""Transfer the actual reviewed face displacement, including fairing, to PBR013.
Does not resculpt the body, regenerate hair/cloth, or alter baked color attributes.
"""
from pathlib import Path
import argparse,hashlib,json,struct,sys
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from face014 import positions,write,deform

def digest(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def colors(body):
 a=body.data.color_attributes.get('Albedo012');assert a is not None
 p=np.empty(len(a.data)*4);a.data.foreach_get('color',p);return hashlib.sha256(p.tobytes()).hexdigest()
def run(master,portable,out):
 bpy.ops.wm.open_mainfile(filepath=str(master));high=bpy.data.objects['Body'];revision=high['art014'];new=positions(high)
 old=np.empty(new.size);high.data.attributes['art014_previous_position'].data.foreach_get('vector',old);old=old.reshape(-1,3);delta=new-old
 high.data.calc_loop_triangles();tri=np.empty(len(high.data.loop_triangles)*3,dtype=np.int32);high.data.loop_triangles.foreach_get('vertices',tri);tri=tri.reshape(-1,3)
 near=(old[:,2]>1.66)&(old[:,2]<1.87)&(abs(old[:,0])<.14)&(old[:,1]<.04)
 keep=np.all(near[tri],axis=1);tri=tri[keep];ix=np.unique(tri);lookup=np.full(len(old),-1,dtype=np.int32);lookup[ix]=np.arange(len(ix));local=lookup[tri]
 original=old[ix].copy();changes=delta[ix].copy();tree=BVHTree.FromPolygons([Vector(v) for v in original],local.tolist(),all_triangles=True)
 del old,new,delta,tri,lookup
 bpy.ops.wm.open_mainfile(filepath=str(portable));body=bpy.data.objects['Body'];assert not body.get('art014'),'Already processed'
 p=positions(body);q=p.copy();color_before=colors(body);_,gate=deform(p);ids=np.flatnonzero(gate>0);errors=[]
 for i in ids:
  hit,normal,index,distance=tree.find_nearest(Vector(p[i]));assert index is not None
  errors.append(distance);ids3=local[index];a,b,c=original[ids3];u=b-a;v=c-a;w=np.asarray(hit)-a;uu=u@u;uv=u@v;vv=v@v;d=uu*vv-uv*uv
  if abs(d)<1e-20:weights=np.array([1.,0,0])
  else:
   s=(vv*(w@u)-uv*(w@v))/d;t=(uu*(w@v)-uv*(w@u))/d;weights=np.array([1-s-t,s,t])
  q[i]+=weights@changes[ids3]
 assert max(errors)<.012,'Unexpected source mapping error'
 assert np.array_equal(q[gate==0],p[gate==0]);write(body,q);body['art014']=revision
 assert colors(body)==color_before
 objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render and not o.name.startswith('STUDIO')]
 bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0;pbr=out/'Character01_PBR014.blend';bpy.ops.wm.save_as_mainfile(filepath=str(pbr),compress=True)
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.hide_set(False);o.select_set(True)
 bpy.context.view_layer.objects.active=body;glb=out/'Character01_Visual014.glb'
 bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_texcoords=True,export_normals=True,export_tangents=True,export_materials='EXPORT',export_vertex_color='MATERIAL',export_animations=False,export_skins=False,export_morph=False,export_cameras=False,export_lights=False,export_extras=True)
 blob=glb.read_bytes();magic,version,size=struct.unpack_from('<III',blob);assert magic==0x46546c67 and version==2 and size==len(blob)
 length,kind=struct.unpack_from('<II',blob,12);doc=json.loads(blob[20:20+length]);tail=blob[20+length:]
 for m in doc.get('materials',[]):
  if m.get('name','').startswith('Hair008'):m['alphaMode']='MASK';m['alphaCutoff']=.30;m['doubleSided']=True
 data=json.dumps(doc,separators=(',',':')).encode();data+=b' '*((-len(data))%4)
 glb.write_bytes(struct.pack('<III',magic,2,20+len(data)+len(tail))+struct.pack('<II',len(data),kind)+data+tail)
 assert all('bufferView' in i for i in doc.get('images',[])) and not doc.get('skins') and not doc.get('animations')
 report={'revision':revision,'masterSha256':digest(master)['sha256'],'portableBaselineSha256':digest(portable)['sha256'],'bakedSkinColorsUnchanged':True,'skinColorSha256':color_before,'bodyVertices':len(q),'mappedFacialVertices':len(ids),'protectedBodyVerticesUnchanged':int(np.count_nonzero(gate==0)),'maximumSurfaceMappingErrorMetres':float(max(errors)),'triangleCount':sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives'] if 'indices' in p),'otherObjectsUnchanged':True,'staticVisualOnly':True,'rigged':False,'physicsIntegrated':False,'files':{p.name:digest(p) for p in (pbr,glb)}}
 bpy.ops.wm.open_mainfile(filepath=str(pbr));assert bpy.data.objects['Body']['art014']==revision;report['savedBlendReopened']=True
 (out/'portable-manifest.json').write_text(json.dumps(report,indent=2));print('ART014_PORTABLE_PASS',flush=True)
def review(out):
 import review013
 review013.SHOTS.update({'face-front':((0,-3,1.808),(0,-.09,1.808),.34,1.,False),'face-quarter':((1.6,-3,1.82),(0,-.09,1.808),.36,1.,False),'face-side':((3,0,1.81),(0,-.075,1.808),.36,1.,False)})
 bpy.ops.wm.open_mainfile(filepath=str(out/'Character01_PBR014.blend'))
 for o in list(bpy.data.objects):
  if o.type=='MESH' and not o.name.startswith('STUDIO'):bpy.data.objects.remove(o,do_unlink=True)
 bpy.ops.import_scene.gltf(filepath=str(out/'Character01_Visual014.glb'))
 f=out/'Reimport014.blend';bpy.ops.wm.save_as_mainfile(filepath=str(f),compress=True)
 review013.render(f,out/'reimport','face-front,face-quarter,face-side',800,32)
 (out/'reimport.json').write_text(json.dumps({'actualGlbReimported':True,'rendered':True}));print('ART014_REIMPORT_PASS',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--master',type=Path);p.add_argument('--portable',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--review',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
 if a.review:review(out)
 else:run(a.master.resolve(),a.portable.resolve(),out)
