"""Final visual surface/garment pass. Anatomy remains independent of clothing.
Installed after the versioned 005 authoring modules; all changes are reproducible.
"""
from __future__ import annotations
import math
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from geometry import tube, ribbon, catmull
from materials import base, linear
import finish_details

def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)

def coordinates(body):
    n=len(body.data.vertices);p=np.empty(n*3);q=np.empty(n*3)
    body.data.attributes['source_position'].data.foreach_get('vector',p)
    body.data.vertices.foreach_get('co',q)
    return p.reshape(-1,3),q.reshape(-1,3)

def relax(body,q,weight,iterations=12):
    """Alternating Laplacian fairing, restricted to the specified surface mask."""
    edges=np.empty(len(body.data.edges)*2,dtype=np.int32);body.data.edges.foreach_get('vertices',edges);edges=edges.reshape(-1,2)
    a=np.r_[edges[:,0],edges[:,1]];b=np.r_[edges[:,1],edges[:,0]];count=np.bincount(a,minlength=len(q));count=np.maximum(count,1)
    for _ in range(iterations):
        for k in (.46,-.47):
            avg=np.column_stack([np.bincount(a,weights=q[b,i],minlength=len(q))/count for i in range(3)])
            q+=k*weight[:,None]*(avg-q)
    return q

def body_finish(body):
    src,q=coordinates(body);x,y,z=src.T;ax=np.abs(x);sg=np.sign(x)
    front=1-smooth(-.075,-.025,y)
    # Replace excessive, repeated abdominal bulges with broader muscle planes.
    for zz,amp in [(1.096,.0040),(1.043,.0055),(.991,.0035)]:
        q[:,1]+=amp*np.exp(-((ax-.042)/.034)**4-((z-zz)/.027)**4)*front
    # Fair the native inframammary transition, not a separately attached breast ball.
    mask=np.exp(-((ax-.092)/.077)**4-((z-1.181)/.105)**4)*front*smooth(.012,.035,ax)
    q=relax(body,q,mask,20)
    # Keep outer/lower fullness and the sternum clear, without widening the skeleton.
    lower=np.exp(-((ax-.105)/.050)**2-((z-1.154)/.040)**2)*front
    q[:,0]+=sg*.0030*lower;q[:,1]-=.0045*lower;q[:,2]-=.004*lower
    # Slightly firmer cheek plane and a softer jaw transition.
    face=front*smooth(1.44,1.46,z)
    q[:,0]-=sg*.0014*np.exp(-((z-1.452)/.025)**2-((ax-.045)/.035)**2)*face
    q[:,1]-=.0014*np.exp(-((z-1.505)/.019)**2-((ax-.044)/.026)**2)*face
    body.data.vertices.foreach_set('co',q.ravel());body.data.update()
    body['art_revision']='006';body['clothing_shapes_body']=False
    return src

def torso_bvh(body):
    fs=body.data.attributes.get('.sculpt_face_set');exclude={9,10,11,12,20,21}|set(range(64,104))
    faces=[p.vertices[:] for p in body.data.polygons if not fs or fs.data[p.index].value not in exclude]
    return BVHTree.FromPolygons([v.co for v in body.data.vertices],faces)

