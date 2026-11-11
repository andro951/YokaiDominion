"""Second authoring pass, using the versioned baseline's export/rig/data pipeline.
Replaces abrupt anatomical weight classification with smooth region blending.
The initial baseline is retained for reproducing the failure that motivated this pass.
"""
from __future__ import annotations
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from mathutils import Vector
import build_character as b

original_limb=b.limb
original_body=b.make_body
original_stage=b.build_stage


def ellipsoid(name,center,scale,mat='Skin',record=True,axis=None):
    if name in ('Quadriceps','CalfMuscle'): return None
    if name=='HipForm': scale=(.214,scale[1],.235)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=32,location=center)
    o=bpy.context.object;o.name=name;o.scale=scale
    if axis is not None:o.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler()
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    o.data.materials.append(b.MATS[mat])
    for p in o.data.polygons:p.use_smooth=True
    if record:b.PARTS.append(o)
    return o


def limb(name,a,c,radius,depth=None):
    if name not in ('Thigh','Calf'):return original_limb(name,a,c,radius,depth)
    a,c=Vector(a),Vector(c)
    points=[tuple(a.lerp(c,t)) for t in (0,.25,.5,.75,1)]
    widths=[.176,.177,.156,.117,.090] if name=='Thigh' else [.091,.111,.104,.075,.058]
    depths=[.154,.159,.145,.112,.088] if name=='Thigh' else [.089,.112,.104,.078,.061]
    return b.tube(name,points,widths,depths,mat='Skin',sides=32,steps=4)


def make_body():
    body=original_body();bpy.context.view_layer.objects.active=body
    smooth=body.modifiers.new('SecondSculptRelax','SMOOTH');smooth.factor=.35;smooth.iterations=8;bpy.ops.object.modifier_apply(modifier=smooth.name)
    dec=body.modifiers.new('PrototypeSurfaceBudget','DECIMATE');dec.ratio=.35;bpy.ops.object.modifier_apply(modifier=dec.name)
    for p in body.data.polygons:p.use_smooth=True
    return body


def smooth(lo,hi,x):
    t=max(0,min(1,(x-lo)/(hi-lo)));return t*t*(3-2*t)


def blend(a,c,t):
    d={n:w*(1-t) for n,w in a.items()}
    for n,w in c.items():d[n]=d.get(n,0)+w*t
    return d


def nearby(p,names):
    raw={n:1/(b.segment_distance(p,b.BONES[n][0],b.BONES[n][1])+.020)**5 for n in names}
    total=sum(raw.values());return {n:w/total for n,w in raw.items()}


def torso(p):
    levels=[('Pelvis',1.03),('Spine01',1.20),('Spine02',1.39),('Chest',1.57),('Neck',1.72),('Head',1.86)]
    z=p.z
    if z<=levels[0][1]:return {levels[0][0]:1}
    if z>=levels[-1][1]:return {levels[-1][0]:1}
    for (n,a),(m,c) in zip(levels,levels[1:]):
        if a<=z<=c:return blend({n:1},{m:1},smooth(a,c,z))
    raise RuntimeError('Torso interpolation')


def skin_weights(o,p):
    if o.name!='Body':return nearby(p,b.candidates(o,p))
    base=torso(p)
    chest=smooth(1.16,1.32,p.z)*(1-smooth(1.64,1.73,p.z))*(1-smooth(-.20,-.08,p.y))
    base=blend(base,{'Chest':1},chest)
    side='L' if p.x>=0 else 'R';ax=abs(p.x)
    arm_inner=.30+.42*(1.60-max(1.06,min(1.60,p.z)))
    arm=smooth(arm_inner-.035,arm_inner+.055,ax)*smooth(-.18,-.075,p.y)
    arm*=smooth(.77,.94,p.z)*(1-smooth(1.69,1.79,p.z))
    arm_names=['Clavicle.'+side,'UpperArm.'+side,'UpperArmTwist.'+side,'Forearm.'+side,'ForearmTwist.'+side,'Hand.'+side]
    if p.z<1.10:arm_names += [n for n in b.BONES if n.endswith('.'+side) and n.startswith(('Index','Middle','Ring','Little','Thumb'))]
    base=blend(base,nearby(p,arm_names),arm)
    leg=(1-smooth(.84,1.08,p.z))*(1-arm)
    if leg>0:
        leg_names=lambda s:['Thigh.'+s,'ThighTwist.'+s,'Shin.'+s,'Foot.'+s,'Toe.'+s]
        legs=blend(nearby(p,leg_names('R')),nearby(p,leg_names('L')),smooth(-.06,.06,p.x))
        base=blend(base,legs,leg)
    return base


def bind(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.quads_convert_to_tris();bpy.ops.uv.smart_project(island_margin=.01);bpy.ops.object.mode_set(mode='OBJECT')
    groups={n:o.vertex_groups.new(name=n) for n in b.BONES if b.BONES[n][3]}
    for v in o.data.vertices:
        pairs=sorted(skin_weights(o,v.co).items(),key=lambda pair:pair[1],reverse=True)[:4]
        total=sum(w for n,w in pairs)
        if total<=0:raise ValueError('No skin support for '+o.name)
        for n,w in pairs:
            if w>0:groups[n].add([v.index],w/total,'REPLACE')
    o.parent=b.RIG;mod=o.modifiers.new('DeformationSkin','ARMATURE');mod.object=b.RIG


def build_stage():
    camera=original_stage();bpy.context.scene.view_settings.exposure=-.65;camera.data.ortho_scale=2.70
    return camera


b.ellipsoid=ellipsoid;b.limb=limb;b.make_body=make_body;b.bind=bind;b.build_stage=build_stage
if __name__=='__main__':b.main()
