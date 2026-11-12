"""Render the actual saved character, not a generated illustration or animation claim."""
from __future__ import annotations
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--orbit',type=int,default=24)
 a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
 bpy.ops.wm.open_mainfile(filepath=str(a.source.resolve()))
 body=bpy.data.objects['Body'];assert body.get('finish008_applied')=='008-complete-visual-pass-11'
 scene=bpy.context.scene;camera=scene.camera
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4
 scene.render.image_settings.file_format='PNG';scene.render.resolution_percentage=100
 scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
 geometry=[]
 for o in scene.objects:
  if o.type!='MESH' or o.hide_render or o.name.startswith('STUDIO'):continue
  points=np.empty(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',points);assert np.isfinite(points).all(),o.name
  geometry.append({'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'materials':[m.name for m in o.data.materials if m]})
 images=[]
 for image in bpy.data.images:
  if image.name in {'Render Result','Viewer Node'}:continue
  used=any(n.type=='TEX_IMAGE' and n.image==image for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes)
  if used:
   assert image.packed_file or image.source=='GENERATED' or Path(bpy.path.abspath(image.filepath)).exists(),image.name
   images.append({'name':image.name,'packed':bool(image.packed_file),'source':image.source})
 report={'modelSha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),'revision':body.get('finish008_applied'),'finiteGeometry':True,'visibleMeshObjects':len(geometry),'meshObjects':geometry,'usedImages':images,'armatures':len([o for o in scene.objects if o.type=='ARMATURE']),'animationClaim':'Static visual turntable only; not a motion or physics test','cordModifiersRetained':sum(o.modifiers.get('Art007 cord rounding') is not None for o in scene.objects)}
 assert report['cordModifiersRetained']==6
 (out/'asset-audit.json').write_text(json.dumps(report,indent=2))
 def shot(name,location,target,scale,width,height,samples):
  camera.location=location;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=scale
  scene.render.resolution_x=width;scene.render.resolution_y=height;scene.cycles.samples=samples
  scene.render.filepath=str(out/name);bpy.ops.render.render(write_still=True)
 shot('hero.png',(3,-6,2.1),(0,0,1.06),2.35,1200,1560,48)
 shot('portrait.png',(.18,-3,1.86),(0,-.04,1.815),.54,1200,1344,48)
 for i in range(a.orbit):
  angle=2*math.pi*i/a.orbit
  shot('orbit-%03d.png'%i,(5*math.sin(angle),-5*math.cos(angle),1.65),(0,0,1.06),2.35,480,624,12)
 print('VISUAL_MASTER_PRESENTATION_PASS',flush=True)
if __name__=='__main__':main()
