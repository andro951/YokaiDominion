"""Reproducible character blockout, deformation rig and volumetric-region authoring.
Blender 4.5.3: --background --python-exit-code 1 --python tools/blender/build_character.py -- --out artifacts/character
This is an early sculpt/rig prototype, NOT approved final topology or anatomically calibrated flesh.
Original illustration controls proportions/outfit/palette; secondary sheet supplies only details.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import bpy
from mathutils import Vector

MATS = {}
PARTS = []
RIG = None
BONES = {}
POSES = [('neutral',1),('overhead',31),('crouch',61),('high_kick',91),('torso_twist',121),('jump',151),('knockdown',181),('recover',211)]

def linear(c):
    return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4

def material(name, color, roughness=.65):
    rgb = tuple(int(color[i:i+2],16)/255 for i in (0,2,4))
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*[linear(x) for x in rgb],1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = m.diffuse_color
    p.inputs['Roughness'].default_value = roughness
    MATS[name] = m
    return m

def mesh_object(name, vertices, faces, mat='Skin', record=True):
    d = bpy.data.meshes.new(name+'Geometry')
    d.from_pydata(vertices, [], faces); d.update()
    o = bpy.data.objects.new(name,d); bpy.context.collection.objects.link(o)
    d.materials.append(MATS[mat])
    for p in d.polygons: p.use_smooth = True
    if record: PARTS.append(o)
    return o

def ellipsoid(name, center, scale, mat='Skin', record=True, axis=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, location=center)
    o = bpy.context.object; o.name=name; o.scale=scale
    if axis is not None: o.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler()
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    o.data.materials.append(MATS[mat])
    for p in o.data.polygons: p.use_smooth=True
    if record: PARTS.append(o)
    return o

def limb(name, a, b, radius, depth=None):
    a,b=Vector(a),Vector(b)
    return ellipsoid(name,(a+b)/2,(radius,depth or radius,(b-a).length/2+radius*.45),axis=b-a)

def tube(name, points, widths, depths=None, mat='Hair', sides=10, steps=5, record=True):
    # Catmull-Rom centerline and elliptical sections; all ends capped with triangles.
    pts=[Vector(p) for p in points]; depths=depths or widths
    centers=[]; wr=[]; dr=[]
    for k in range(len(pts)-1):
        p0,p1,p2,p3=pts[max(0,k-1)],pts[k],pts[k+1],pts[min(len(pts)-1,k+2)]
        for j in range(steps):
            t=j/steps
            centers.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
            wr.append(max(.0007,widths[k]*(1-t)+widths[k+1]*t)); dr.append(max(.0007,depths[k]*(1-t)+depths[k+1]*t))
    centers.append(pts[-1]); wr.append(max(.0007,widths[-1])); dr.append(max(.0007,depths[-1]))
    vertices=[]; faces=[]
    for i,p in enumerate(centers):
        tangent=(centers[min(i+1,len(centers)-1)]-centers[max(i-1,0)]).normalized()
        ref=Vector((0,1,0)) if abs(tangent.y)<.94 else Vector((1,0,0))
        u=tangent.cross(ref).normalized(); v=tangent.cross(u).normalized()
        for j in range(sides):
            t=2*math.pi*j/sides; vertices.append(tuple(p+u*(wr[i]*math.cos(t))+v*(dr[i]*math.sin(t))))
    for i in range(len(centers)-1):
        for j in range(sides):
            a=i*sides+j; b=i*sides+(j+1)%sides; faces.append((a,b,b+sides,a+sides))
    for base,reverse in [(0,True),((len(centers)-1)*sides,False)]:
        for j in range(1,sides-1):
            tri=(base,base+j,base+j+1); faces.append(tuple(reversed(tri)) if reverse else tri)
    return mesh_object(name,vertices,faces,mat,record)

def loft(name, rings, n=48):
    # rings = z, x half-width, y half-depth, y center
    verts=[]; faces=[]
    for z,rx,ry,cy in rings:
        for j in range(n):
            t=j*2*math.pi/n; verts.append((rx*math.cos(t),cy+ry*math.sin(t),z))
    for i in range(len(rings)-1):
        for j in range(n):
            a=i*n+j; b=i*n+(j+1)%n; faces.append((a,b,b+n,a+n))
    for j in range(1,n-1):
        faces.append((0,j+1,j)); a=(len(rings)-1)*n; faces.append((a,a+j,a+j+1))
    return mesh_object(name,verts,faces)

def make_body():
    start=len(PARTS)
    loft('Torso',[(.90,.22,.15,.025),(.98,.31,.19,.02),(1.07,.29,.175,.005),(1.16,.225,.135,0),(1.23,.205,.13,0),(1.32,.235,.145,0),(1.43,.28,.165,.01),(1.54,.30,.16,.015),(1.62,.26,.14,.015),(1.68,.14,.10,.015),(1.75,.072,.066,0)],64)
    loft('Head',[(1.72,.035,.048,-.015),(1.75,.064,.068,-.015),(1.79,.088,.078,-.004),(1.84,.113,.091,.006),(1.90,.108,.092,.012),(1.95,.079,.072,.013),(1.978,.025,.027,.01)],48)
    ellipsoid('NoseBridge',(0,-.078,1.822),(.017,.028,.042))
    ellipsoid('NoseTip',(0,-.104,1.793),(.020,.022,.013))
    for s in (-1,1):
        ellipsoid('BreastForm',(s*.185,-.205,1.452),(.229,.249,.255))
        ellipsoid('HipForm',(s*.16,.005,1.005),(.224,.176,.205))
        ellipsoid('GlutealForm',(s*.164,.117,1.005),(.216,.196,.221))
        shoulder=(s*.325,0,1.61); elbow=(s*.489,-.008,1.296); wrist=(s*.586,-.020,1.06)
        ellipsoid('Deltoid',shoulder,(.116,.108,.123))
        limb('UpperArm',shoulder,elbow,.101,.093)
        ellipsoid('Biceps',(s*.414,-.044,1.455),(.089,.082,.152),axis=(s*.4,0,-.9))
        ellipsoid('Elbow',elbow,(.069,.070,.076))
        limb('Forearm',elbow,wrist,.076,.071)
        ellipsoid('Palm',(s*.608,-.019,.990),(.055,.032,.087),axis=(s*.15,0,-1))
        for f in range(4):
            x=s*(.565+f*.026); z=.951-abs(f-1)*.007
            length=[.092,.108,.099,.079][f]
            limb('Finger',(x,-.022,z),(x+s*.016,-.027,z-length),.013,.012)
        limb('Thumb',(s*.565,-.021,1.013),(s*.536,-.042,.944),.019,.016)
        thigh=(s*.184,.012,.955); knee=(s*.199,-.025,.545); ankle=(s*.207,.015,.145)
        limb('Thigh',thigh,knee,.170,.151)
        ellipsoid('Quadriceps',(s*.197,-.047,.77),(.164,.143,.250))
        ellipsoid('Knee',knee,(.092,.099,.095))
        limb('Calf',knee,ankle,.103,.100)
        ellipsoid('CalfMuscle',(s*.207,.050,.345),(.111,.114,.180))
        ellipsoid('Ankle',ankle,(.062,.063,.090))
        ellipsoid('Foot',(s*.207,-.073,.065),(.091,.155,.060))
        for t in range(5):
            x=s*(.145+t*.031); y=-.193+abs(t-1)*.011
            ellipsoid('Toe',(x,y,.043),(.021-.0016*t,.052-.004*t,.027-.002*t))
        # Low-amplitude abdominal forms merge into the torso rather than sitting on it.
        for z,rx in [(1.27,.049),(1.33,.058),(1.39,.062)]:
            ellipsoid('Abdominal',(s*.055,-.126,z),(rx,.020,.042))
    pieces=PARTS[start:]
    bpy.ops.object.select_all(action='DESELECT')
    for o in pieces: o.select_set(True)
    bpy.context.view_layer.objects.active=pieces[0]; bpy.ops.object.join()
    body=bpy.context.object; body.name='Body'
    mod=body.modifiers.new('BlockoutVoxelUnion','REMESH'); mod.mode='VOXEL'; mod.voxel_size=.0075; mod.use_smooth_shade=True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    smooth=body.modifiers.new('SculptRelax','SMOOTH'); smooth.factor=.45; smooth.iterations=3; bpy.ops.object.modifier_apply(modifier=smooth.name)
    dec=body.modifiers.new('BlockoutBudget','DECIMATE'); dec.ratio=.62; bpy.ops.object.modifier_apply(modifier=dec.name)
    body.data.materials.clear(); body.data.materials.append(MATS['Skin'])
    for p in body.data.polygons: p.use_smooth=True
    del PARTS[start:]; PARTS.append(body)
    # Color attribute records original-style dark shoulder/arm markings, not painted lighting.
    colors=body.data.color_attributes.new(name='SkinPalette',type='FLOAT_COLOR',domain='POINT')
    skin=MATS['Skin'].diffuse_color; marking=MATS['Markings'].diffuse_color
    for v in body.data.vertices:
        x,y,z=v.co; ax=abs(x); dark=False
        if .30<ax<.52 and 1.30<z<1.67:
            line=math.sin(30*z+12*ax); dark=y<-.015 and line>.73 and abs(y)<.13
        if .49<ax<.64 and 1.09<z<1.30:
            dark=y<-.015 and math.sin(43*z+18*ax)>.84
        colors.data[v.index].color=marking if dark else skin
    attr=MATS['Skin'].node_tree.nodes.new('ShaderNodeVertexColor'); attr.layer_name='SkinPalette'
    MATS['Skin'].node_tree.links.new(attr.outputs['Color'],MATS['Skin'].node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    return body

def make_details():
    for s in (-1,1):
        ear=mesh_object('Ear_'+str(s),[(s*.095,.012,1.856),(s*.206,.025,1.914),(s*.155,.035,1.810),(s*.108,-.014,1.824),(s*.143,-.012,1.855),(s*.136,.039,1.853)],[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(0,5,1),(1,5,2),(2,5,3),(3,5,0)],'PlainSkin')
        sub=ear.modifiers.new('EarSmooth','SUBSURF'); sub.levels=2; bpy.context.view_layer.objects.active=ear; bpy.ops.object.modifier_apply(modifier=sub.name)
        tube('Horn_'+str(s),[(s*.078,.005,1.939),(s*.127,-.003,2.026),(s*.149,.006,2.115),(s*.117,-.020,2.190)],[.043,.039,.024,.001],mat='Horn',sides=14)
        ellipsoid('EyeWhite_'+str(s),(s*.053,-.081,1.843),(.033,.018,.014),'EyeWhite')
        ellipsoid('Iris_'+str(s),(s*.052,-.098,1.843),(.012,.0038,.011),'Iris')
        ellipsoid('Pupil_'+str(s),(s*.052,-.1015,1.843),(.005,.002,.009),'Ink')
        ellipsoid('EyeGlint_'+str(s),(s*.049,-.1035,1.847),(.003,.0012,.003),'Hair')
        tube('UpperLid_'+str(s),[(s*.023,-.091,1.842),(s*.045,-.100,1.853),(s*.069,-.092,1.853),(s*.087,-.080,1.852)],[.002,.0035,.0035,.001],mat='Ink',sides=8)
        tube('Brow_'+str(s),[(s*.025,-.079,1.874),(s*.047,-.084,1.881),(s*.077,-.073,1.876)],[.003,.005,.001],mat='Hair',sides=8)
        tube('CheekMark_'+str(s),[(s*.079,-.063,1.818),(s*.098,-.043,1.827),(s*.106,-.026,1.835)],[.001,.004,.001],mat='Markings',sides=6)
    tube('Mouth', [(-.034,-.073,1.777),(0,-.087,1.773),(.034,-.073,1.777)],[.0015,.002,.0015],mat='Ink',sides=6)
    for s in (-1,1):
        tube('Fang_'+str(s),[(s*.024,-.082,1.777),(s*.024,-.084,1.766)],[.0035,.0008],mat='EyeWhite',sides=8)
    # Scalp and many tapered, deliberately chunky locks are editable individual meshes.
    ellipsoid('HairCrown',(0,.030,1.925),(.118,.106,.060),'Hair')
    for s in (-1,1):
        for j in range(3):
            x=.085+.021*j
            tube('FaceLock_'+str(s)+'_'+str(j),[(s*x,.006,1.948),(s*(x+.020),-.056,1.88),(s*(x+.025),-.071,1.77),(s*(x+.064),-.025,1.701+j*.020)],[.027,.032,.023,.001],[.015,.022,.016,.001])
    for row in range(3):
        count=7 if row==0 else 9
        for j in range(count):
            a=(j/(count-1)-.5)*2; x=a*(.10+.025*row)
            z=1.94-row*.08; end=1.08+abs(a)*.16-row*.06
            tube('BackLock_%d_%d'%(row,j),[(x,.080,z),(x*1.7,.16,z-.15),(x*2.5+.018*math.sin(j),.23,z-.34),(x*2.8-.02*math.sin(j),.245,end+.09),(x*3.0+.04*math.sin(j),.22,end)],[.032,.048,.055,.038,.001],[.020,.035,.035,.025,.001])
    tailpts=[(0,.18,1.04),(0,.36,.94),(.14,.48,.70),(.41,.42,.68),(.62,.25,.91),(.68,.16,1.22)]
    tube('Tail',tailpts,[.045,.038,.031,.024,.019,.012],mat='PlainSkin',sides=12,steps=6)
    tube('TailSpade',[(.68,.16,1.19),(.69,.16,1.29),(.75,.16,1.39)],[.018,.064,.001],[.012,.019,.001],mat='Horn',sides=12)
    return tailpts

def panel(name,rows,mat='Cloth'):
    # rows contain center xyz, half-width. Transverse sag adds broad drapery folds.
    verts=[]; faces=[]; n=12
    for i,(x,y,z,w) in enumerate(rows):
        for j in range(n+1):
            u=2*j/n-1; verts.append((x+w*u,y-.012*math.cos(3*math.pi*u)*math.sin(math.pi*i/max(1,len(rows)-1)),z))
    for i in range(len(rows)-1):
        for j in range(n):
            a=i*(n+1)+j; faces.append((a,a+1,a+n+2,a+n+1))
    o=mesh_object(name,verts,faces,mat)
    solid=o.modifiers.new('FabricThickness','SOLIDIFY'); solid.thickness=.004
    bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=solid.name)
    return o

def make_outfit():
    for s in (-1,1):
        verts=[]; faces=[]; n=12; steps=25
        for i in range(steps):
            t=i/(steps-1); z=1.712-.506*t; cx=.272+.100*math.sin(math.pi*t)-.113*t
            w=.032+.053*math.sin(math.pi*t)
            for j in range(n+1):
                u=2*j/n-1; x=cx+w*u
                q=((x-.185)/.229)**2+((z-1.452)/.255)**2
                y=-.205-.249*math.sqrt(max(0,1-q))-.012 if q<1 else -.14
                if t<.16: y=y*(t/.16)+(-.03)*(1-t/.16)
                if t>.90: y=y*(1-t)/.10+(-.17)*(t-.90)/.10
                verts.append((s*x,y,z))
        for i in range(steps-1):
            for j in range(n):
                a=i*(n+1)+j; quad=(a,a+1,a+n+2,a+n+1); faces.append(quad if s>0 else tuple(reversed(quad)))
        o=mesh_object('ChestDrape_'+str(s),verts,faces,'Cloth')
        solid=o.modifiers.new('FabricThickness','SOLIDIFY'); solid.thickness=.004; bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=solid.name)
        panel('BackStrap_'+str(s),[(s*.272,.03,1.712,.036),(s*.23,.15,1.59,.045),(s*.15,.172,1.38,.046),(s*.07,.155,1.21,.05)])
    panel('FrontDrape',[(0,-.178,1.208,.183),(0,-.205,1.10,.165),(0,-.226,.94,.139),(0,-.213,.75,.128),(0,-.194,.55,.125),(0,-.18,.37,.100),(0,-.17,.32,.032)])
    panel('RearDrape',[(0,.177,1.208,.150),(0,.309,1.03,.143),(0,.30,.88,.135),(0,.25,.70,.124),(0,.20,.49,.105),(0,.18,.40,.065)])
    verts=[]; faces=[]; n=64
    for z in (1.172,1.229):
        for j in range(n):
            a=2*math.pi*j/n; verts.append((.237*math.cos(a),.170*math.sin(a),z))
    for j in range(n): faces.append((j,(j+1)%n,(j+1)%n+n,j+n))
    o=mesh_object('WaistSash',verts,faces,'Ink'); solid=o.modifiers.new('SashThickness','SOLIDIFY'); solid.thickness=.007; bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=solid.name)
    for s in (-1,1):
        tube('SashLoop_'+str(s),[(.065,-.184,1.203),(.065+s*.041,-.193,1.217),(.065+s*.041,-.196,1.186),(.065,-.184,1.203)],[.009]*4,mat='Ink',sides=8)
        tube('SashCord_'+str(s),[(.065,-.184,1.20),(.065+s*.018,-.218,1.11),(.065+s*.027,-.222,1.04)],[.009,.007,.004],mat='Ink',sides=8)

def bone(name,a,b,parent=None,deform=True):
    BONES[name]=(Vector(a),Vector(b),parent,deform)

def make_rig(tailpts):
    global RIG
    bone('Root',(0,0,0),(0,0,.15),deform=False)
    bone('Pelvis',(0,0,.95),(0,0,1.10),'Root')
    bone('Spine01',(0,0,1.10),(0,0,1.30),'Pelvis')
    bone('Spine02',(0,0,1.30),(0,0,1.48),'Spine01')
    bone('Chest',(0,0,1.48),(0,0,1.67),'Spine02')
    bone('Neck',(0,0,1.67),(0,0,1.78),'Chest')
    bone('Head',(0,0,1.78),(0,0,1.96),'Neck')
    bone('Jaw',(0,-.035,1.79),(0,-.08,1.75),'Head')
    for s,suffix in [(1,'L'),(-1,'R')]:
        shoulder=(s*.325,0,1.61); elbow=(s*.489,-.008,1.296); wrist=(s*.586,-.020,1.06)
        bone('Clavicle.'+suffix,(s*.04,0,1.63),shoulder,'Chest')
        bone('UpperArm.'+suffix,shoulder,elbow,'Clavicle.'+suffix)
        bone('UpperArmTwist.'+suffix,Vector(shoulder).lerp(Vector(elbow),.5),elbow,'UpperArm.'+suffix)
        bone('Forearm.'+suffix,elbow,wrist,'UpperArm.'+suffix)
        bone('ForearmTwist.'+suffix,Vector(elbow).lerp(Vector(wrist),.5),wrist,'Forearm.'+suffix)
        bone('Hand.'+suffix,wrist,(s*.610,-.022,.946),'Forearm.'+suffix)
        for f,label in enumerate(['Index','Middle','Ring','Little']):
            x=s*(.565+f*.026); z=.951-abs(f-1)*.007; length=[.092,.108,.099,.079][f]
            for k in range(3):
                a=(x+s*.016*k/3,-.022-.005*k/3,z-length*k/3); b=(x+s*.016*(k+1)/3,-.022-.005*(k+1)/3,z-length*(k+1)/3)
                bone(f'{label}{k+1}.{suffix}',a,b,'Hand.'+suffix if k==0 else f'{label}{k}.{suffix}')
        for k in range(3):
            a=Vector((s*.565,-.021,1.013)).lerp(Vector((s*.536,-.042,.944)),k/3); b=Vector((s*.565,-.021,1.013)).lerp(Vector((s*.536,-.042,.944)),(k+1)/3)
            bone(f'Thumb{k+1}.{suffix}',a,b,'Hand.'+suffix if k==0 else f'Thumb{k}.{suffix}')
        hip=(s*.184,.012,.955); knee=(s*.199,-.025,.545); ankle=(s*.207,.015,.145)
        bone('Thigh.'+suffix,hip,knee,'Pelvis'); bone('ThighTwist.'+suffix,Vector(hip).lerp(Vector(knee),.5),knee,'Thigh.'+suffix)
        bone('Shin.'+suffix,knee,ankle,'Thigh.'+suffix); bone('Foot.'+suffix,ankle,(s*.207,-.15,.05),'Shin.'+suffix)
        bone('Toe.'+suffix,(s*.207,-.15,.05),(s*.207,-.24,.04),'Foot.'+suffix)
    for i in range(len(tailpts)-1): bone('Tail%02d'%i,tailpts[i],tailpts[i+1],'Pelvis' if i==0 else 'Tail%02d'%(i-1))
    bone('Tail05',tailpts[-1],(.75,.16,1.39),'Tail04')
    for s,label in [(-1,'R'),(1,'L')]:
        for k in range(3): bone(f'Hair{k}.{label}',(s*.15,.17,1.83-k*.24),(s*.20,.22,1.59-k*.24),'Head' if k==0 else f'Hair{k-1}.{label}')
    data=bpy.data.armatures.new('YokaiDeformationRig'); RIG=bpy.data.objects.new('YokaiRig',data); bpy.context.collection.objects.link(RIG)
    bpy.ops.object.select_all(action='DESELECT'); RIG.select_set(True); bpy.context.view_layer.objects.active=RIG; bpy.ops.object.mode_set(mode='EDIT')
    for name,(a,b,parent,deform) in BONES.items():
        eb=data.edit_bones.new(name); eb.head=a; eb.tail=b; eb.use_deform=deform
        if parent: eb.parent=data.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT'); RIG.show_in_front=True
    return RIG

def segment_distance(p,a,b):
    ab=b-a; t=max(0,min(1,(p-a).dot(ab)/ab.length_squared)); return (p-a-t*ab).length

def candidates(o,p):
    if o.name.startswith(('Horn','Ear','Eye','Iris','Pupil','Brow','Mouth','Fang','Cheek','FaceLock','HairCrown','UpperLid')): return ['Head']
    if o.name.startswith('BackLock'): return ['Head']+['Hair%d.%s'%(k,'L' if p.x>=0 else 'R') for k in range(3)]
    if o.name.startswith('Tail'): return ['Tail%02d'%i for i in range(6)]
    if o.name.startswith(('Sash','Waist','FrontDrape','RearDrape')): return ['Pelvis']
    if o.name.startswith(('ChestDrape','BackStrap')): return ['Spine01','Spine02','Chest']
    side='L' if p.x>=0 else 'R'; x=abs(p.x); z=p.z
    if z>1.73: return ['Head','Neck']
    if x>.53 and z<1.07:
        return ['Hand.'+side,'Forearm.'+side]+[n for n in BONES if n.endswith('.'+side) and n.startswith(('Index','Middle','Ring','Little','Thumb'))]
    if x>.31 and z>1.02: return ['Chest','Clavicle.'+side,'UpperArm.'+side,'UpperArmTwist.'+side,'Forearm.'+side,'ForearmTwist.'+side,'Hand.'+side]
    if z<1.0: return ['Pelvis','Thigh.'+side,'ThighTwist.'+side,'Shin.'+side,'Foot.'+side,'Toe.'+side]
    return ['Pelvis','Spine01','Spine02','Chest','Neck']

def bind(o):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    # UV and tangent streams are required even while materials remain simple.
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.quads_convert_to_tris(); bpy.ops.uv.smart_project(island_margin=.01); bpy.ops.object.mode_set(mode='OBJECT')
    groups={n:o.vertex_groups.new(name=n) for n in BONES if BONES[n][3]}
    for v in o.data.vertices:
        nearest=sorted([(segment_distance(v.co,BONES[n][0],BONES[n][1]),n) for n in candidates(o,v.co)])[:4]
        weights=[1/(d+.018)**5 for d,n in nearest]; total=sum(weights)
        for (d,n),w in zip(nearest,weights):
            if w/total>.00001: groups[n].add([v.index],w/total,'REPLACE')
    o.parent=RIG; mod=o.modifiers.new('DeformationSkin','ARMATURE'); mod.object=RIG


def make_correctives(body):
    body.shape_key_add(name='Basis')
    for label in ('ShoulderVolume','HipFlexionVolume'):
        key=body.shape_key_add(name=label)
        for v in key.data:
            p=v.co; x=abs(p.x)
            if label=='ShoulderVolume':
                strength=.014*math.exp(-((x-.30)/.13)**2-((p.z-1.60)/.11)**2)
                p.y+=strength*(1 if p.y>0 else -1)
            else:
                strength=.017*math.exp(-((x-.19)/.15)**2-((p.z-1.0)/.16)**2)
                if p.y>0: p.y+=strength
    return body.data.shape_keys

def animate(keys):
    for name,frame in POSES:
        for p in RIG.pose.bones: p.rotation_mode='XYZ'; p.rotation_euler=(0,0,0); p.location=(0,0,0)
        def rotate(n,x=0,y=0,z=0): RIG.pose.bones[n].rotation_euler=tuple(math.radians(v) for v in (x,y,z))
        if name=='overhead':
            rotate('UpperArm.L',z=-145); rotate('UpperArm.R',z=145); rotate('Forearm.L',z=-12); rotate('Forearm.R',z=12)
        if name=='crouch':
            RIG.pose.bones['Root'].location.z=-.29
            for side in ('L','R'): rotate('Thigh.'+side,x=-74); rotate('Shin.'+side,x=122); rotate('Foot.'+side,x=-48)
            rotate('Spine01',x=14); rotate('Spine02',x=10)
        if name=='high_kick':
            rotate('Thigh.L',x=-110); rotate('Shin.L',x=10); rotate('Spine01',x=-12); rotate('UpperArm.R',x=-48,z=28)
        if name=='torso_twist':
            rotate('Spine01',y=18); rotate('Spine02',y=25); rotate('Chest',y=20); rotate('Head',y=-20)
            rotate('UpperArm.L',x=-40); rotate('Forearm.L',z=-55)
        if name=='jump':
            RIG.pose.bones['Root'].location.z=.40
            rotate('Thigh.L',x=-28); rotate('Shin.L',x=62); rotate('Thigh.R',x=-45); rotate('Shin.R',x=80)
            rotate('UpperArm.L',z=-68); rotate('UpperArm.R',z=68)
        if name=='knockdown':
            rotate('Root',x=86); RIG.pose.bones['Root'].location=(0,-.45,.21)
            rotate('Thigh.L',x=-15); rotate('Forearm.R',x=-35); rotate('Head',x=-15)
        for p in RIG.pose.bones:
            p.keyframe_insert(data_path='rotation_euler',frame=frame,group=p.name); p.keyframe_insert(data_path='location',frame=frame,group=p.name)
        for key in keys.key_blocks:
            if key.name=='Basis': continue
            key.value=float((key.name=='ShoulderVolume' and name in ('overhead','jump')) or (key.name=='HipFlexionVolume' and name in ('crouch','high_kick')))
            key.keyframe_insert(data_path='value',frame=frame)


def export_regions(out):
    # Low-resolution spherified-cube tetrahedral cages. No claim of anatomical layers.
    regions=[]; n=4
    def godot(p): return [p[0],p[2],-p[1]]
    for kind,cx,cy,cz,rx,ry,rz,support,bone_name in [('breast',.185,-.205,1.452,.275,.300,.305,-1,'Chest'),('glute',.164,.117,1.005,.265,.245,.270,1,'Pelvis')]:
        for s in (-1,1):
            nodes=[]; attaches=[]; ids=lambda i,j,k:(k*(n+1)+j)*(n+1)+i
            for k in range(n+1):
                for j in range(n+1):
                    for i in range(n+1):
                        x,y,z=[2*t/n-1 for t in (i,j,k)]
                        qx=x*math.sqrt(1-y*y/2-z*z/2+y*y*z*z/3); qy=y*math.sqrt(1-z*z/2-x*x/2+z*z*x*x/3); qz=z*math.sqrt(1-x*x/2-y*y/2+x*x*y*y/3)
                        nodes.append(godot((s*cx+rx*qx,cy+ry*qy,cz+rz*qz)))
                        depth=support*qy
                        if depth<-.50: attaches.append({'vertex':len(nodes)-1,'compliance':0.0})
                        elif depth<-.10: attaches.append({'vertex':len(nodes)-1,'compliance':2e-6*(depth+.50)/.40})
            tets=[]
            for k in range(n):
                for j in range(n):
                    for i in range(n):
                        a,b,c,d,e,f,g,h=[ids(i+di,j+dj,k+dk) for di,dj,dk in [(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)]]
                        tets.extend([[a,b,c,g],[a,c,d,g],[a,d,h,g],[a,h,e,g],[a,e,f,g],[a,f,b,g]])
            regions.append({'name':kind+('.L' if s>0 else '.R'),'bone':bone_name,'center':godot((s*cx,cy,cz)),'radii':[rx,rz,ry],'outwardZ':-support,'nodes':nodes,'tetrahedra':tets,'attachments':attaches,'youngModulus':9000 if kind=='breast' else 18000,'poissonRatio':.499,'density':1000})
    doc={'schemaVersion':1,'coordinateSystem':'glTF Y-up metres; front +Z','regions':regions,'limitations':['Single skeletal support per region with spatially graded compliance.','Uniform elastic material, no biological calibration or skin/muscle layers.','Cages are authoring prototypes, not final fitted tetrahedral anatomy.']}
    (out/'tissue-regions.json').write_text(json.dumps(doc,separators=(',',':')),encoding='utf8')
    return doc

def build_stage():
    scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.cycles.samples=24
    scene.render.resolution_x=900; scene.render.resolution_y=1050; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=False
    scene.view_settings.view_transform='Standard'; scene.view_settings.look='Medium High Contrast' if 'Medium High Contrast' in [] else 'None'
    scene.world.color=(.22,.22,.22)
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.012)); floor=bpy.context.object; floor.name='PreviewFloor'; floor.data.materials.append(MATS['Stage'])
    for loc,power,size in [((3,-4,5),550,4),((-3,-1,3),350,3),((0,3,4),650,3)]:
        bpy.ops.object.light_add(type='AREA',location=loc); light=bpy.context.object; light.data.energy=power; light.data.shape='DISK'; light.data.size=size
        light.rotation_euler=(Vector((0,0,1.1))-light.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=(0,-5,1.20)); scene.camera=bpy.context.object; scene.camera.data.type='ORTHO'; scene.camera.data.ortho_scale=2.48
    return scene.camera

def inspect(body):
    import bmesh
    bm=bmesh.new(); bm.from_mesh(body.data); nonmanifold=sum(not e.is_manifold for e in bm.edges); bm.free()
    bad_weights=0
    for o in PARTS:
        for v in o.data.vertices:
            weights=[g.weight for g in v.groups]
            if not weights or abs(sum(weights)-1)>.001 or len(weights)>4: bad_weights+=1
    if nonmanifold or bad_weights: raise ValueError(f'Body nonmanifold edges={nonmanifold}; bad skin weights={bad_weights}')
    return {'bodyVertices':len(body.data.vertices),'bodyTriangles':sum(len(p.vertices)-2 for p in body.data.polygons),'meshObjects':len(PARTS),'bones':len(BONES),'bodyNonmanifoldEdges':nonmanifold,'invalidSkinWeights':bad_weights}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]); out=args.out.resolve(); out.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1; scene.frame_start=1; scene.frame_end=211; scene.render.fps=30
    for name,color,rough in [('Skin','777b91',.62),('PlainSkin','777b91',.62),('Markings','44475e',.68),('Hair','eee9ef',.55),('Horn','292839',.48),('Cloth','d8ccb8',.90),('Ink','24232a',.80),('EyeWhite','d5d6e5',.35),('Iris','777fb3',.38),('Stage','414552',.85)]: material(name,color,rough)
    body=make_body(); tailpts=make_details(); make_outfit(); make_rig(tailpts)
    for o in PARTS: bind(o)
    keys=make_correctives(body); animate(keys); scene.frame_set(1); camera=build_stage()
    metrics=inspect(body); regions=export_regions(out)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'character-blockout.blend'))
    bpy.ops.object.select_all(action='DESELECT'); RIG.select_set(True)
    for o in PARTS: o.select_set(True)
    bpy.context.view_layer.objects.active=RIG
    bpy.ops.export_scene.gltf(filepath=str(out/'character-blockout.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=False,export_texcoords=True,export_normals=True,export_tangents=True,export_animations=True,export_animation_mode='SCENE',export_anim_scene_split_object=False,export_nla_strips_merged_animation_name='ValidationPoses',export_frame_range=True,export_force_sampling=True,export_skins=True,export_morph=True,export_morph_animation=True,export_cameras=False,export_lights=False)
    views=[('front',(0,-5,1.16),1),('three-quarter',(3,-5,1.8),1),('side',(5,0,1.17),1),('back',(0,5,1.17),1),('overhead',(3,-5,1.8),31),('crouch',(3,-5,1.8),61),('high-kick',(3,-5,1.8),91)]
    for name,loc,frame in views:
        scene.frame_set(frame); camera.location=loc; camera.rotation_euler=(Vector((0,0,1.08))-camera.location).to_track_quat('-Z','Y').to_euler(); scene.render.filepath=str(out/(name+'.png')); bpy.ops.render.render(write_still=True)
    scene.frame_set(1); camera.location=(3,-5,1.8); camera.rotation_euler=(Vector((0,0,1.08))-camera.location).to_track_quat('-Z','Y').to_euler(); bpy.ops.wm.save_as_mainfile(filepath=str(out/'character-blockout.blend'))
    manifest={'schemaVersion':1,'milestone':'002 initial character blockout','sourceCommit':os.getenv('GITHUB_SHA'),'blender':bpy.app.version_string,'status':'early proportions and deformation prototype; not finished art or game-ready acceptance','metrics':metrics,'poses':[{'name':n,'frame':f,'seconds':(f-1)/30} for n,f in POSES],'paletteSRGB':{'skin':'777b91','cloth':'d8ccb8','hair':'eee9ef','horn':'292839'},'regionCount':len(regions['regions']),'limitations':['Procedural voxel-union topology needs anatomical retopology.','Distance-based skinning and two generic volume correctives need pose-specific refinement.','Hair and garments are skinned placeholders, not independent physics.','Validation clip contains test poses, not polished locomotion.','Original-image likeness still needs rendered review.'],'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file() and p.suffix in ('.blend','.glb','.json','.png')}}
    (out/'character-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8'); print(json.dumps(metrics)); print('YOKAI_CHARACTER_BUILD_PASS')

if __name__=='__main__': main()
