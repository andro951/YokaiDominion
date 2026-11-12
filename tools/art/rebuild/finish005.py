"""Finish the anatomical art surface and explicitly connected neck fabric."""
import math
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from geometry import ribbon,catmull,tube
from materials import base
import finish_details

def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)

def anatomical_details(body,eyes,mat):
    nail_ids={37,42,43,44,45,47,51,55,59,63,67,71,75,79,83,87,91,95,99,103}
    face_sets=body.data.attributes.get('.sculpt_face_set')
    nail,shader=base('Nails | muted violet keratin',(.24,.215,.30),.30);shader.inputs['Coat Weight'].default_value=.22
    body.data.materials.append(nail);index=len(body.data.materials)-1
    if face_sets:
        for f,fs in zip(body.data.polygons,face_sets.data):
            if fs.value in nail_ids:f.material_index=index
    n=len(body.data.vertices);src=np.empty(n*3);body.data.attributes['source_position'].data.foreach_get('vector',src);src=src.reshape(-1,3)
    q=np.empty(n*3);body.data.vertices.foreach_get('co',q);q=q.reshape(-1,3)
    x,y,z=src.T;ax=np.abs(x);sg=np.sign(x);front=1-smooth(-.10,-.066,y)
    chin=np.exp(-((z-1.438)/.024)**2)*smooth(.016,.043,ax)*front;q[:,0]-=sg*.0018*chin
    nose=np.exp(-((z-1.493)/.014)**2)*(1-smooth(-.14,-.115,y))*np.exp(-(x/.023)**2);q[:,1]+=.0012*nose
    eye=np.exp(-((ax-.033)/.017)**4)*(1-smooth(-.110,-.092,y))
    lid=smooth(1.536,1.541,z)*(1-smooth(1.548,1.555,z))*eye;q[:,2]-=.00135*lid
    body.data.vertices.foreach_set('co',q.ravel());body.data.update()
    for o in bpy.data.objects:
        if o.type=='MESH' and (o.name.startswith('Upper liner') or o.name.startswith('Outer eyelash')):
            for v in o.data.vertices:v.co.z-=.00125*math.exp(-((abs(v.co.x)-.039)/.024)**4)
            o.data.update()
        if o.type=='MESH' and (o.name.startswith('Face wave') or o.name.startswith('Crown sweep')):
            for v in o.data.vertices:
                p=v.co
                if p.y<-.045 and p.z>1.895:
                    w=math.exp(-(p.x/.060)**4)*float(smooth(1.895,1.94,p.z));p.z-=.009*w;p.y-=.008*w
            o.data.update()
    for eye_o in eyes:
        for m in eye_o.data.materials:
            bs=m.node_tree.nodes.get('Principled BSDF')
            if bs:bs.inputs['Roughness'].default_value=.075;bs.inputs['Coat Weight'].default_value=.40;bs.inputs['Coat Roughness'].default_value=.08
    return src

def finish_neck_and_drape(body,src,mat):
    fs=body.data.attributes.get('.sculpt_face_set');arm_ids={9,10,11,12,20,21}|set(range(64,104))
    torsofaces=[p.vertices[:] for p in body.data.polygons if not fs or fs.data[p.index].value not in arm_ids]
    bvh=BVHTree.FromPolygons([v.co for v in body.data.vertices],torsofaces)
    def front(x,z):
        h,_,_,_=bvh.ray_cast(Vector((x,-2,z)),Vector((0,1,0)),4)
        return h.y if h else None
    for o in list(bpy.data.objects):
        if o.name.startswith('Soft nape drape'):bpy.data.objects.remove(o,do_unlink=True)
    for side in (-1.,1.):
        o=bpy.data.objects.get('Loose neck panel '+str(side))
        if o is None:continue
        a=np.array([v.co[:] for v in o.data.vertices]).reshape(115,33,3)
        for i in range(len(a)):
            for j in range(33):
                x,y,z=a[i,j];skin=front(x,z)
                if skin is not None:a[i,j,1]=min(y,skin-.007)
        o.data.vertices.foreach_set('co',a.reshape(-1));o.data.update()
        first=a[0].copy();center=first.mean(0)
        centers=catmull([center,(side*.061,-.073,1.662),(side*.073,-.037,1.681),(side*.075,.005,1.684),(side*.064,.049,1.670),(side*.039,.079,1.653),(0,.086,1.650)],64)
        grid=[]
        for i,c in enumerate(centers):
            t=i/(len(centers)-1);tangent=centers[min(i+1,len(centers)-1)]-centers[max(i-1,0)];tangent/=max(np.linalg.norm(tangent),1e-9)
            normal=np.array([c[0],c[1]-.012,.035]);normal/=max(np.linalg.norm(normal),1e-9)
            lateral=np.cross(tangent,normal);lateral/=max(np.linalg.norm(lateral),1e-9)
            if lateral[0]*side<0:lateral=-lateral
            width=.014+.008*t;row=[]
            for j,u in enumerate(np.linspace(-1,1,33)):
                p=c+width*u*lateral
                if i<8:
                    blend=float(smooth(0,7,i));p=(center+(first[j]-center)+(c-center))*(1-blend)+p*blend
                row.append(p)
            grid.append(row)
        ribbon('Continuous neck fabric '+str(side),grid,mat['cloth'],.0014,1)
        for j in (0,-1):tube('Neck selvedge',[r[j] for r in grid],[.0006,.0006],mat['cloth'],n=64,sides=5)

def install():
    previous=finish_details.build
    def build(body,eyes,mat,bvh,front):
        previous(body,eyes,mat,bvh,front)
        src=anatomical_details(body,eyes,mat);finish_neck_and_drape(body,src,mat)
    finish_details.build=build
