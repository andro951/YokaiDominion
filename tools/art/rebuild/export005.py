"""Bake portable visual assets; this does not claim a new rig or calibrated tissue integration."""
from __future__ import annotations
import bpy,sys,argparse,json,hashlib,math
from pathlib import Path
import numpy as np

def active(o):
    bpy.ops.object.select_all(action='DESELECT');o.hide_set(False);o.select_set(True);bpy.context.view_layer.objects.active=o

def uv_if_missing(o):
    if o.data.uv_layers:return
    co=np.array([v.co[:] for v in o.data.vertices]);extent=np.ptp(co,axis=0);axes=np.argsort(extent)[-2:];uv=o.data.uv_layers.new(name='UVMap')
    lo=co[:,axes].min(0);span=np.maximum(co[:,axes].max(0)-lo,1e-9)
    for loop in o.data.loops:uv.data[loop.index].uv=(co[loop.vertex_index,axes]-lo)/span

def bake_channel(o,name,size,out,channel='Base Color',normal=False):
    active(o);uv_if_missing(o);image=bpy.data.images.new(name,width=size,height=size,alpha=False,float_buffer=False)
    image.colorspace_settings.name='Non-Color' if normal or channel=='Roughness' else 'sRGB';image.generated_color=(.5,.5,1,1) if normal else (0,0,0,1)
    backups=[];mats=list(dict.fromkeys(m for m in o.data.materials if m))
    for m in mats:
        nodes=m.node_tree.nodes;links=m.node_tree.links;tex=nodes.new('ShaderNodeTexImage');tex.image=image;nodes.active=tex
        output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output);orig=output.inputs['Surface'].links[0].from_socket if output.inputs['Surface'].links else None;emission=None
        if not normal:
            bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');src=bs.inputs[channel];emission=nodes.new('ShaderNodeEmission')
            if src.links:links.new(src.links[0].from_socket,emission.inputs['Color'])
            elif channel=='Roughness':emission.inputs['Color'].default_value=(src.default_value,)*3+(1,)
            else:emission.inputs['Color'].default_value=src.default_value
            links.new(emission.outputs['Emission'],output.inputs['Surface'])
        backups.append((m,tex,emission,orig,output))
    bpy.context.scene.render.bake.use_selected_to_active=False;bpy.context.scene.render.bake.margin=16;bpy.ops.object.bake(type='NORMAL' if normal else 'EMIT')
    image.filepath_raw=str(out/(name+'.png'));image.file_format='PNG';image.save();image.pack()
    for m,tex,emission,orig,output in backups:
        if orig:m.node_tree.links.new(orig,output.inputs['Surface'])
        if emission:m.node_tree.nodes.remove(emission)
        m.node_tree.nodes.remove(tex)
    return image

def pbr(name,color,rough=.5,normal=None,roughmap=None):
    m=bpy.data.materials.new(name);m.use_nodes=True;nodes=m.node_tree.nodes;links=m.node_tree.links;bs=nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=rough
    if isinstance(color,bpy.types.Image):
        t=nodes.new('ShaderNodeTexImage');t.image=color;links.new(t.outputs['Color'],bs.inputs['Base Color'])
    else:bs.inputs['Base Color'].default_value=color
    if normal:
        t=nodes.new('ShaderNodeTexImage');t.image=normal;n=nodes.new('ShaderNodeNormalMap');links.new(t.outputs['Color'],n.inputs['Color']);links.new(n.outputs['Normal'],bs.inputs['Normal'])
    if roughmap:
        t=nodes.new('ShaderNodeTexImage');t.image=roughmap;links.new(t.outputs['Color'],bs.inputs['Roughness'])
    return m

def replace_material_everywhere(old,new):
    for o in bpy.data.objects:
        if o.type=='MESH':
            for slot in o.material_slots:
                if slot.material==old:slot.material=new

def bake_flat_material(material,name,size,out):
    bpy.ops.mesh.primitive_plane_add(size=1,location=(0,0,-100));o=bpy.context.object;o.name='BAKE temporary '+name;o.data.materials.append(material)
    albedo=bake_channel(o,name+'_BaseColor',size,out);normal=bake_channel(o,name+'_Normal',size,out,normal=True);bpy.data.objects.remove(o,do_unlink=True)
    return albedo,normal

def group_for(o):
    n=o.name
    if n=='Body':return 'Body'
    m=o.active_material.name if o.active_material else ''
    if 'hair' in n.lower() or 'wave' in n.lower() or 'mane' in n.lower() or 'sweep' in n.lower():return 'Hair'
    if m.startswith('Cloth') or m.startswith('Clothing'):return 'Clothing'
    if 'cord' in n.lower() or 'knot' in n.lower():return 'WaistCord'
    if n.startswith(('Horn','Tail')):return 'HornsAndTail'
    if n.startswith(('Eye.','Iris.')):return 'Eyes'
    if n.startswith(('Brow','Upper liner','Outer eyelash','Canine','Neck selvedge')):return 'FaceAndSeams'
    return 'Details'

