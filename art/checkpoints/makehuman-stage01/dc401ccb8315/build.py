"""Fresh MakeHuman/MPFB body study. Native controls only; no prior mesh imported.
Blender 4.5.3: --python build.py -- --vendor DIR --out DIR
"""
from pathlib import Path
import argparse, sys, json, hashlib, math, shutil
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
REVISION='makehuman-stage01-2'
MACROS=dict(gender=0.0,age=.56,muscle=.95,weight=.52,proportions=.60,height=.72,cupsize=1.0,firmness=.35,race={'asian':.65,'caucasian':.35,'african':0.0})
TARGETS={'buttocks/buttocks-volume-incr':.55,'stomach/stomach-tone-incr':.35,'torso/torso-muscle-dorsi-incr':.15}
for side in ['l','r']:
 TARGETS[f'legs/{side}-upperleg-scale-horiz-incr']=.25
 TARGETS[f'legs/{side}-upperleg-scale-depth-incr']=.25
 TARGETS[f'arms/{side}-upperarm-muscle-incr']=.30
 TARGETS[f'arms/{side}-upperarm-shoulder-muscle-incr']=.18
 TARGETS[f'arms/{side}-lowerarm-muscle-incr']=.18
PARTS=[('Eyes','eyes','high-poly'),('Eyebrows','eyebrows','eyebrow006'),('Eyelashes','eyelashes','eyelashes01'),('Hair','hair','elvs_hazel_hair')]

def digest(path):
 return {'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
def linear(c):
 a=np.array(c);return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
def coords(o):
 p=np.empty(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',p);return p.reshape(-1,3)
def simple_mat(name,color,rough=.5):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*linear(color),1);p.inputs['Roughness'].default_value=rough;return m

def skin(body,vendor,out):
 original=vendor/'assets/skins/young_caucasian_female2/young_lightskinned_female_diffuse2.png'
 image=bpy.data.images.load(str(original));a=np.empty(image.size[0]*image.size[1]*4,np.float32);image.pixels.foreach_get(a);a=a.reshape(-1,4)
 lum=a[:,:3]@np.array([.2126,.7152,.0722],np.float32);median=np.quantile(lum[lum>.08],.6)
 shade=np.clip(lum/max(median,1e-5),.08,1.5)**.65
 a[:,:3]=np.clip(shade[:,None]*linear((.76,.70,.82)),0,1);a[:,3]=1
 img=bpy.data.images.new('MakeHuman_Lavender_Diffuse',width=image.size[0],height=image.size[1]);img.pixels.foreach_set(a.ravel());img.filepath_raw=str(out/'LavenderSkin.png');img.file_format='PNG';img.save();img.pack()
 mat=simple_mat('MakeHuman | light lavender skin',(.76,.70,.82),.5);nodes=mat.node_tree.nodes;links=mat.node_tree.links;p=nodes.get('Principled BSDF');tex=nodes.new('ShaderNodeTexImage');tex.image=img;links.new(tex.outputs['Color'],p.inputs['Base Color'])
 p.inputs['Subsurface Weight'].default_value=.075;p.inputs['Subsurface Radius'].default_value=(.006,.003,.002)
 texco=nodes.new('ShaderNodeTexCoord');noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1800;noise.inputs['Detail'].default_value=2;links.new(texco.outputs['Object'],noise.inputs['Vector'])
 bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.14;bump.inputs['Distance'].default_value=.00009;links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],p.inputs['Normal'])
 body.data.materials.clear();body.data.materials.append(mat)
 return {'original':str(original.relative_to(vendor)),'originalSha256':digest(original)['sha256'],'paletteSrgb':[.76,.70,.82]}

def hair_and_brows():
 for o in bpy.data.objects:
  if o.type!='MESH' or not ('hazel' in o.name or 'eyebrow' in o.name):continue
  for mat in o.data.materials:
   if not mat or not mat.use_nodes:continue
   n=mat.node_tree.nodes;l=mat.node_tree.links;p=next((v for v in n if v.type=='BSDF_PRINCIPLED'),None)
   if p is None:continue
   col=p.inputs['Base Color'];old=col.links[0].from_socket if col.is_linked else None
   for link in list(col.links):l.remove(link)
   if old:
    bw=n.new('ShaderNodeRGBToBW');l.new(old,bw.inputs[0]);r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.05;r.color_ramp.elements[1].position=.8
    r.color_ramp.elements[0].color=(*linear((.30,.31,.34)),1);r.color_ramp.elements[1].color=(*linear((.92,.90,.85)),1)
    if 'eyebrow' in o.name:r.color_ramp.elements[0].color=(*linear((.31,.29,.35)),1);r.color_ramp.elements[1].color=(*linear((.68,.65,.72)),1)
    l.new(bw.outputs[0],r.inputs[0]);l.new(r.outputs[0],col)
   else:col.default_value=(*linear((.88,.86,.81)),1)
   p.inputs['Roughness'].default_value=.45

