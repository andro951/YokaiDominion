"""Editable, exportable curved-lock hairstyle for the anatomical replacement."""
from __future__ import annotations
import math, random
import bpy
import numpy as np
from geometry import mesh, strand, tube, catmull
from materials import base, linear


def make_hair(mat, body):
    rng = random.Random(3103)
    out = []
    data = body.data
    src = np.empty(len(data.vertices)*3)
    data.attributes['source_position'].data.foreach_get('vector', src)
    src = src.reshape(-1,3)
    keep = []
    for p in data.polygons:
        if all(src[i,2] > (1.607-.27*abs(src[i,0]) if src[i,1]<-.052 else 1.548) for i in p.vertices):
            keep.append(tuple(p.vertices))
    used = sorted({i for p in keep for i in p})
    mapping = {a:i for i,a in enumerate(used)}
    verts = [tuple(data.vertices[i].co+data.vertices[i].normal*.0012) for i in used]
    faces = [tuple(mapping[i] for i in p) for p in keep]
    capmat, bs = base('Hair roots - soft silver', (.64,.66,.72), .54)
    cap = mesh('Hair scalp',verts,faces,capmat)
    sub = cap.modifiers.new('Hairline smoothing','SUBSURF')
    sub.levels = sub.render_levels = 1
    out.append(cap)
    variants = []
    for j in range(5):
        m = mat['hair'].copy()
        m.name = 'Silver lock tone '+str(j)
        ramp = next((n for n in m.node_tree.nodes if n.type=='VALTORGB'),None)
        if ramp:
            factor = .88+.03*j
            for el in ramp.color_ramp.elements:
                c = el.color[:]
                el.color = (*[min(1,x*factor) for x in c[:3]],1)
        variants.append(m)
    guides = []
    for layer,count in enumerate([20,18,15]):
        for j,s in enumerate(np.linspace(-1,1,count)):
            phase = j*1.71+layer*.63
            endz = [1.025,1.18,1.36][layer]+.065*abs(s)+.025*math.sin(j*2.35)
            rootx, spread = s*.093, [.235,.245,.218][layer]
            rootz = 1.941-.048*abs(s)
            pts = []
            for k,t in enumerate(np.linspace(0,1,9)):
                x = (1-t)*rootx+t*s*spread+.019*math.sin(2.4*math.pi*t+phase)*math.sin(math.pi*t)
                y = .060+.12*t+.042*math.sin(math.pi*t)+.012*math.sin(2.6*math.pi*t+phase)+layer*.012
                z = rootz*(1-t)+endz*t
                if z<1.2:
                    y = max(y,.215)
                pts.append((x,y,z))
            width = .0215*(1+.10*math.sin(j*1.4))
            radii = [.008,width*.75,width,width*.98,width*.90,width*.82,width*.60,width*.32,.00025]
            guides.append((f'Hair back {layer:02d} {j:02d}',pts,radii,.47,phase))
    for s in (-1,1):
        for j in range(7):
            f = j/6
            pts = [(s*(.046+.035*f),-.030+.070*f,1.945-.018*f),
                   (s*(.095+.018*f),.009+.045*f,1.86-.015*f),
                   (s*(.135+.022*f),.052+.040*f,1.747-.014*f),
                   (s*(.174+.036*f),.094+.040*f,1.63-.015*f),
                   (s*(.188+.055*f),.135+.030*f,1.51-.030*f),
                   (s*(.221+.033*f),.165+.028*f,1.405-.045*f),
                   (s*(.233+.026*f),.196,1.30-.08*f),
                   (s*(.222+.030*f),.213,1.25-.10*f)]
            guides.append((f'Hair side {s} {j}',pts,[.009,.021,.024,.023,.021,.016,.008,.0003],.52,j))
        for j in range(5):
            f = j/4
            pts = [(s*(.005+.009*f),-.112+.021*f,1.958-.005*f),
                   (s*(.040+.012*f),-.144+.010*f,1.946-.011*f),
                   (s*(.078+.016*f),-.164+.010*f,1.911-.018*f),
                   (s*(.104+.015*f),-.173+.020*f,1.848-.030*f),
                   (s*(.111+.020*f),-.170+.029*f,1.785-.035*f),
                   (s*(.124+.025*f),-.158+.030*f,1.728-.037*f),
                   (s*(.143+.024*f),-.132+.028*f,1.713-.035*f)]
            guides.append((f'Hair forelock {s} {j}',pts,[.007,.014,.017,.017,.014,.007,.00025],.57,j*.7))
        for j in range(13):
            f = j/12
            pts = [(s*.004,-.119+.200*f,1.956-.020*f),
                   (s*.038,-.115+.195*f,1.960-.019*f),
                   (s*.073,-.093+.195*f,1.939-.021*f),
                   (s*.102,-.058+.177*f,1.902-.034*f),
                   (s*.115,-.018+.153*f,1.844-.046*f),
                   (s*.117,.038+.123*f,1.778-.065*f)]
            guides.append((f'Hair crown {s} {j}',pts,[.0045,.0115,.0145,.0145,.010,.003],.55,j*.5))
    for index,(name,points,widths,depth,phase) in enumerate(guides):
        material = variants[index%len(variants)]
        lock = strand(name,points,widths,material,n=52,sides=12,depth=depth,phase=phase)
        out.append(lock)
        co = np.array([v.co[:] for v in lock.data.vertices[:-2]]).reshape(52,12,3)
        centers = co.mean(axis=1)
        for k in [3,9]:
            curve = co[:,k,:]*1.015-centers*.015
            radius = .00028 if index%3 else .00038
            out.append(tube(name+' fine strand '+str(k),curve.tolist(),[radius*.7,radius,radius,.000035],
                            variants[(index+2)%5],n=50,sides=5,cap=True))
    for s in (-1,1):
        for j in range(7):
            f = j/6
            pts = [(s*(.06+.015*f),-.01+.10*f,1.93),
                   (s*(.13+.014*f),.03+.10*f,1.82),
                   (s*(.174+.02*f),.08+.10*f,1.65),
                   (s*(.22+.02*f),.14+.10*f,1.52),
                   (s*(.245+.02*f),.18+.08*f,1.42-.10*f)]
            out.append(tube('Loose silver strand',pts,[.00045,.00065,.00050,.00025,.00002],
                            variants[j%5],n=70,sides=5))
    return out