def export_lod(objects,out,name,ratios):
    copies=[];groups={}
    for o in objects:
        c=o.copy();c.data=o.data.copy();c.name=o.name+'__export';bpy.context.collection.objects.link(c);c.hide_render=False;active(c)
        for mod in list(c.modifiers):
            try:bpy.ops.object.modifier_apply(modifier=mod.name)
            except RuntimeError:raise RuntimeError('Could not apply '+mod.name+' on '+o.name)
        uv_if_missing(c);ratio=ratios.get(group_for(o),.6)
        if ratio<1 and len(c.data.polygons)>250:
            mod=c.modifiers.new('Export budget','DECIMATE');mod.ratio=ratio;bpy.ops.object.modifier_apply(modifier=mod.name)
        for a in list(c.data.color_attributes):c.data.color_attributes.remove(a)
        groups.setdefault(group_for(o),[]).append(c);copies.append(c)
    merged=[]
    for group,items in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for c in items:c.select_set(True)
        bpy.context.view_layer.objects.active=items[0]
        if len(items)>1:bpy.ops.object.join()
        o=items[0];o.name=group;merged.append(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in merged:o.select_set(True)
    bpy.context.view_layer.objects.active=merged[0]
    kwargs=dict(filepath=str(out/(name+'.glb')),export_format='GLB',use_selection=True,export_apply=False,export_animations=False,export_skins=False,export_morph=False,export_texcoords=True,export_normals=True,export_tangents=True,export_cameras=False,export_lights=False)
    props=bpy.ops.export_scene.gltf.get_rna_type().properties
    if 'export_vertex_color' in props:kwargs['export_vertex_color']='NONE'
    bpy.ops.export_scene.gltf(**kwargs)
    stats={'file':name+'.glb','parts':[],'triangles':0,'vertices':0,'rigged':False}
    for o in merged:
        o.data.calc_loop_triangles();tri=len(o.data.loop_triangles);ver=len(o.data.vertices);stats['parts'].append({'name':o.name,'vertices':ver,'triangles':tri});stats['triangles']+=tri;stats['vertices']+=ver
    for o in merged:bpy.data.objects.remove(o,do_unlink=True)
    return stats

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--out',type=Path,required=True);args=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True);tex=out/'textures';tex.mkdir(exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(args.input.resolve()));sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=4;body=bpy.data.objects['Body']
    albedo=bake_channel(body,'Body_BaseColor',2048,tex);normal=bake_channel(body,'Body_Normal',2048,tex,normal=True);rough=bake_channel(body,'Body_Roughness',1024,tex,channel='Roughness')
    bodymat=pbr('Body | baked PBR',albedo,.48,normal,rough);bs=bodymat.node_tree.nodes.get('Principled BSDF');bs.inputs['Subsurface Weight'].default_value=.045;bs.inputs['Subsurface Scale'].default_value=.0015;bs.inputs['Subsurface Radius'].default_value=(1,.5,.25)
    body.data.materials.clear();body.data.materials.append(bodymat)
    for f in body.data.polygons:f.material_index=0
    for oldname,label,roughness in [('Hair | ivory silver','Hair',.46),('Cloth | warm ivory','Clothing',.77)]:
        old=bpy.data.materials.get(oldname)
        if old:
            bc,no=bake_flat_material(old,label,1024,tex);mat=pbr(label+' | baked PBR',bc,roughness,no);replace_material_everywhere(old,mat)
    for o in list(bpy.data.objects):
        if o.type=='MESH' and o.name.startswith('Iris.'):
            uv_if_missing(o);bc=bake_channel(o,o.name.replace('.','_')+'_BaseColor',512,tex);m=pbr('Iris | baked '+o.name,bc,.16);m.node_tree.nodes.get('Principled BSDF').inputs['Coat Weight'].default_value=.4;o.data.materials.clear();o.data.materials.append(m)
    objects=[o for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith(('STUDIO','BAKE'))]
    for o in objects:uv_if_missing(o)
    sc.cycles.samples=48
    from mathutils import Vector
    cam=sc.camera;cam.location=(3.3,-6,2.15);cam.rotation_euler=(Vector((0,0,1.12))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.52
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'Character01_TexturedMaster.blend'),compress=True)
    stats=[]
    for label,r in [('Character01_LOD0',{'Body':.24,'Hair':.30,'Clothing':.25,'WaistCord':.30,'HornsAndTail':.65,'Eyes':.65,'FaceAndSeams':.6}),('Character01_LOD1',{'Body':.12,'Hair':.15,'Clothing':.12,'WaistCord':.15,'HornsAndTail':.35,'Eyes':.4,'FaceAndSeams':.35})]:stats.append(export_lod(objects,out,label,r))
    manifest={'revision':'005','scope':'anatomical visual-art rebuild','units':'metres','source_height':1.95,'runtime_rig_and_tissue_refit':False,'models':stats,'textures':[x.name for x in tex.glob('*.png')],'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*') if p.is_file()}}
    (out/'asset-manifest.json').write_text(json.dumps(manifest,indent=2));print('CHARACTER_VISUAL_EXPORT_COMPLETE',json.dumps(manifest))

if __name__=='__main__':main()
