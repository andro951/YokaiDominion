"""Portable PBR export of the saved visual master. No rig or physics is invented."""
from __future__ import annotations
import argparse,hashlib,json,re,struct,sys,shutil,time
from pathlib import Path
import bpy
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import portable_geometry009
prepare_body=portable_geometry009.prepare_body

def select_only(o):
 bpy.ops.object.select_all(action='DESELECT');o.hide_set(False);o.hide_viewport=False;o.select_set(True);bpy.context.view_layer.objects.active=o

def bake_set(obj,materials,label,out,resolution,high=None):
 images={};scene=bpy.context.scene
 for kind in ('BaseColor','Normal','Roughness'):
  select_only(obj);selected_to_active=high is not None
  if high:
   high.hide_render=False;high.hide_set(False);high.select_set(True)
  scene.render.bake.use_selected_to_active=selected_to_active;scene.render.bake.use_cage=False
  scene.render.bake.cage_extrusion=.008;scene.render.bake.max_ray_distance=.015
  image=bpy.data.images.new(label+'_'+kind,width=resolution,height=resolution,alpha=False)
  if kind!='BaseColor':image.colorspace_settings.name='Non-Color'
  restore=[];temp=[]
  for m in materials:
   nodes=m.node_tree.nodes;links=m.node_tree.links;bs=nodes.get('Principled BSDF');output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
   target=nodes.new('ShaderNodeTexImage');target.image=image;nodes.active=target;target.select=True;temp.append((m,target))
   if kind=='BaseColor':
    old=[link.from_socket for link in output.inputs['Surface'].links];emit=nodes.new('ShaderNodeEmission')
    if bs.inputs['Base Color'].is_linked:links.new(bs.inputs['Base Color'].links[0].from_socket,emit.inputs['Color'])
    else:emit.inputs['Color'].default_value=bs.inputs['Base Color'].default_value
    links.new(emit.outputs[0],output.inputs['Surface']);restore.append((m,output,old,emit))
  print('BAKE_BEGIN',label,kind,resolution,time.time(),flush=True)
  bpy.ops.object.bake(type={'BaseColor':'EMIT','Normal':'NORMAL','Roughness':'ROUGHNESS'}[kind],margin=16,use_clear=True,normal_space='TANGENT',use_selected_to_active=selected_to_active,use_cage=False,cage_extrusion=.008,max_ray_distance=.015)
  for m,output,old,emit in restore:
   for link in list(output.inputs['Surface'].links):m.node_tree.links.remove(link)
   for socket in old:m.node_tree.links.new(socket,output.inputs['Surface'])
   m.node_tree.nodes.remove(emit)
  for m,target in temp:m.node_tree.nodes.remove(target)
  image.filepath_raw=str(out/'textures'/(label+'_'+kind+'.png'));image.file_format='PNG';image.save();image.pack();images[kind]=image
  print('BAKED',label,kind,time.time(),flush=True)
 if high:high.hide_render=True;high.hide_set(True)
 scene.render.bake.use_selected_to_active=False
 return images

def coverage(body,image):
 uv=body.data.uv_layers.active;u=np.empty(len(uv.data)*2);uv.data.foreach_get('uv',u);u=u.reshape(-1,2)
 centers=np.array([u[list(p.loop_indices)].mean(0) for p in body.data.polygons]);w,h=image.size
 pixels=np.empty(w*h*4,dtype=np.float32);image.pixels.foreach_get(pixels);pixels=pixels.reshape(h,w,4)
 x=np.clip((centers[:,0]*w).astype(int),0,w-1);y=np.clip((centers[:,1]*h).astype(int),0,h-1)
 fraction=float(np.mean(pixels[y,x,:3].max(1)<.001))
 if fraction>.005:raise RuntimeError(f'Black/unbaked body coverage {fraction:.3%}')
 return {'sampledFaces':len(centers),'unbakedFraction':fraction,'threshold':.005}

def pbr_material(name,images):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF')
 for kind,image in images.items():
  node=n.new('ShaderNodeTexImage');node.image=image;node.label=kind
  if kind=='Normal':
   normal=n.new('ShaderNodeNormalMap');normal.space='TANGENT';l.new(node.outputs['Color'],normal.inputs['Color']);l.new(normal.outputs['Normal'],bs.inputs['Normal'])
  else:l.new(node.outputs['Color'],bs.inputs['Base Color' if kind=='BaseColor' else 'Roughness'])
 return m

def plane_for(material):
 bpy.ops.mesh.primitive_plane_add(size=1,location=(10,0,0));p=bpy.context.object;p.name='BAKE_HELPER';p.data.materials.append(material)
 names=[n.uv_map for n in material.node_tree.nodes if n.type=='UVMAP' and n.uv_map]
 if names:p.data.uv_layers[0].name=names[0]
 return p