def fabric_finish(body,mat):
    """Cut loose halter panels on the already-shaped body. No cups or underband."""
    prefixes=('Loose neck panel','Continuous','Soft nape','Fine folded','Rolled cloth','Shaped lower','Neck selvedge','Drape boundary','Neck rolled','Apron','Front hanging cloth','Back hanging cloth','Gathered')
    for o in list(bpy.data.objects):
        if o.type=='MESH' and o.name.startswith(prefixes):bpy.data.objects.remove(o,do_unlink=True)
    bvh=torso_bvh(body)
    def surface(x,z,rear=False):
        h,n,_,_=bvh.ray_cast(Vector((x,2 if rear else -2,z)),Vector((0,-1 if rear else 1,0)),4)
        return h.y if h else None
    # The strap directions converge at the neck; they do not run over the shoulders.
    guide=catmull([[.050,1.645,.013],[.072,1.587,.020],[.107,1.519,.033],[.143,1.450,.043],[.151,1.391,.049],[.140,1.322,.048],[.112,1.247,.045],[.087,1.197,.062]],112)
    for side in (-1.,1.):
        grid=[]
        for i,(cx,z,half) in enumerate(guide):
            t=i/(len(guide)-1);row=[]
            for u in np.linspace(-1,1,31):
                x=side*(cx+half*u);zz=z+.004*math.sin(math.pi*t)*u;support=surface(x,zz)
                if support is None:
                    support=surface(side*(cx+half*max(-1,min(.6,u))),zz)
                if support is None:support=-.065
                row.append([x,support-.0065,zz])
            grid.append(row)
        a=np.array(grid)
        # A taut-envelope only bridges concavities. It never pulls the body inward/up.
        depth=-a[:,:,1];obstacle=depth.copy()
        for _ in range(170):
            avg=depth.copy();avg[1:-1,1:-1]=.25*(depth[:-2,1:-1]+depth[2:,1:-1]+depth[1:-1,:-2]+depth[1:-1,2:])
            avg[1:-1,0]=.50*depth[1:-1,1]+.25*(depth[:-2,0]+depth[2:,0]);avg[1:-1,-1]=.50*depth[1:-1,-2]+.25*(depth[:-2,-1]+depth[2:,-1])
            depth=np.maximum(obstacle,avg-.000025)
        a[:,:,1]=-depth
        for j in range(31):
            start=int(np.argmin(a[:88,j,1]));t=np.linspace(0,1,len(a)-start)
            hanging=a[start,j,1]*(1-t)+a[-1,j,1]*t-.004*np.sin(math.pi*t)
            a[start:,j,1]=np.minimum(a[start:,j,1],hanging)
        for i,t in enumerate(np.linspace(0,1,len(a))):
            for j,u in enumerate(np.linspace(-1,1,31)):
                # Broad curved folds, rather than straight accordion grooves.
                ripple=(.0007+.0021*math.sin(math.pi*t)**2)*(1+math.sin(2.25*math.pi*u+1.8*t+.35*side))
                gather=.0014*(math.exp(-t*10)+math.exp(-(1-t)*10))*(1+math.sin(4*math.pi*u+.6*t))
                a[i,j,1]-=ripple+gather
        o=ribbon('Gathered halter '+str(side),a,mat['cloth'],.0011,2);o['construction']='Loose neck-to-waist drape; no cup, underwire, lift or body shaping'
        for j in (0,-1):tube('Gathered halter hem '+str(side),a[:,j,:],[.00045,.00045],mat['cloth'],n=112,sides=5)
        # Narrow soft neck passage, positioned on the neck surface, not a collar.
        first=a[0];center=first.mean(0)
        path=catmull([center,(side*.061,-.064,1.659),(side*.073,-.021,1.671),(side*.072,.021,1.666),(side*.052,.070,1.645),(0,.084,1.632)],60)
        neck=[]
        for i,c in enumerate(path):
            tan=path[min(i+1,59)]-path[max(0,i-1)];tan/=max(np.linalg.norm(tan),1e-9)
            no=np.array([c[0],c[1],.025]);no/=max(np.linalg.norm(no),1e-9);lat=np.cross(tan,no);lat/=max(np.linalg.norm(lat),1e-9)
            if lat[0]*side<0:lat=-lat
            row=[]
            for j,u in enumerate(np.linspace(-1,1,31)):
                p=c+lat*u*(.013+.004*i/59)
                if i<9:
                    t=float(smooth(0,8,i));p=(first[j]+c-center)*(1-t)+p*t
                h,n,_,d=bvh.find_nearest(Vector(p))
                if i and h and d<.026:p=np.array(h)+np.array(n)*.0035
                row.append(p)
            neck.append(row)
        ribbon('Gathered soft neck passage '+str(side),neck,mat['cloth'],.0011,2)
    for rear in (False,True):
        grid=[]
        for t in np.linspace(0,1,112):
            row=[]
            for u in np.linspace(-1,1,45):
                half=.151-.048*t**1.4+.011*math.sin(math.pi*t)
                x=half*u+.005*math.sin(math.pi*t)*math.sin(1.7*t)
                z=1.197-.735*t-.050*t**5*(1-u*u)+.007*t**7*math.sin(4.3*u+.7)
                sup=surface(x,z,rear);top=surface(.151*u,1.197,rear)
                top=(top if top is not None else (.16 if rear else -.17))+( .006 if rear else -.006)
                free=(.215 if rear else -.202)+(.011 if rear else -.009)*math.sin(math.pi*t)
                v=float(smooth(0,.28,t));y=top*(1-v)+free*v
                if sup is not None:y=max(y,sup+.006) if rear else min(y,sup-.006)
                wave=(.001+.0062*math.sin(math.pi*t*.92))*(math.sin(3.2*math.pi*u+.85*t)+.24*math.sin(6.4*math.pi*u-1.2*t))
                y+=wave;row.append([x,y,z])
            grid.append(row)
        a=np.array(grid)
        for _ in range(16):a[1:-1,:,1]=.20*a[:-2,:,1]+.60*a[1:-1,:,1]+.20*a[2:,:,1]
        o=ribbon('Gathered rear skirt' if rear else 'Gathered front skirt',a,mat['cloth'],.0012,2)
        for j in (0,-1):tube('Gathered skirt edge',a[:,j,:],[.0005,.0005],mat['cloth'],n=112,sides=5)
        tube('Gathered skirt hem',a[-1],[.0005,.0005],mat['cloth'],n=55,sides=5)
        if rear:
            import bmesh
            bm=bmesh.new();bm.from_mesh(o.data)
            remove=[f for f in bm.faces if ((f.calc_center_median().x-.031)/.034)**2+((f.calc_center_median().z-.994)/.039)**2<1]
            bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(o.data);bm.free()

def materials_finish(mat):
    skin=mat['skin'];bs=skin.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Roughness'].default_value=.52;bs.inputs['Specular IOR Level'].default_value=.28
    bs.inputs['Subsurface Weight'].default_value=.055;bs.inputs['Subsurface Scale'].default_value=.0018
    bs.inputs['Subsurface Radius'].default_value=(1,.55,.35)
    for m in bpy.data.materials:
        if not m.use_nodes:continue
        bs=m.node_tree.nodes.get('Principled BSDF')
        if not bs:continue
        if m.name.startswith('Iris'):
            bs.inputs['Roughness'].default_value=.22;bs.inputs['Coat Weight'].default_value=.35
        if m.name.startswith('Hair | ivory'):
            bs.inputs['Roughness'].default_value=.42;bs.inputs['Anisotropic'].default_value=.50
        if m.name.startswith('Cloth'):
            bs.inputs['Roughness'].default_value=.82;bs.inputs['Sheen Weight'].default_value=.23
        if m.name.startswith('Horns'):
            bs.inputs['Roughness'].default_value=.40;bs.inputs['Coat Weight'].default_value=.08

def install():
    previous=finish_details.build
    def build(body,eyes,mat,bvh,front):
        previous(body,eyes,mat,bvh,front)
        body_finish(body);fabric_finish(body,mat);materials_finish(mat)
    finish_details.build=build
