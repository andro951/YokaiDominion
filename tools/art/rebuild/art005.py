"""Anatomy-first art finishing. Real editable geometry; garments never shape the body."""
from __future__ import annotations
import math,random
import bpy
import numpy as np
from mathutils import Vector
from geometry import mesh,tube,ribbon,strand,catmull
from materials import base,linear
import finish_details as old

def sm(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)

def smooth_rows(a,passes=5):
    a=np.asarray(a).copy()
    for _ in range(passes):a[1:-1]=.22*a[:-2]+.56*a[1:-1]+.22*a[2:]
    return a

def garment(body,mat,bvh,front):
    out=[]
    guide=np.array([[.050,1.649,.014],[.070,1.594,.023],[.103,1.532,.034],[.134,1.453,.041],[.145,1.389,.043],[.136,1.312,.040],[.119,1.250,.042],[.092,1.197,.061]])
    profile=catmull(guide,115)
    for side in (-1.,1.):
        grid=[]
        for i,(cx,z,half) in enumerate(profile):
            t=i/(len(profile)-1);row=[]
            for u in np.linspace(-1,1,33):
                x=side*(cx+half*u);zz=z+.004*u*math.sin(math.pi*t);y=front(x,zz,.008)
                if y is None:
                    for inset in np.linspace(.001,.07,50):
                        test=front(x-side*inset,zz,.008)
                        if test is not None:x-=side*inset;y=test;break
                if y is None:y=-.075
                row.append([x,y,zz])
            grid.append(row)
        a=np.array(grid)
        for j in range(a.shape[1]):
            yy=a[:,j,1];start=int(np.argmin(yy[:90]))
            if start<100:
                v=np.linspace(0,1,len(yy)-start);hanging=yy[start]*(1-v)+yy[-1]*v-.006*np.sin(np.pi*v);yy[start:]=np.minimum(yy[start:],hanging)
            baseline=yy.copy();yy[:]=np.minimum(smooth_rows(yy[:,None],8)[:,0],baseline+.001)
        for _ in range(4):a[:,1:-1,1]=np.minimum(a[:,1:-1,1],.24*a[:,:-2,1]+.52*a[:,1:-1,1]+.24*a[:,2:,1])
        for i,t in enumerate(np.linspace(0,1,len(a))):
            for j,u in enumerate(np.linspace(-1,1,a.shape[1])):
                fold=(.0015+.003*np.sin(np.pi*t)**2)*(1+math.sin(3.5*math.pi*u+.9*t));a[i,j,1]-=fold
        obj=ribbon('Loose neck panel '+str(side),a,mat['cloth'],.0014,1);out.append(obj)
        for j in (0,-1):tube('Fine folded selvedge',[p[j] for p in a],[.00065,.00065],mat['cloth'],n=115,sides=6)
    for side in (-1.,1.):
        pts=[(side*.050,-.074,1.649),(side*.067,-.055,1.672),(side*.074,-.01,1.683),(side*.069,.037,1.678),(side*.045,.071,1.660),(0,.083,1.651)]
        out.append(strand('Soft nape drape '+str(side),pts,[.015,.017,.019,.020,.023,.026],mat['cloth'],n=65,sides=14,depth=.11))
    for rear in (False,True):
        grid=[]
        for t in np.linspace(0,1,115):
            row=[]
            for u in np.linspace(-1,1,49):
                width=.158-.072*t**1.7+.018*math.sin(math.pi*t);x=width*u+.008*math.sin(math.pi*t)*math.sin(2*t)
                z=1.197-.795*t-.065*t**7*(1-u*u)+.008*t**8*math.sin(5*u+1)
                wave=(.002+.008*t)*(math.sin(3.4*math.pi*u+.7*t)+.25*math.sin(7*math.pi*u-t))
                if rear:
                    hit,_,_,_=bvh.ray_cast(Vector((x,2,z)),Vector((0,-1,0)),4);surface=hit.y+.009 if hit else .17;y=max(.17+.025*math.sin(math.pi*t),surface)+wave
                else:
                    surface=front(x,z,.009);y=min(-.173-.015*math.sin(math.pi*t),surface if surface is not None else -.173)+wave
                row.append([x,y,z])
            grid.append(row)
        a=np.array(grid);a[:,:,1]=smooth_rows(a[:,:,1],25)
        o=ribbon('Back hanging cloth' if rear else 'Front hanging cloth',a,mat['cloth'],.0014,1);out.append(o)
        for j in (0,-1):tube('Rolled cloth hem',[r[j] for r in a],[.0008,.0008],mat['cloth'],n=110,sides=6)
        tube('Shaped lower hem',a[-1],[.0008,.0008],mat['cloth'],n=60,sides=6)
    points=[]
    for a in np.linspace(0,2*math.pi,200):
        d=Vector((math.cos(a),math.sin(a),0));origin=d*1.;origin.z=1.198;hit,n,_,_=bvh.ray_cast(origin,-d,2)
        p=hit+n*.008 if hit else Vector((.17*math.cos(a),.15*math.sin(a),1.158))
        if p.y<-.10:p.y=min(p.y,-.183)
        if p.y>.10:p.y=max(p.y,.180)
        p.z=1.198+.001*math.sin(2*a);points.append(tuple(p))
    tube('Braided waist cord',points,[.0045,.0045],mat['cord'],n=230,sides=12)
    for phase in (0,math.pi):
        pts=[]
        for i,p in enumerate(points):
            a=2*math.pi*i/(len(points)-1);v=45*a+phase;pts.append(np.array(p)+.0042*np.array([math.cos(a)*math.cos(v),math.sin(a)*math.cos(v),math.sin(v)]))
        tube('Cord braid',pts,[.00075,.00075],mat['cord'],n=600,sides=5)
    cx=.065;y=-.189;z=1.198
    tube('Cord knot',[(cx-.01,y,z),(cx+.008,y-.006,z+.008),(cx+.014,y-.008,z-.004),(cx-.006,y-.005,z-.01),(cx-.01,y,z)],[.004,.004],mat['cord'],n=55,sides=12)
    tube('Long cord end',[(cx,y-.006,z),(cx+.012,y-.017,z-.06),(cx+.006,y-.014,z-.15),(cx+.014,y-.005,z-.20)],[.0033,.0030,.0026,.0018],mat['cord'],n=60,sides=10)
    tube('Short cord end',[(cx+.01,y-.004,z),(cx+.033,y-.018,z-.05),(cx+.035,y-.010,z-.13)],[.0032,.0028,.0018],mat['cord'],n=45,sides=10)
    return out

