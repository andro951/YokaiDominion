"""Character-specific proportion, skinning and pose refinement over the reusable baseline.
Still an early voxel-sculpt mesh: anatomical retopology and corrective refinement remain.
"""
from __future__ import annotations
import json
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
original_rig=b.make_rig
original_outfit=b.make_outfit
original_animate=b.animate
original_regions=b.export_regions


def ellipsoid(name,center,scale,mat='Skin',record=True,axis=None):
    if name in ('Quadriceps','CalfMuscle'): return None
    if name=='HipForm': scale=(.214,scale[1],.235)
    if name=='BreastForm':
        center=(math.copysign(.175,center[0]),-.180,1.415);scale=(.205,.220,.205)
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
    return {n:w for n,w in d.items() if w>1e-9}


def nearby(p,names):
    raw={n:1/(b.segment_distance(p,b.BONES[n][0],b.BONES[n][1])+.020)**5 for n in names}
    total=sum(raw.values());return {n:w/total for n,w in raw.items()}


def chain(z,levels):
    if z<=levels[0][1]:return {levels[0][0]:1}
    if z>=levels[-1][1]:return {levels[-1][0]:1}
    for (a,za),(c,zc) in zip(levels,levels[1:]):
        if za<=z<=zc:return blend({a:1},{c:1},smooth(za,zc,z))
    raise ValueError('No chain interval')


def skin_weights(o,p):
    if o.name!='Body':return nearby(p,b.candidates(o,p))
    x,y,z=p;ax=abs(x);side='L' if x>=0 else 'R'
    chest=smooth(1.16,1.32,z)*(1-smooth(1.62,1.73,z))*(1-smooth(-.18,-.06,y))
    tz=z*(1-chest)+1.57*chest
    base=chain(tz,[('Pelvis',1.03),('Spine01',1.20),('Spine02',1.39),('Chest',1.57),('Neck',1.72),('Head',1.86)])
    # Distal arms must not retain torso/pelvis weights. Only blend at the shoulder/armpit.
    inner=.255+.12*(1.60-max(1.,min(1.60,z)))
    outer=.335+.16*(1.60-max(1.,min(1.60,z)))
    arm=smooth(inner,outer,ax)*smooth(-.18,-.07,y)*smooth(.69,.78,z)
    arm_bones=chain(z,[('Hand.'+side,1.03),('Forearm.'+side,1.10),('Forearm.'+side,1.24),('UpperArm.'+side,1.36)])
    # Finger joints exist but isolated finger deformation is not validated in this milestone.
    if arm>1-1e-7:return arm_bones
    if z<1.12 and ax<.43:
        leg=(1-smooth(.85,1.10,z))*smooth(.015,.09,ax)
        legs=chain(z,[('Toe.'+side,.03),('Foot.'+side,.12),('Shin.'+side,.24),('Shin.'+side,.49),('Thigh.'+side,.62)])
        base=blend(base,legs,leg)
    return blend(base,arm_bones,arm)


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


def make_rig(tail):
    rig=original_rig(tail)
    bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
    for name in b.BONES:
        eb=rig.data.edit_bones[name]
        if name.startswith(('Clavicle','UpperArm','Forearm','Hand','Thigh','Shin','Foot','Toe','Index','Middle','Ring','Little','Thumb')):
            eb.align_roll(Vector((0,1,0)))
        elif name in ('Root','Pelvis','Spine01','Spine02','Chest','Neck','Head','Jaw'):
            eb.align_roll(Vector((0,-1,0)))
    bpy.ops.object.mode_set(mode='OBJECT')
    return rig


def make_outfit():
    original_outfit()
    # Replace angular old breast panels with a single smooth parametric drape per side.
    for o in list(b.PARTS):
        if o.name.startswith('ChestDrape'):
            b.PARTS.remove(o);bpy.data.objects.remove(o,do_unlink=True)
    for s in (-1,1):
        vertices=[];faces=[];rows=37;cols=16
        for i in range(rows):
            t=i/(rows-1);z=1.71-.505*t
            angle=.66-.14*math.sin(math.pi*t)
            u=(z-1.415)/.205
            r=math.sqrt(max(0,1-u*u))
            for j in range(cols+1):
                q=2*j/cols-1;phi=angle+q*.28
                if 1.21<=z<=1.62:
                    x=.175+.205*r*math.sin(phi);y=-.180-.220*r*math.cos(phi)-.009
                elif z>1.62:
                    a=smooth(1.62,1.71,z);x=.175*(1-a)+.272*a+q*(.027+.005*a);y=-.189*(1-a)-.03*a
                else:
                    a=smooth(1.205,1.21,z);x=.17+q*.035;y=-.174-.015*a
                vertices.append((s*x,y,z))
        for i in range(rows-1):
            for j in range(cols):
                a=i*(cols+1)+j;face=(a,a+1,a+cols+2,a+cols+1);faces.append(face if s>0 else tuple(reversed(face)))
        o=b.mesh_object('ChestDrape_'+str(s),vertices,faces,'Cloth');sol=o.modifiers.new('FabricThickness','SOLIDIFY');sol.thickness=.004;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=sol.name)


def animate(keys):
    original_animate(keys)
    root=b.RIG.pose.bones['Root'];inverse=b.RIG.data.bones['Root'].matrix_local.to_3x3().inverted()
    for name,frame in b.POSES:
        delta=(0,0,-.43) if name=='crouch' else (0,0,.40) if name=='jump' else (0,-.45,.21) if name=='knockdown' else (0,0,0)
        root.location=inverse@Vector(delta);root.keyframe_insert(data_path='location',frame=frame,group='Root')


def export_regions(out):
    doc=original_regions(out)
    for r in doc['regions']:
        if r['name'].startswith('breast'):
            old_c=r['center'];old_r=r['radii'];new_c=[math.copysign(.175,old_c[0]),1.415,.180];new_r=[.23,.245,.25]
            r['nodes']=[[new_c[k]+(p[k]-old_c[k])*new_r[k]/old_r[k] for k in range(3)] for p in r['nodes']]
            r['center']=new_c;r['radii']=new_r;r['youngModulus']=30000
        else:r['youngModulus']=60000
        r['poissonRatio']=.4999
        r['solverSubsteps']=8;r['solverIterations']=8;r['velocityDrag']=4.0
    (out/'tissue-regions.json').write_text(json.dumps(doc,separators=(',',':')),encoding='utf8')
    return doc


def build_stage():
    camera=original_stage();bpy.context.scene.view_settings.exposure=-.65;camera.data.ortho_scale=2.70
    return camera


b.ellipsoid=ellipsoid;b.limb=limb;b.make_body=make_body;b.bind=bind;b.make_rig=make_rig;b.make_outfit=make_outfit;b.animate=animate;b.export_regions=export_regions;b.build_stage=build_stage
if __name__=='__main__':b.main()
