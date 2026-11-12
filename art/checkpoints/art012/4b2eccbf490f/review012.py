"""Repeatable visual review of actual Blender geometry, not generated images.
Usage: blender -b --python review012.py -- --source FILE.blend --out DIR
All revisions use exactly the same cameras, framing, lights and color management.
The tight body-only views deliberately exclude the lower body.
"""
from __future__ import annotations
import argparse, hashlib, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

SHOTS = {
    'front': ((0,-4,1.45),(0,-.06,1.45),.88,1.08,False),
    'quarter': ((2,-4,1.50),(0,-.06,1.45),.88,1.08,False),
    'side': ((4,0,1.45),(0,-.07,1.45),.88,1.08,False),
    'shoulder': ((1,-2,2.05),(0,-.015,1.635),.58,1.0,False),
    'body-front': ((0,-4,1.44),(0,-.06,1.44),.76,1.0,True),
    'body-quarter': ((2,-4,1.49),(0,-.06,1.44),.76,1.0,True),
    'body-side': ((4,0,1.44),(0,-.07,1.44),.76,1.0,True),
    'full': ((2.6,-5.8,1.85),(0,-.015,1.08),2.35,1.32,False),
    'back': ((0,4,1.45),(0,0,1.45),.88,1.08,False)
}

def render(source: Path, out: Path, shots: str='front,quarter,side', width: int=720, samples: int=24):
    source=source.resolve();out=out.resolve();out.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene=bpy.context.scene
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=samples
    scene.cycles.use_denoising=True;scene.cycles.seed=0;scene.cycles.use_animated_seed=False
    scene.render.threads_mode='FIXED';scene.render.threads=4
    scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    scene.view_settings.view_transform='AgX'
    scene.view_settings.look='AgX - Medium High Contrast'
    scene.view_settings.exposure=0;scene.view_settings.gamma=1
    # Identical lights for the baseline and every candidate. No beauty-light changes.
    for name,energy in [('STUDIO Key',520),('STUDIO Fill',260),('STUDIO Rim',720),('STUDIO lower front fill',65)]:
        if name in bpy.data.objects:bpy.data.objects[name].data.energy=energy
    camera=scene.camera
    if camera is None:
        data=bpy.data.cameras.new('REVIEW012');camera=bpy.data.objects.new('REVIEW012',data)
        scene.collection.objects.link(camera);scene.camera=camera
    initial={o.name:o.hide_render for o in bpy.data.objects}
    record={'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'fixedReviewVersion':1,'width':width,'samples':samples,'images':{},'shots':{}}
    for name in shots.split(','):
        if name not in SHOTS:raise ValueError('Unknown review view: '+name)
        loc,target,scale,aspect,body_only=SHOTS[name]
        for obj in bpy.data.objects:
            obj.hide_render=initial[obj.name]
            if body_only and obj.type in ('MESH','CURVE') and obj.name!='Body' and not obj.name.startswith('STUDIO'):
                obj.hide_render=True
        camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.type='ORTHO';camera.data.ortho_scale=scale;camera.data.lens=70
        scene.render.resolution_x=width;scene.render.resolution_y=round(width*aspect)
        path=out/(name+'.png');scene.render.filepath=str(path)
        bpy.ops.render.render(write_still=True)
        record['shots'][name]={'location':loc,'target':target,'orthoScale':scale,'aspect':aspect,'bodyOnly':body_only}
        record['images'][path.name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size}
        (out/'review-manifest.json').write_text(json.dumps(record,indent=2))
        print('REVIEW012_SAVED',name,flush=True)
    print('REVIEW012_COMPLETE',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--shots',default='front,quarter,side');parser.add_argument('--width',type=int,default=720);parser.add_argument('--samples',type=int,default=24)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);render(args.source,args.out,args.shots,args.width,args.samples)
