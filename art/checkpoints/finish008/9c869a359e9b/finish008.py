"""Art008: edit a pinned, complete Blender asset; save before rendering.
Visual art only. Rig and physics acceptance must be established separately.
"""
from __future__ import annotations
import argparse, hashlib, json, sys, shutil, importlib
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
MODULES=[importlib.import_module(n) for n in ('surface008','portrait008','silhouette008','finishing008','beauty008','skin008','garment008','groom009','hair008','face009','detail009')]
REVISION='008-complete-visual-pass-11'

def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def positions(obj):
 p=np.empty(len(obj.data.vertices)*3);obj.data.vertices.foreach_get('co',p);return p.reshape(-1,3)
def put(obj,p):
 if not np.isfinite(p).all():raise ValueError('Non-finite mesh '+obj.name)
 obj.data.vertices.foreach_set('co',p.ravel());obj.data.update()
def facial_warp(p):
 x,y,z=p.T;ax=np.abs(x);d=np.zeros_like(p);front=1-smooth(-.11,-.045,y)
 jaw=np.exp(-((z-1.728)/.041)**2)*smooth(.023,.065,ax)*front;d[:,0]-=x*.075*jaw
 chin=np.exp(-((z-1.698)/.022)**2-(x/.045)**2)*front;d[:,2]+=.0028*chin
 nose=np.exp(-((z-1.772)/.019)**2-((ax-.021)/.018)**2)*(1-smooth(-.181,-.137,y));d[:,0]-=np.sign(x)*.0011*nose
 outer=np.exp(-((ax-.060)/.016)**2-((z-1.825)/.018)**2)*front;d[:,2]+=.0018*outer
 corners=np.exp(-((ax-.030)/.012)**2-((z-1.742)/.013)**2)*front;d[:,2]+=(.0010+.0008*(x>0))*corners;d[:,0]+=np.sign(x)*.0010*corners
 return p+d

def edit():
 body=bpy.data.objects.get('Body')
 if body is None:raise RuntimeError('Expected complete Cord007 character')
 if body.get('finish008_applied'):raise RuntimeError('Refusing duplicate sculpt')
 put(body,facial_warp(positions(body)))
 for o in bpy.data.objects:
  if o.type!='MESH' or o==body:continue
  if o.name.startswith(('Brow','Upper liner','Outer eyelash','Canine')):
   p=facial_warp(positions(o))
   if o.name.startswith('Brow.'):
    center=p.mean(0);p[:,2]=center[2]+(p[:,2]-center[2])*.77;p[:,1]+=.0003
   if o.name.startswith('Canine'):
    top=p[:,2].max();p[:,2]=top+(p[:,2]-top)*.72+.0016;p[:,1]+=.0010
   put(o,p)
 skin=bpy.data.materials.get('Skin | cool slate')
 if skin and skin.use_nodes:
  bs=skin.node_tree.nodes.get('Principled BSDF')
  if bs:
   bs.inputs['Specular IOR Level'].default_value=.24;bs.inputs['Subsurface Weight'].default_value=.075;bs.inputs['Subsurface Scale'].default_value=.0015
 for m in MODULES:m.apply(body)
 body['finish008_applied']=REVISION;body['asset_kind']='Visual art master; rig and physics refit remain separate';bpy.context.scene['art_checkpoint']=REVISION

def render(out,views,width,samples):
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=samples;scene.cycles.use_denoising=True
 scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.image_settings.file_format='PNG';scene.render.resolution_percentage=100
 scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';camera=scene.camera
 shots={'front':((0,-5,1.30),(0,0,1.06),2.35),'three-quarter':((3,-6,2.1),(0,0,1.06),2.35),'side':((5,0,1.30),(0,0,1.06),2.35),'back':((.15,5,1.30),(0,0,1.06),2.35),'portrait':((.18,-3,1.86),(0,-.04,1.815),.54),'torso':((.15,-4,1.51),(0,-.04,1.44),.90)}
 for view in views.split(','):
  loc,target,scale=shots[view];camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=scale
  scene.render.resolution_x=width;scene.render.resolution_y=round(width*(1.12 if view in ('portrait','torso') else 1.30));scene.render.filepath=str(out/(view+'.png'));bpy.ops.render.render(write_still=True)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--render-only',action='store_true');ap.add_argument('--views',default='');ap.add_argument('--width',type=int,default=850);ap.add_argument('--samples',type=int,default=24)
 a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
 for f in [Path(__file__)]+[Path(m.__file__) for m in MODULES]:
  target=out/f.name
  if target.resolve()!=f.resolve():shutil.copy2(f,target)
 bpy.ops.wm.open_mainfile(filepath=str(a.source.resolve()))
 if not a.render_only:
  edit();bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0;path=out/'Character01_Finish008.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
  bpy.ops.wm.open_mainfile(filepath=str(path));assert bpy.data.objects['Body'].get('finish008_applied')==REVISION
  files={path.name:{'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}}
  manifest={'revision':REVISION,'sourceSha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),'savedBlendReopened':True,'finishedCharacter':False,'files':files}
  (out/'manifest.json').write_text(json.dumps(manifest,indent=2));print('ART008_EDIT_SAVE_REOPEN_PASS',flush=True)
 if a.views:render(out,a.views,a.width,a.samples)
if __name__=='__main__':main()
