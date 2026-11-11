"""Anatomy-first Character01 reconstruction from Blender's CC0 realistic female.
Metres; source coordinates X lateral, -Y front, +Z up. Garments never shape the body.
"""
from __future__ import annotations
import bpy
import numpy as np
from pathlib import Path
HEIGHT = 1.95
SOURCE_HEIGHT = 1.641334056854248
SCALE = HEIGHT / SOURCE_HEIGHT

def smooth(a, b, x):
    t = np.clip((x-a)/(b-a), 0, 1)
    return t*t*(3-2*t)

def gauss(x, c, s):
    return np.exp(-((x-c)/s)**2)

def physique(src, eyelids=True):
    p = np.array(src, dtype=np.float64, copy=True)
    x, y, z = p.T
    ax = np.abs(x)
    sg = np.where(x >= 0, 1., -1.)
    q = p.copy()
    width = np.interp(z, [0,.25,.46,.65,.81,.91,1.02,1.11,1.22,1.31,1.38,1.43,1.53,1.65],
                        [1.04,1.08,1.10,1.14,1.27,1.22,1.13,1.12,1.12,1.09,1.20,1.04,1.04,1.04])
    torso = 1-smooth(.17,.23,ax)
    q[:,0] = x*(1+(width-1)*torso)
    glute = gauss(z,.827,.114)*smooth(-.015,.075,y)
    q[:,1] += .044*glute
    q[:,0] += sg*.015*gauss(z,.815,.125)*gauss(ax,.135,.10)
    for side in (-1.,1.):
        sidegate = smooth(.04,.10,side*x)
        for a,b,amount,spread in [((side*.158,.012,1.31),(side*.244,.010,1.07),.43,.062),
                                  ((side*.244,.01,1.07),(side*.343,-.017,.866),.29,.052),
                                  ((side*.087,.008,.828),(side*.112,-.009,.454),.24,.105),
                                  ((side*.112,-.009,.454),(side*.139,.02,.092),.20,.070)]:
            a=np.array(a); b=np.array(b); v=b-a
            t=(p-a)@v/(v@v)
            center=a+np.clip(t,0,1)[:,None]*v
            radial=p-center; dist=np.linalg.norm(radial,axis=1)
            envelope=np.sin(np.pi*np.clip(t,0,1))**.8
            gate=(1-smooth(spread,spread*1.8,dist))*sidegate
            q += radial*(amount*envelope*gate)[:,None]
        center=np.array((side*.169,.013,1.291)); d=p-center
        w=np.exp(-((d[:,0]/.061)**2+(d[:,1]/.075)**2+(d[:,2]/.081)**2))*sidegate
        q += d*(.30*w)[:,None]
    neck=gauss(z,1.375,.066)*(1-smooth(.065,.11,ax))
    q[:,0] += x*.16*neck
    q[:,1] += (y+.014)*.14*neck
    # Scale the existing rounded breast patch, not the entire pectoral silhouette.
    front=1-smooth(-.072,-.025,y)
    rho=np.sqrt(((ax-.076)/.079)**2+((z-1.185)/.090)**2)
    region=(1-smooth(.52,1.12,rho))*front*smooth(.010,.025,ax)*smooth(1.102,1.124,z)
    target=p.copy()
    target[:,0]=sg*(.113+(ax-.076)*1.46)
    target[:,1]=-.085+(y+.085)*2.12
    target[:,2]=1.224+(z-1.224)*1.46-.040
    q += (target-p)*region[:,None]
    shoulder_top=gauss(z,1.335,.052)*gauss(ax,.176,.047)
    q[:,2] -= .018*shoulder_top
    traps=gauss(z,1.351,.041)*gauss(ax,.081,.036)*smooth(-.06,-.015,y)
    q[:,2] += .011*traps
    abs_gate=(1-smooth(-.095,-.06,y))*(1-smooth(.095,.135,ax))
    abdomen=np.zeros(len(p))
    for zz,hh,amp in [(1.096,.025,.024),(1.043,.024,.028),(.991,.027,.020)]:
        abdomen += amp*np.exp(-((ax-.042)/.029)**4-((z-zz)/hh)**4)
    alba=.0034*gauss(x,0,.008)*gauss(z,1.05,.115)
    q[:,1] += (alba-abdomen)*abs_gate
    oblique=gauss(ax,.091+.19*(z-1.03),.019)*gauss(z,1.054,.093)*front
    q[:,1] -= .0055*oblique
    for zz in [1.123,1.163,1.203]:
        serr=gauss(ax,.122,.023)*gauss(z,zz+.38*(ax-.12),.013)*front
        q[:,1] -= .003*serr
    pect=gauss(ax,.074,.072)*gauss(z,1.275,.036)*front
    q[:,1] -= .009*pect
    q[:,1] += .007*gauss(z,.984,.08)*front*(1-smooth(.09,.15,ax))
    for side in (-1.,1.):
        bicep=gauss(x,side*.218,.046)*gauss(z,1.179,.083)*(1-smooth(-.016,.012,y))
        q[:,1] -= .012*bicep
        tricep=gauss(x,side*.208,.049)*gauss(z,1.188,.091)*smooth(.018,.045,y)
        q[:,1] += .010*tricep
        quad=gauss(x,side*.099,.060)*gauss(z,.640,.137)*(1-smooth(-.055,-.010,y))
        q[:,1] -= .014*quad
        vastus=gauss(x,side*.063,.032)*gauss(z,.505,.063)*(1-smooth(-.045,-.005,y))
        q[:,1] -= .006*vastus
    head=smooth(1.409,1.452,z)
    q[:,0] += x*.025*head
    cheeks=gauss(ax,.047,.024)*gauss(z,1.495,.034)*(1-smooth(-.07,-.03,y))
    q[:,0] += sg*.0022*cheeks
    q[:,1] -= .0014*cheeks
    lift=.0022*smooth(.025,.050,ax)*gauss(z,1.536,.027)*(1-smooth(-.07,-.03,y))
    q[:,2] += lift
    if eyelids:
        eyezone=gauss(ax,.033,.021)*(1-smooth(-.086,-.065,y))
        q[:,2] -= .0030*gauss(z,1.544,.008)*eyezone
        q[:,2] += .0010*gauss(z,1.527,.007)*eyezone
    ear=smooth(1.500,1.531,z)*(1-smooth(1.531,1.545,z))*smooth(.069,.079,ax)*smooth(-.075,-.055,y)*(1-smooth(-.025,.002,y))
    q[:,0] += sg*.028*ear
    q[:,2] += .023*ear
    return q*SCALE