def glb_document(path):
 data=path.read_bytes();magic,version,size=struct.unpack_from('<III',data);assert magic==0x46546C67 and version==2 and size==len(data)
 length,kind=struct.unpack_from('<II',data,12);assert kind==0x4E4F534A
 doc=json.loads(data[20:20+length]);tail=data[20+length:]
 for mat in doc.get('materials',[]):
  if mat.get('name','').startswith('Hair008'):
   mat['alphaMode']='MASK';mat['alphaCutoff']=.30;mat['doubleSided']=True
 payload=json.dumps(doc,separators=(',',':')).encode();payload+=b' '*((-len(payload))%4)
 path.write_bytes(struct.pack('<III',magic,2,20+len(payload)+len(tail))+struct.pack('<II',len(payload),kind)+payload+tail)
 return doc

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--resolution',type=int,default=4096)
 a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=a.out.resolve();(out/'textures').mkdir(parents=True,exist_ok=True)
 bpy.ops.wm.open_mainfile(filepath=str(a.source.resolve()));scene=bpy.context.scene
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.bake.use_selected_to_active=False
 objects=[o for o in scene.objects if o.type=='MESH' and not o.hide_render and not o.name.startswith('STUDIO')]
 original=bpy.data.objects.get('Body');assert original in objects and original.get('finish008_applied')
 body,high,uv_report=prepare_body(original);objects.remove(high);objects.append(body)
 images=bake_set(body,list(body.data.materials),'Body',out,a.resolution,high);coverage_report=coverage(body,images['BaseColor'])
 mat=pbr_material('Body_PBR',images);body.data.materials.clear();body.data.materials.append(mat)
 for f in body.data.polygons:f.material_index=0
 for o in objects:
  for mod in o.modifiers:
   if mod.type=='SUBSURF':mod.levels=mod.render_levels=0
 materials=sorted({m for o in objects if o!=body for m in o.data.materials if m},key=lambda m:m.name)
 for m in materials:
  if not m.use_nodes:continue
  if m.get('portable_pbr_ready'):
   for node in m.node_tree.nodes:
    if node.type=='TEX_IMAGE' and node.image:
     image=node.image;dest=out/'textures'/(re.sub('[^A-Za-z0-9]+','_',image.name)+'.png')
     if image.packed_file:dest.write_bytes(image.packed_file.data)
     else:image.filepath_raw=str(dest);image.file_format='PNG';image.save()
   continue
  bs=m.node_tree.nodes.get('Principled BSDF')
  if not bs or any(n.type in {'VERTEX_COLOR','ATTRIBUTE'} for n in m.node_tree.nodes):continue
  if not any(bs.inputs[s].is_linked for s in ('Base Color','Normal','Roughness')):continue
  label=re.sub('[^A-Za-z0-9]+','_',m.name).strip('_')[:55]
  helper=plane_for(m);tiles=bake_set(helper,[m],label,out,1024);bpy.data.objects.remove(helper,do_unlink=True);new=pbr_material(label+'_PBR',tiles)
  new.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value=bs.inputs['Metallic'].default_value
  for o in objects:
   for j,old in enumerate(o.data.materials):
    if old==m:o.data.materials[j]=new
  for o in objects:
   if new in list(o.data.materials) and o.data.uv_layers.get('StrandUV'):
    for uv in list(o.data.uv_layers):
     if uv.name!='StrandUV':o.data.uv_layers.remove(uv)
    o.data.uv_layers.active=o.data.uv_layers['StrandUV'];o.data.uv_layers['StrandUV'].active_render=True
 for o in objects:
  if not o.data.uv_layers:
   select_only(o);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
  if not all(len(p.vertices)==3 for p in o.data.polygons):
   tri=o.modifiers.new('Portable triangulation','TRIANGULATE');tri.keep_custom_normals=True
 bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0;body['export_status']='Static visual asset; rig/physics refit and production LOD are not implied'
 pbr=out/'Character01_PBR008.blend';bpy.ops.wm.save_as_mainfile(filepath=str(pbr),compress=True)
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.hide_set(False);o.select_set(True)
 bpy.context.view_layer.objects.active=body;glb=out/'Character01_Visual008.glb'
 bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_texcoords=True,export_normals=True,export_tangents=True,export_materials='EXPORT',export_vertex_color='MATERIAL',export_animations=False,export_skins=False,export_morph=False,export_cameras=False,export_lights=False,export_extras=True)
 doc=glb_document(glb);assert doc.get('meshes') and len(doc.get('images',[]))>=3
 report={'sourceSha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),'staticVisualAsset':True,'rigged':False,'runtimePhysicsIntegrated':False,'uvAtlas':uv_report,'bodyBakeCoverage':coverage_report,'materials':len(doc.get('materials',[])),'meshes':len(doc['meshes']),'images':len(doc.get('images',[])),'triangles':sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives'] if 'indices' in p),'files':{}}
 for f in sorted(out.rglob('*')):
  if f.is_file() and f.suffix in ('.blend','.glb','.png'):
   assert f.stat().st_size<99_000_000,(f,'exceeds conservative ordinary-Git file limit')
   report['files'][str(f.relative_to(out))]={'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 (out/'portable-manifest.json').write_text(json.dumps(report,indent=2))
 shutil.copy2(__file__,out/'export008.py');shutil.copy2(portable_geometry009.__file__,out/'portable_geometry009.py');print('ART008_PORTABLE_EXPORT_PASS',flush=True)
if __name__=='__main__':main()