def coverage(body):
 """Review-only coverage built AFTER body; it does not deform or support anatomy."""
 dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);mesh=ev.to_mesh();p=np.array([v.co[:] for v in mesh.vertices]);polys=[list(f.vertices) for f in mesh.polygons];normals=np.array([v.normal[:] for v in mesh.vertices]);ev.to_mesh_clear()
 bvh=BVHTree.FromPolygons([Vector(v) for v in p],polys)
 mat=simple_mat('Temporary review coverage | ivory',(.80,.76,.68),.83)
 collection=bpy.data.collections.new('TEMPORARY_REVIEW_COVERAGE');bpy.context.scene.collection.children.link(collection)
 def obj(name,verts,faces):
  m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update();o=bpy.data.objects.new(name,m);collection.objects.link(o);m.materials.append(mat)
  for f in m.polygons:f.use_smooth=True
  s=o.modifiers.new('Soft edge','SUBSURF');s.levels=1;s.render_levels=2
  s=o.modifiers.new('Thin cloth','SOLIDIFY');s.thickness=.001;s.offset=0
  o['stage']='Temporary non-shaping coverage, not final outfit';return o
 for side in [-1,1]:
  verts=[];faces=[];rows=84;cols=18
  for i,z in enumerate(np.linspace(1.10,1.52,rows)):
   t=i/(rows-1);cx=np.interp(z,[1.10,1.22,1.30,1.40,1.52],[.07,.12,.122,.105,.082]);width=np.interp(z,[1.10,1.23,1.32,1.43,1.52],[.063,.055,.058,.047,.030])
   for j,u in enumerate(np.linspace(-1,1,cols)):
    x=side*(cx+width*u);hit,_,_,_=bvh.ray_cast(Vector((x,-2,z)),Vector((0,1,0)),3)
    yy=hit.y-.006 if hit is not None else -.11
    yy-=.0015*(1+math.cos(u*math.pi*2))*math.sin(math.pi*t)
    verts.append((x,yy,z))
    if i and j:
     k=i*cols+j;faces.append((k-cols-1,k-cols,k,k-1))
  obj('Review drape '+('L' if side>0 else 'R'),verts,faces)
 chosen=[]
 for f in polys:
  c=p[f].mean(0);x,y,z=c;low=.91+.10*min(1,abs(x)/.205)**1.8
  if low<z<1.10 and abs(x)<.30:chosen.append(f)
 used=sorted({v for f in chosen for v in f});remap={v:i for i,v in enumerate(used)}
 obj('Review lower cover',(p[used]+normals[used]*.003).tolist(),[[remap[v] for v in f] for f in chosen])
 return ['Review drape L','Review drape R','Review lower cover']

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--vendor',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);vendor=args.vendor.resolve();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
 root=out.parent/'extension-repo';root.mkdir(exist_ok=True);link=root/'mpfb'
 if not link.exists():link.symlink_to(vendor/'mpfb',target_is_directory=True)
 bpy.context.preferences.extensions.repos.new(name='MakeHumanStudy',module='makehuman_study',custom_directory=str(root))
 import addon_utils;addon_utils.enable('bl_ext.makehuman_study.mpfb',default_set=True,persistent=True)
 from bl_ext.makehuman_study.mpfb.services.humanservice import HumanService
 from bl_ext.makehuman_study.mpfb.services.targetservice import TargetService
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 b=HumanService.create_human(macro_detail_dict=MACROS);b.name='MakeHuman_Oni_Body'
 for target,weight in TARGETS.items():TargetService.load_target(b,str(vendor/'mpfb/data/targets'/(target+'.target.gz')),weight=weight)
 for part,sub,name in PARTS:HumanService.add_mhclo_asset(str(vendor/'assets'/sub/name/(name+'.mhclo')),b,asset_type=part,subdiv_levels=1,set_up_rigging=False)
 b['creation_method']='Official MakeHuman/MPFB native base plus macro and detail controls. New scene; no earlier character imported.';b['stage']=REVISION
 HumanService.serialize_to_json_file(b,str(out/'MakeHuman_Oni_Stage01.json'),save_clothes=True)
 macros={'macrodetails/Gender':'gender','macrodetails/Age':'age','macrodetails-universal/Muscle':'muscle','macrodetails-universal/Weight':'weight','macrodetails-proportions/BodyProportions':'proportions','macrodetails-height/Height':'height','breast/BreastSize':'cupsize','breast/BreastFirmness':'firmness'}
 mhm=['# MakeHuman character study. Native body parameters; see Blender for colored preview.','version v1.2.0','name Oni body study']
 for key,k in macros.items():mhm.append(f'modifier {key} {MACROS[k]:.6f}')
 for k,v in MACROS['race'].items():mhm.append(f'modifier macrodetails/{k.capitalize()} {v:.6f}')
 for key,value in TARGETS.items():
  key=key.removesuffix('-incr')+'-decr|incr';mhm.append(f'modifier {key} {value:.6f}')
 (out/'MakeHuman_Oni_Body.mhm').write_text('\n'.join(mhm)+'\n',encoding='utf-8')
 before=coords(b).copy();sub=b.modifiers.new('Anatomical subdivision','SUBSURF');sub.levels=1;sub.render_levels=2
 for f in b.data.polygons:f.use_smooth=True
 info=skin(b,vendor,out);hair_and_brows();covers=coverage(b);assert np.array_equal(before,coords(b))
 b['cloth_does_not_shape_body']=True
 bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0
 target=out/'MakeHuman_Oni_Stage01.blend';bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
 bpy.ops.wm.open_mainfile(filepath=str(target));assert bpy.data.objects['MakeHuman_Oni_Body'].get('stage')==REVISION
 report={'revision':REVISION,'mpfbVersion':'2.0.18','upstreamCommit':(vendor/'mpfb.ref').read_text().strip(),'bodyCageVertices':len(bpy.data.objects['MakeHuman_Oni_Body'].data.vertices),'macros':MACROS,'targets':TARGETS,'bodyShapedOnlyByNativeTargets':True,'priorCharacterImported':False,'skin':info,'hair':{'asset':'elvs_hazel_hair','author':'Elvaerwyn','license':'CC-BY','recolored':'ivory-silver'},'coverage':covers,'finalOutfitCreated':False,'rigged':False,'physicsIntegrated':False,'savedBlendReopened':True,'files':{p.name:digest(p) for p in out.iterdir() if p.is_file() and p.suffix in ['.blend','.json','.mhm','.png']}}
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print('MAKEHUMAN_STAGE01_SAVED_REOPENED',flush=True)
if __name__=='__main__':main()
