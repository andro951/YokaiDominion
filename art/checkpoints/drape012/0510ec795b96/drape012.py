"""Static garment relaxation on a fixed character. No runtime physics acceptance."""
from pathlib import Path
import argparse,hashlib,json,sys,time
import bpy
import numpy as np
REVISION='012-volume-and-relaxed-cloth-10'
ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--frames',type=int,default=40);args=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
assert 1<=args.frames<=180
out=args.out.resolve();out.mkdir(parents=True,exist_ok=True);bpy.ops.wm.open_mainfile(filepath=str(args.source.resolve()))
s=bpy.context.scene;s.frame_start=1;s.frame_end=args.frames;s.frame_set(1)
body=bpy.data.objects['Body'];before=np.empty(len(body.data.vertices)*3);body.data.vertices.foreach_get('co',before)
proxy=body.copy();proxy.data=body.data.copy();bpy.context.collection.objects.link(proxy);proxy.name='Art012_BODY_COLLISION';proxy.hide_render=True
bpy.ops.object.select_all(action='DESELECT');proxy.select_set(True);bpy.context.view_layer.objects.active=proxy
m=proxy.modifiers.new('Static collision approximation','DECIMATE');m.ratio=.045;bpy.ops.object.modifier_apply(modifier=m.name)
proxy.modifiers.new('Static body collision','COLLISION');proxy.collision.thickness_outer=.002;proxy.collision.thickness_inner=.001;proxy.collision.cloth_friction=5
cloth=[]
for side in ['L','R']:
 o=bpy.data.objects['Loose over-trapezius panel '+side];initial=np.array([v.co[:] for v in o.data.vertices]);mods=[]
 for m in o.modifiers:
  mods.append((m,m.show_viewport,m.show_render));m.show_viewport=False;m.show_render=False
 vg=o.vertex_groups.new(name='Art012_Attachments')
 for i in range(242):
  if i in [0,241]:w=1.
  elif i in [1,240]:w=.8
  elif 111<=i<=132:w=1.
  elif 106<=i<=137:w=.85
  elif i<=3 or i>=238:w=.3
  else:continue
  vg.add(list(range(i*33,(i+1)*33)),w,'REPLACE')
 m=o.modifiers.new('Art012 static drape relaxation','CLOTH');m.settings.quality=6;m.settings.mass=.18;m.settings.air_damping=5;m.settings.time_scale=.65
 m.settings.tension_stiffness=20;m.settings.compression_stiffness=20;m.settings.shear_stiffness=10;m.settings.bending_stiffness=.45
 m.settings.tension_damping=5;m.settings.compression_damping=5;m.settings.shear_damping=5;m.settings.bending_damping=.5
 m.settings.vertex_group_mass=vg.name;m.settings.pin_stiffness=1
 m.collision_settings.use_collision=True;m.collision_settings.distance_min=.003;m.collision_settings.collision_quality=3;m.collision_settings.use_self_collision=False
 m.point_cache.frame_start=1;m.point_cache.frame_end=args.frames
 cloth.append((o,m,mods,initial))
start=time.time()
for frame in range(1,args.frames+1):
 s.frame_set(frame);deps=bpy.context.evaluated_depsgraph_get()
 for o,m,mods,initial in cloth:
  ev=o.evaluated_get(deps);mesh=ev.to_mesh();ev.to_mesh_clear()
 if frame%10==0:print('CLOTH_FRAME',frame,round(time.time()-start,1),flush=True)
results=[]
for o,m,mods,initial in cloth:
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();p=np.array([v.co[:] for v in mesh.vertices]);ev.to_mesh_clear()
 assert len(p)==len(initial);delta=np.linalg.norm(p-initial,axis=1)
 assert np.isfinite(p).all() and delta.max()<.30,('cloth runaway',delta.max())
 o.modifiers.remove(m);o.data.vertices.foreach_set('co',p.ravel());o.data.update()
 for mm,viewport,render in mods:mm.show_viewport=viewport;mm.show_render=render
 o['art012']=REVISION;o['Art012_StaticDrape']='Relaxed over fixed body; no dynamic runtime acceptance'
 results.append({'name':o.name,'maxMovementMetres':float(delta.max()),'meanMovementMetres':float(delta.mean())})
bpy.data.objects.remove(proxy,do_unlink=True);s.frame_set(1)
after=np.empty(len(body.data.vertices)*3);body.data.vertices.foreach_get('co',after);assert np.array_equal(before,after),'Clothing must not reshape body'
body['art012']=REVISION;s['art_checkpoint']=REVISION
bpy.ops.outliner.orphans_purge(do_local_ids=True,do_linked_ids=False,do_recursive=True);bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0
file=out/'Character01_Art012.blend';bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True)
report={'revision':REVISION,'frames':args.frames,'seconds':time.time()-start,'bodyUnchanged':True,'cloth':results,'staticVisualAsset':True,'rigUpdated':False,'runtimePhysicsUpdated':False,'userApproved':False,'sourceSha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),'files':{file.name:{'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}}}
bpy.ops.wm.open_mainfile(filepath=str(file));assert bpy.data.objects['Body'].get('art012')==REVISION;report['savedBlendReopened']=True
(out/'manifest.json').write_text(json.dumps(report,indent=2));print('ART012_SAVED_REOPENED',flush=True)
