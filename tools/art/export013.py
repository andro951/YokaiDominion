"""Transfer the reviewed Art013 changes into the existing portable materials.
Preserves baked skin albedo and UVs; imports the actual corrected cloth mesh.
"""
from pathlib import Path
import argparse,hashlib,json,struct,sys
import bpy,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from finish013 import deform,positions,set_positions,REVISION
from review013 import render

def digest(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def colors(body):
 a=body.data.color_attributes.get('Albedo012')
 if a is None:raise ValueError('Wrong portable baseline: no baked albedo')
 p=np.empty(len(a.data)*4);a.data.foreach_get('color',p);return hashlib.sha256(p.tobytes()).hexdigest()
def run(master,portable,out):
 bpy.ops.wm.open_mainfile(filepath=str(portable));body=bpy.data.objects['Body']
 if body.get('art013'):raise ValueError('Already processed')
 before=positions(body);c=colors(body);set_positions(body,deform(before));body['art013']=REVISION
 assert colors(body)==c
 names=['Loose over-trapezius panel L','Loose over-trapezius panel R']
 mat=bpy.data.objects[names[0]].data.materials[0]
 for name in names:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
 with bpy.data.libraries.load(str(master),link=False) as (src,dst):dst.objects=names
 for o in dst.objects:
  if o is None or o.get('art013')!=REVISION:raise ValueError('Wrong master cloth revision')
  bpy.context.scene.collection.objects.link(o);o.hide_set(False);o.hide_render=False
  o.data.materials.clear();o.data.materials.append(mat)
  for m in o.modifiers:
   if m.type=='SUBSURF':m.levels=1;m.render_levels=1
 objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render and not o.name.startswith('STUDIO')]
 bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0
 pbr=out/'Character01_PBR013.blend';bpy.ops.wm.save_as_mainfile(filepath=str(pbr),compress=True)
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.hide_set(False);o.select_set(True)
 bpy.context.view_layer.objects.active=body;glb=out/'Character01_Visual013.glb'
 bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_texcoords=True,export_normals=True,export_tangents=True,export_materials='EXPORT',export_vertex_color='MATERIAL',export_animations=False,export_skins=False,export_morph=False,export_cameras=False,export_lights=False,export_extras=True)
 blob=glb.read_bytes();magic,version,size=struct.unpack_from('<III',blob);assert magic==0x46546c67 and version==2 and size==len(blob)
 length,kind=struct.unpack_from('<II',blob,12);doc=json.loads(blob[20:20+length]);tail=blob[20+length:]
 for m in doc.get('materials',[]):
  if m.get('name','').startswith('Hair008'):m['alphaMode']='MASK';m['alphaCutoff']=.30;m['doubleSided']=True
 data=json.dumps(doc,separators=(',',':')).encode();data+=b' '*((-len(data))%4)
 glb.write_bytes(struct.pack('<III',magic,2,20+len(data)+len(tail))+struct.pack('<II',len(data),kind)+data+tail)
 assert all('bufferView' in i for i in doc.get('images',[])) and not doc.get('skins') and not doc.get('animations')
 report={'revision':REVISION,'masterSha256':digest(master)['sha256'],'portableBaselineSha256':digest(portable)['sha256'],'bakedSkinColorsUnchanged':True,'skinColorSha256':c,'bodyVertices':len(body.data.vertices),'triangleCount':sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives'] if 'indices' in p),'staticVisualOnly':True,'rigged':False,'physicsIntegrated':False,'files':{p.name:digest(p) for p in (pbr,glb)}}
 bpy.ops.wm.open_mainfile(filepath=str(pbr));assert bpy.data.objects['Body']['art013']==REVISION;report['savedBlendReopened']=True
 (out/'portable-manifest.json').write_text(json.dumps(report,indent=2));print('ART013_PORTABLE_PASS',flush=True)
def review(out):
 bpy.ops.wm.open_mainfile(filepath=str(out/'Character01_PBR013.blend'))
 for o in list(bpy.data.objects):
  if o.type=='MESH' and not o.name.startswith('STUDIO'):bpy.data.objects.remove(o,do_unlink=True)
 bpy.ops.import_scene.gltf(filepath=str(out/'Character01_Visual013.glb'))
 f=out/'Reimport013.blend';bpy.ops.wm.save_as_mainfile(filepath=str(f),compress=True)
 render(f,out/'reimport','front,quarter,side',800,32)
 (out/'reimport.json').write_text(json.dumps({'actualGlbReimported':True,'rendered':True}));print('ART013_REIMPORT_PASS',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--master',type=Path);p.add_argument('--portable',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--review',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
 if a.review:review(out)
 else:run(a.master.resolve(),a.portable.resolve(),out)