def load_body(source: Path, detail=1):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(source),link=False) as (src,dst):
        dst.objects=[n for n in src.objects if n.startswith('GEO-body_female_realistic')]
    for o in dst.objects:
        bpy.context.collection.objects.link(o)
        o.hide_set(False); o.hide_viewport=False; o.hide_render=False
    body=bpy.data.objects['GEO-body_female_realistic']
    body.location=(0,0,0)
    bpy.context.view_layer.update()
    eyes=[o for o in dst.objects if o!=body]
    for o in eyes:
        mat=o.matrix_world.copy();o.parent=None;o.matrix_world=mat
        bpy.context.view_layer.objects.active=o;o.select_set(True)
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        o.select_set(False)
    bpy.context.view_layer.objects.active=body;body.select_set(True)
    for mod in list(body.modifiers):
        if mod.type=='MULTIRES':mod.levels=detail;mod.render_levels=detail
        bpy.ops.object.modifier_apply(modifier=mod.name)
    for o in [body]+eyes:
        o.name='Body' if o==body else ('Eye.L' if '.L' in o.name else 'Eye.R')
        co=np.empty(len(o.data.vertices)*3)
        o.data.vertices.foreach_get('co',co);co=co.reshape(-1,3)
        attr=o.data.attributes.new('source_position','FLOAT_VECTOR','POINT')
        attr.data.foreach_set('vector',co.flatten())
        shaped=physique(co,eyelids=(o==body))
        o.data.vertices.foreach_set('co',shaped.flatten());o.data.update()
        for p in o.data.polygons:p.use_smooth=True
        o.data.materials.clear()
        if o.data.has_custom_normals:
            bpy.context.view_layer.objects.active=o
            try:bpy.ops.mesh.customdata_custom_splitnormals_clear()
            except RuntimeError:pass
    return body,eyes
