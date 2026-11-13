"""Fixed cameras/lights for this new MakeHuman study. Renders real mesh only."""
from pathlib import Path
import bpy,sys,argparse,hashlib,json
from mathutils import Vector
SHOTS={
 'quarter':((2.6,-5.8,2.0),(0,-.035,.93),2.12,1.35),
 'front':((0,-5,1.15),(0,-.035,.93),2.10,1.35),
 'side':((5,0,1.15),(0,-.035,.93),2.10,1.35),
 'back':((.0,5,1.15),(0,-.035,.93),2.10,1.35),
 'portrait':((1.2,-4,1.72),(0,-.045,1.66),.50,1.10),
 'torso':((1.2,-4,1.55),(0,-.055,1.36),.90,1.10)
}
def setup():
 s=bpy.context.scene
 for o in list(bpy.data.objects):
  if o.type in ('CAMERA','LIGHT') or o.name.startswith('REVIEW_'):bpy.data.objects.remove(o,do_unlink=True)
 s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=32;s.cycles.use_denoising=True;s.cycles.seed=0;s.render.threads_mode='FIXED';s.render.threads=4
 s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=0;s.view_settings.gamma=1
 w=bpy.data.worlds.new('Neutral review studio');w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Color'].default_value=(.035,.040,.045,1);w.node_tree.nodes['Background'].inputs['Strength'].default_value=.5;s.world=w
 for name,loc,energy,size in [('Key',(-3,-4,4),650,3.5),('Fill',(3,-3,2.2),320,3.0),('Rim',(0,2,3),700,3.0)]:
  d=bpy.data.lights.new('REVIEW_'+name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;o=bpy.data.objects.new('REVIEW_'+name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,-.04,1.1))-o.location).to_track_quat('-Z','Y').to_euler()
 c=bpy.data.cameras.new('REVIEW_CAMERA');o=bpy.data.objects.new('REVIEW_CAMERA',c);s.collection.objects.link(o);s.camera=o;c.type='ORTHO'
 setshot('quarter',900)
 return s

def setshot(name,width):
 s=bpy.context.scene;loc,target,scale,aspect=SHOTS[name];c=s.camera;c.location=loc;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=scale;s.render.resolution_x=width;s.render.resolution_y=round(width*aspect);s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'

def render(source,out,shots,width,samples):
 out.mkdir(parents=True,exist_ok=True);bpy.ops.wm.open_mainfile(filepath=str(source));s=setup();s.cycles.samples=samples
 result={'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'cameraVersion':1,'width':width,'samples':samples,'shots':{}}
 for name in shots.split(','):
  setshot(name,width);p=out/(name+'.png');s.render.filepath=str(p);bpy.ops.render.render(write_still=True);result['shots'][name]={'camera':SHOTS[name],'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size};(out/'review-manifest.json').write_text(json.dumps(result,indent=2));print('REVIEW_SAVED',name,flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--shots',default='quarter,front,side,back,portrait');ap.add_argument('--width',type=int,default=900);ap.add_argument('--samples',type=int,default=32);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);render(a.source.resolve(),a.out.resolve(),a.shots,a.width,a.samples)
