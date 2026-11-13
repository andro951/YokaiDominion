"""Fixed camera/light review of real Blender assets. Does not save over the asset."""
from pathlib import Path
import argparse, hashlib, json, sys
import bpy
from mathutils import Vector
SHOTS={
 'front':((0,-4,1.45),(0,-.06,1.45),.88,1.08,False),
 'quarter':((2,-4,1.50),(0,-.06,1.45),.88,1.08,False),
 'side':((4,0,1.45),(0,-.07,1.45),.88,1.08,False),
 'shoulder':((1,-2,2.05),(0,-.015,1.635),.58,1.,False),
 'body-front':((0,-4,1.44),(0,-.06,1.44),.76,1.,True),
 'body-quarter':((2,-4,1.49),(0,-.06,1.44),.76,1.,True),
 'body-side':((4,0,1.44),(0,-.07,1.44),.76,1.,True),
 'full':((2.6,-5.8,1.85),(0,-.015,1.08),2.35,1.32,False),
 'back':((0,4,1.45),(0,0,1.45),.88,1.08,False)}
LIGHTS=[('key',(-3,-4,5),520,3),('fill',(4,-2,3),260,3.5),('rim',(1,2,4.2),720,2.2),('lower',(0,-3,1.35),65,2)]
def render(source,out,shots='front,quarter,side',width=800,samples=32):
 source=Path(source).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
 if width<128 or samples<1:raise ValueError('Invalid settings')
 bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.context.scene
 for o in list(bpy.data.objects):
  if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
  elif o.name.startswith('STUDIO'):o.hide_render=True
 for name,position,power,size in LIGHTS:
  light=bpy.data.lights.new('REVIEW013_'+name,'AREA');light.energy=power;light.shape='DISK';light.size=size
  o=bpy.data.objects.new(light.name,light);s.collection.objects.link(o);o.location=position
  target=(0,0,1.4) if name=='lower' else (0,0,1.1)
  o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
 world=bpy.data.worlds.new('REVIEW013_WORLD');world.use_nodes=True;s.world=world
 world.node_tree.nodes['Background'].inputs['Color'].default_value=(.035,.045,.06,1)
 world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
 s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=samples;s.cycles.use_denoising=True
 s.cycles.seed=0;s.cycles.use_animated_seed=False;s.render.threads_mode='FIXED';s.render.threads=4
 s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.film_transparent=False
 s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=0;s.view_settings.gamma=1
 if s.camera is None:
  camera=bpy.data.objects.new('Review camera',bpy.data.cameras.new('Review camera'));s.collection.objects.link(camera);s.camera=camera
 camera=s.camera;initial={o.name:o.hide_render for o in bpy.data.objects}
 record={'version':13,'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'lights':LIGHTS,'width':width,'samples':samples,'images':{},'shots':{}}
 for name in shots.split(','):
  if name not in SHOTS:raise ValueError('Unknown shot '+name)
  loc,target,scale,aspect,body_only=SHOTS[name]
  for o in bpy.data.objects:
   o.hide_render=initial[o.name]
   if body_only and o.type in ('MESH','CURVE') and o.name!='Body':o.hide_render=True
  camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=scale
  s.render.resolution_x=width;s.render.resolution_y=round(width*aspect);p=out/(name+'.png');s.render.filepath=str(p)
  bpy.ops.render.render(write_still=True)
  record['shots'][name]={'location':loc,'target':target,'scale':scale,'aspect':aspect,'bodyOnly':body_only}
  record['images'][p.name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
  (out/'review-manifest.json').write_text(json.dumps(record,indent=2));print('REVIEW013_SAVED',name,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--shots',default='front,quarter,side');p.add_argument('--width',type=int,default=800);p.add_argument('--samples',type=int,default=32)
 a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);render(a.source,a.out,a.shots,a.width,a.samples)