def resolve_cloth(clothes,bvh):
    for o in clothes:
        for p in o.data.polygons:p.use_smooth=True

def hair(body,mat):
    rng=random.Random(1505);out=[];m=mat['hair'];vv=[];ff=[];n=72
    for j,t in enumerate(np.linspace(0,1,34)):
        for k,a in enumerate(np.linspace(0,2*math.pi,n,endpoint=False)):
            th=.012+t*(1.45+.42*(math.sin(a)+1)/2);vv.append((.108*math.sin(th)*math.cos(a),.004+.089*math.sin(th)*math.sin(a),1.845+.110*math.cos(th)))
            if j:
                p=(j-1)*n+k;q=(j-1)*n+(k+1)%n;ff.append((p,q,q+n,p+n))
    out.append(mesh('Fitted hair scalp',vv,ff,m))
    inner,bs=base('Hair | inner shadow',(.56,.59,.66),.48)
    levels=[(1.933,.062,.055,.026),(1.85,.090,.096,.039),(1.74,.119,.125,.035),(1.62,.148,.165,.037),(1.49,.181,.176,.034),(1.35,.209,.182,.030),(1.20,.225,.156,.023),(1.105,.233,.085,.015),(1.065,.237,.003,.001)]
    cv=[];cf=[]
    for j,(z,cy,rx,ry) in enumerate(levels):
        for k,a in enumerate(np.linspace(0,2*math.pi,56,endpoint=False)):
            cv.append((rx*math.cos(a),cy+ry*math.sin(a),z+.008*math.sin(5*a)*math.sin(j*math.pi/8)))
            if j:
                q=(j-1)*56+k;r=(j-1)*56+(k+1)%56;cf.append((q,r,r+56,q+56))
    core=mesh('Continuous inner mane',cv,cf,inner);sub=core.modifiers.new('Smooth inner volume','SUBSURF');sub.levels=sub.render_levels=2;out.append(core);guides=[]
    for layer,count in enumerate((11,9,7)):
        for j in range(count):
            f=2*j/(count-1)-1;phase=.9*j+.5*layer;endz=1.03+.15*layer+.07*abs(f)+rng.uniform(-.03,.03);pts=[]
            for t in np.linspace(0,1,12):
                wave=math.sin(t*math.pi*4.1+phase)*math.sin(math.pi*t);x=f*(.064+.135*t)+.027*wave
                y=.060+.16*t+.028*math.sin(math.pi*t)+layer*.020+.020*math.cos(t*math.pi*4+phase)*math.sin(math.pi*t)
                z=1.946*(1-t)+endz*t;x+=np.sign(f)*.027*t**7;pts.append((x,y,z))
            w=.030+rng.uniform(-.004,.005)
            guides.append((f'Back wave {layer}-{j}',pts,[.008,.020,w,w*1.05,w,w,w*.98,w*.94,w*.86,w*.72,w*.40,.0005],.68))
    for s in (-1.,1.):
        for j in range(6):
            f=j/5
            pts=[(s*(.045+.035*f),.00+.035*f,1.943-.01*f),(s*(.10+.017*f),.025+.045*f,1.87),(s*(.13+.022*f),.045+.06*f,1.79),(s*(.168+.020*f),.065+.05*f,1.735-.02*f),(s*(.142+.035*f),.082+.055*f,1.665-.025*f),(s*(.199+.025*f),.102+.05*f,1.595-.035*f),(s*(.225+.035*f),.11+.05*f,1.60-.07*f)]
            guides.append((f'Side S wave {s}-{j}',pts,[.008,.022,.031,.033,.030,.018,.0003],.64))
        for j in range(2):
            f=j
            pts=[(s*(.010+.017*f),-.065+.02*f,1.951),(s*(.044+.010*f),-.116+.014*f,1.933),(s*(.077+.016*f),-.133+.02*f,1.892),(s*(.094+.019*f),-.136+.035*f,1.831),(s*(.091+.029*f),-.113+.040*f,1.781-.02*f),(s*(.125+.035*f),-.093+.045*f,1.759-.024*f),(s*(.149+.038*f),-.085+.048*f,1.776-.02*f)]
            guides.append((f'Face wave {s}-{j}',pts,[.005,.018,.023,.021,.018,.011,.0003],.60))
        for j in range(7):
            f=j/6
            pts=[(s*.001,-.071+.143*f,1.952-.006*f),(s*.037,-.079+.153*f,1.961-.015*f),(s*.078,-.056+.15*f,1.943-.022*f),(s*.104,-.013+.128*f,1.897-.026*f),(s*.115,.035+.11*f,1.844-.03*f),(s*.133,.061+.11*f,1.798-.03*f)]
            guides.append((f'Crown sweep {s}-{j}',pts,[.003,.015,.023,.024,.019,.009],.65))
    for i,(name,points,widths,depth) in enumerate(guides):out.append(strand(name,points,widths,m,n=76,sides=16,depth=depth,phase=i*.37))
    return out

