"""Fair loose garment surfaces without altering their anatomical support mesh."""
import math
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from geometry import tube,ribbon,catmull
import finish_details

def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)

def front_envelope(a):
    """Bridge underarm hollows instead of shaping cloth into a rigid cup."""
    depths=-a[:,:,1];fixed=depths.copy()
    for _ in range(180):
        avg=depths.copy()
        avg[1:-1,1:-1]=.25*(depths[:-2,1:-1]+depths[2:,1:-1]+depths[1:-1,:-2]+depths[1:-1,2:])
        avg[1:-1,0]=.42*depths[1:-1,1]+.29*(depths[:-2,0]+depths[2:,0])
        avg[1:-1,-1]=.42*depths[1:-1,-2]+.29*(depths[:-2,-1]+depths[2:,-1])
        depths=np.maximum(fixed,avg-.00004)
    a[:,:,1]=-depths
    for i in range(1,len(a)-1):
        z=a[i,16,2];weight=math.exp(-((z-1.452)/.052)**4)
        for j in range(23,33):
            u=(j-23)/9.;reference=a[i,23,1]+.032*u
            a[i,j,1]=min(a[i,j,1],reference*weight+a[i,j,1]*(1-weight))
    return a

def restyle_garment(body,mat):
    bvh=BVHTree.FromPolygons([v.co for v in body.data.vertices],[p.vertices[:] for p in body.data.polygons])
    def front(x,z):
        h,_,_,_=bvh.ray_cast(Vector((x,-2,z)),Vector((0,1,0)),4);return h.y if h else None
    def rear(x,z):
        h,_,_,_=bvh.ray_cast(Vector((x,2,z)),Vector((0,-1,0)),4);return h.y if h else None
    prefixes=('Fine folded selvedge','Rolled cloth hem','Shaped lower hem','Neck selvedge','Continuous neck fabric')
    for o in list(bpy.data.objects):
        if o.name.startswith(prefixes):bpy.data.objects.remove(o,do_unlink=True)
    for side in (-1.,1.):
        o=bpy.data.objects['Loose neck panel '+str(side)]
        a=np.array([v.co[:] for v in o.data.vertices]).reshape(115,33,3);a=front_envelope(a)
        for i in range(22):
            w=1-float(smooth(0,21,i))
            for j,u in enumerate(np.linspace(-1,1,33)):a[i,j,1]-=.0008*w*math.sin(3*math.pi*u)
        o.data.vertices.foreach_set('co',a.ravel());o.data.update()
        for j in (0,-1):tube('Drape boundary '+str(side),[p[j] for p in a],[.0006,.0006],mat['cloth'],n=115,sides=6)
        first=a[0].copy();center=first.mean(0)
        centers=catmull([center,(side*.061,-.069,1.660),(side*.073,-.029,1.671),(side*.075,.012,1.672),(side*.061,.056,1.652),(side*.035,.082,1.636),(0,.087,1.632)],64)
        grid=[]
        for i,c in enumerate(centers):
            tangent=centers[min(i+1,63)]-centers[max(i-1,0)];tangent/=max(np.linalg.norm(tangent),1e-8)
            normal=np.array([c[0],c[1]-.012,.022]);normal/=max(np.linalg.norm(normal),1e-8)
            lateral=np.cross(tangent,normal);lateral/=max(np.linalg.norm(lateral),1e-8)
            if lateral[0]*side<0:lateral=-lateral
            w=.014+.005*i/63;row=[]
            for j,u in enumerate(np.linspace(-1,1,33)):
                point=c+w*u*lateral
                if i<10:
                    blend=float(smooth(0,9,i));point=(first[j]+c-center)*(1-blend)+point*blend
                h,no,_,distance=bvh.find_nearest(Vector(point))
                if i>0 and h and distance<.035:point=np.array(h)+np.array(no)*.004
                point+=np.array([0,0,.0008*math.sin(u*3*math.pi+i*.04)]);row.append(point)
            grid.append(row)
        ribbon('Continuous soft neck wrap '+str(side),grid,mat['cloth'],.0013,1)
        for j in (0,-1):tube('Neck rolled edge',[r[j] for r in grid],[.0005,.0005],mat['cloth'],n=64,sides=6)
    for name in ('Front hanging cloth','Back hanging cloth'):
        old=bpy.data.objects.get(name)
        if old:bpy.data.objects.remove(old,do_unlink=True)
    for back in (False,True):
        grid=[]
        for t in np.linspace(0,1,95):
            row=[]
            for u in np.linspace(-1,1,41):
                width=.148*(1-.37*t**1.5)+.012*math.sin(math.pi*t);x=width*u+.006*math.sin(math.pi*t)*math.sin(1.5*t)
                z=1.197-.785*t-.055*t**6*(1-u*u)+.008*t**7*math.sin(5*u+1)
                if back:
                    support=rear(x,z);start=rear(.148*u,1.197);start=(start if start is not None else .07)+.008
                    free=.196+.012*math.sin(math.pi*t);y=start*(1-float(smooth(0,.24,t)))+free*float(smooth(0,.24,t))
                    if support is not None:y=max(y,support+.008)
                else:
                    support=front(x,z);y=-.174-.012*math.sin(math.pi*t)
                    if support is not None:y=min(y,support-.008)
                amp=.0018+.0065*math.sin(math.pi*min(1,t*1.25));y+=amp*(math.sin(3.5*math.pi*u+.65*t)+.23*math.sin(7.3*math.pi*u-.8*t))
                row.append((x,y,z))
            grid.append(row)
        a=np.array(grid)
        for _ in range(18):a[1:-1,:,1]=.21*a[:-2,:,1]+.58*a[1:-1,:,1]+.21*a[2:,:,1]
        o=ribbon('Back hanging cloth' if back else 'Front hanging cloth',a,mat['cloth'],.0013,1)
        for j in (0,-1):tube('Apron stitched edge',[r[j] for r in a],[.00065,.00065],mat['cloth'],n=95,sides=6)
        tube('Apron lower edge',a[-1],[.00065,.00065],mat['cloth'],n=50,sides=6)
        if back:
            import bmesh
            bm=bmesh.new();bm.from_mesh(o.data)
            remove=[f for f in bm.faces if ((f.calc_center_median().x-.031)/.036)**2+((f.calc_center_median().z-.994)/.042)**2<1]
            bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(o.data);bm.free();o.data.update()

def install():
    previous=finish_details.build
    def build(body,eyes,mat,bvh,front):
        previous(body,eyes,mat,bvh,front);restyle_garment(body,mat)
    finish_details.build=build
