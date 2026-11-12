"""Portable static Art012 export. Baked vertex albedo preserves procedural markings.
The untouched master remains authoritative. No rig/physics or production-LOD acceptance.
"""
from pathlib import Path
import argparse,sys,json,hashlib,struct
import bpy,numpy as np

def select(o):
 bpy.ops.object.select_all(action='DESELECT');o.hide_set(False);o.hide_render=False;o.select_set(True);bpy.context.view_layer.objects.active=o

def digest(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def run(master,portable,out):
 bpy.ops.wm.open_mainfile(filepath=str(portable))
 clothmat=bpy.data.objects['Loose over-trapezius panel L'].data.materials[0]
 for name in ['Body','Body_SculptSource','Loose over-trapezius panel L','Loose over-trapezius panel R']:
  if name in bpy.data.objects:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
 with bpy.data.libraries.load(str(master),link=False) as (src,dst):dst.objects=['Body','Loose over-trapezius panel L','Loose over-trapezius panel R']
 for o in dst.objects:
  assert o is not None;bpy.context.scene.collection.objects.link(o);o.hide_set(False);o.hide_render=False
 body=bpy.data.objects['Body'];highcount=len(body.data.vertices);select(body)
 dec=body.modifiers.new('Portable static surface reduction','DECIMATE');dec.ratio=.22;dec.use_collapse_triangulate=True
 bpy.ops.object.modifier_apply(modifier=dec.name)
 for p in body.data.polygons:p.use_smooth=True
 print('BODY_REDUCED',highcount,len(body.data.vertices),flush=True)
 # Bake actual procedural albedo, not scene lighting, into exportable vertex data.
 col=body.data.color_attributes.new(name='Albedo012',type='FLOAT_COLOR',domain='CORNER')
 body.data.color_attributes.active_color=col
 body.data.color_attributes.render_color_index=list(body.data.color_attributes).index(col)
 for index,material in enumerate(body.data.materials):
  if material is None:body.data.materials[index]=body.data.materials[0]
 for material in set(body.data.materials):
  material.use_nodes=True;nodes=material.node_tree.nodes;links=material.node_tree.links
  outnode=next(n for n in nodes if n.type=='OUTPUT_MATERIAL');bsdf=next((n for n in nodes if n.type=='BSDF_PRINCIPLED'),None)
  emission=nodes.new('ShaderNodeEmission')
  if bsdf and bsdf.inputs['Base Color'].is_linked:links.new(bsdf.inputs['Base Color'].links[0].from_socket,emission.inputs['Color'])
  elif bsdf:emission.inputs['Color'].default_value=bsdf.inputs['Base Color'].default_value
  links.new(emission.outputs[0],outnode.inputs['Surface'])
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1
 scene.render.bake.target='VERTEX_COLORS';scene.render.bake.use_selected_to_active=False
 scene.render.threads_mode='FIXED';scene.render.threads=4
 bpy.ops.object.bake(type='EMIT')
 data=np.empty(len(col.data)*4);col.data.foreach_get('color',data);data=data.reshape(-1,4)
 assert np.isfinite(data).all() and np.max(data[:,:3])>.05
 print('ALBEDO_BAKED',data.shape,np.quantile(data[:,:3],[0,.5,1],axis=0).tolist(),flush=True)
 mat=bpy.data.materials.new('Skin | Art012 baked vertex albedo');mat.use_nodes=True
 nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes.get('Principled BSDF');attr=nodes.new('ShaderNodeVertexColor');attr.layer_name='Albedo012'
 links.new(attr.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.52;bs.inputs['Metallic'].default_value=0;bs.inputs['IOR'].default_value=1.4
 body.data.materials.clear();body.data.materials.append(mat)
 for p in body.data.polygons:p.material_index=0
 for a in list(body.data.attributes):
  if not a.is_required and a.name!='Albedo012' and not a.name.startswith('.'):
   body.data.attributes.remove(a)
 for name in ['Loose over-trapezius panel L','Loose over-trapezius panel R']:
  o=bpy.data.objects[name];o.data.materials.clear();o.data.materials.append(clothmat)
  for m in o.modifiers:
   if m.type=='SUBSURF':m.levels=1;m.render_levels=1
 visible=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render and not o.name.startswith('STUDIO')]
 for o in list(bpy.data.objects):
  if o.type=='MESH' and o.hide_render:bpy.data.objects.remove(o,do_unlink=True)
 bpy.ops.outliner.orphans_purge(do_local_ids=True,do_linked_ids=False,do_recursive=True)
 bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0
 pbr=out/'Character01_PBR012.blend';bpy.ops.wm.save_as_mainfile(filepath=str(pbr),compress=True)
 bpy.ops.object.select_all(action='DESELECT')
 for o in visible:o.hide_set(False);o.select_set(True)
 bpy.context.view_layer.objects.active=body;glb=out/'Character01_Visual012.glb'
 bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_texcoords=True,export_normals=True,export_tangents=True,export_materials='EXPORT',export_vertex_color='MATERIAL',export_animations=False,export_skins=False,export_morph=False,export_cameras=False,export_lights=False,export_extras=True)
 blob=glb.read_bytes();magic,version,size=struct.unpack_from('<III',blob);length,kind=struct.unpack_from('<II',blob,12);doc=json.loads(blob[20:20+length]);tail=blob[20+length:]
 for m in doc.get('materials',[]):
  if m.get('name','').startswith('Hair008'):m['alphaMode']='MASK';m['alphaCutoff']=.30;m['doubleSided']=True
 payload=json.dumps(doc,separators=(',',':')).encode();payload+=b' '*((-len(payload))%4);glb.write_bytes(struct.pack('<III',magic,2,20+len(payload)+len(tail))+struct.pack('<II',len(payload),kind)+payload+tail)
 assert any('COLOR_0' in p['attributes'] for m in doc['meshes'] for p in m['primitives'])
 assert not doc.get('skins') and not doc.get('animations') and all('bufferView' in i for i in doc.get('images',[]))
 report={'masterSha256':digest(master)['sha256'],'staticVisualAsset':True,'rigged':False,'physicsIntegrated':False,'skinRepresentation':'unlit-albedo bake to vertex colors, with normally lit PBR material; no pores/SSS bake','sourceBodyVertices':highcount,'portableBodyVertices':len(body.data.vertices),'triangleCount':sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives'] if 'indices' in p),'materials':len(doc['materials']),'embeddedImages':len(doc.get('images',[])),'files':{p.name:digest(p) for p in (pbr,glb)}}
 (out/'portable-manifest.json').write_text(json.dumps(report,indent=2));print('ART012_PORTABLE_PASS',flush=True)

def review(out):
 bpy.ops.wm.open_mainfile(filepath=str(out/'Character01_PBR012.blend'))
 for o in list(bpy.data.objects):
  if o.type=='MESH' and not o.name.startswith('STUDIO'):bpy.data.objects.remove(o,do_unlink=True)
 bpy.ops.import_scene.gltf(filepath=str(out/'Character01_Visual012.glb'))
 f=out/'Reimport012.blend';bpy.ops.wm.save_as_mainfile(filepath=str(f),compress=True)
 sys.path.insert(0,str(Path(__file__).resolve().parent));from review012 import render
 render(f,out/'reimport','front,quarter,side',720,24)
 (out/'reimport.json').write_text(json.dumps({'actualGlbReimported':True,'rendered':True}));print('ART012_REIMPORT_PASS',flush=True)

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--master',type=Path);a.add_argument('--portable',type=Path);a.add_argument('--out',type=Path,required=True);a.add_argument('--review',action='store_true');args=a.parse_args(sys.argv[sys.argv.index('--')+1:]);out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
 if args.review:review(out)
 else:run(args.master.resolve(),args.portable.resolve(),out)