_old_horns=old.horns_tail
_old_face=old.eyes_and_face

def horns_tail(mat):
    _old_horns(mat)
    for o in bpy.data.objects:
        if o.type=='MESH' and o.name.startswith('Horn.'):
            for v in o.data.vertices:v.co.z=1.913+.77*(v.co.z-1.913);v.co.x*=1.03
            o.data.update()

def face(body,eyes,mat,bvh,front):
    _old_face(body,eyes,mat,bvh,front)
    for o in bpy.data.objects:
        if o.type=='MESH' and o.name.startswith('Iris.'):
            for m in o.data.materials:
                bs=m.node_tree.nodes.get('Principled BSDF')
                if bs:bs.inputs['Coat Weight'].default_value=.38;bs.inputs['Coat Roughness'].default_value=.10
    a=body.data.attributes.get('source_position');c=body.data.color_attributes.get('Complexion')
    if a and c:
        p=np.empty(len(body.data.vertices)*3);a.data.foreach_get('vector',p);p=p.reshape(-1,3)
        col=np.empty(len(body.data.vertices)*4);c.data.foreach_get('color',col);col=col.reshape(-1,4)
        w=sm(.068,.080,np.abs(p[:,0]))*np.exp(-((p[:,2]-1.519)/.018)**2)*(1-sm(-.02,.008,p[:,1]))
        col[:,:3]=col[:,:3]*(1-w[:,None]*.38)+np.array(linear((.34,.315,.415)))*w[:,None]*.38;c.data.foreach_set('color',col.ravel())

def install():
    old.garment=garment;old.resolve_cloth=resolve_cloth;old.hair=hair;old.horns_tail=horns_tail;old.eyes_and_face=face
