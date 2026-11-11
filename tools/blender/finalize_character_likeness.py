"""Character01 final likeness integration.
Rebuilds from versioned art checkpoints; the original illustration remains authoritative.
This is an art pass, not certification of biological tissue mechanics or locomotion.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy, bmesh, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import detailed_character_likeness as d

f, b, a, r = d.f, d.b, d.a, d.r
BASE_BODY, BASE_FACE, BASE_HAIR = f.make_anatomy, f.make_face, f.make_hair
BASE_STAGE, BASE_BIND, BASE_RIG = f.make_stage, f.bind_all, a.create_rig
BODY_TREE = None
BODY_ONLY_TREE = None
SCULPT_REPORT = {}
OUT = None

def smooth(lo,hi,x):
    q=max(0.,min(1.,(x-lo)/(hi-lo)))
    return q*q*(3-2*q)

def curve(z, levels, values):
    k=max(0,min(len(levels)-2,int(np.searchsorted(levels,z)-1)))
    u=max(0.,min(1.,(z-levels[k])/(levels[k+1]-levels[k])))
    return r.cat(values[max(0,k-1)],values[k],values[k+1],values[min(len(values)-1,k+2)],u)

def remove(prefixes):
    for obj in list(f.PARTS):
        if obj.name.startswith(prefixes):
            f.PARTS.remove(obj)
            bpy.data.objects.remove(obj,do_unlink=True)

def normals(obj):
    bm=bmesh.new();bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
    bm.to_mesh(obj.data);bm.free();obj.data.update()
    for poly in obj.data.polygons: poly.use_smooth=True

def skin_warp(co):
    x,y,z=map(float,co)
    # Continuous hip-to-thigh silhouette, replacing the abrupt upper-hip step.
    if z<1.22 and abs(x)<.47:
        levels=[.48,.60,.70,.80,.90,1.,1.05,1.12,1.22]
        amounts=[1.,1.015,1.065,1.040,.985,.985,1.025,1.055,1.]
        factor=curve(z,levels,amounts)
        x*=factor
    # Defined cheeks, a pointed rather than square chin, and a smaller nose.
    if z>1.69 and y<-.055:
        jaw=smooth(1.78,1.715,z)*smooth(1.69,1.715,z)
        x*=1-.13*jaw
        chin=math.exp(-((x/.04)**4+((z-1.713)/.025)**4))
        z-=.0045*chin;y-=.003*chin
        nose=math.exp(-((z-1.795)/.028)**4)*smooth(-.155,-.198,y)
        if abs(x)<.045:
            x*=1-.20*nose
            tip=math.exp(-(x/.014)**2)*math.exp(-((z-1.789)/.016)**2)
            z-=.003*tip;y-=.003*tip
        # Lift the outer eyelid with a broad falloff so cheek/brow remain continuous.
        eye=math.exp(-((abs(x)-.0564)/.050)**4-((z-1.8434)/.034)**4)
        z+=.16*(abs(x)-.0564)*eye
        mouth=math.exp(-((z-1.750)/.013)**4)*math.exp(-(x/.050)**6)
        x*=1+.10*mouth
        z+=(.0033*(x/.04)**2+.0017*x/.04)*mouth
    return (x,y,z)

def anatomy(path):
    global BODY_TREE,BODY_ONLY_TREE
    obj,v,definition,weights=BASE_BODY(path)
    for p in obj.data.vertices:p.co=skin_warp(p.co)
    v=np.array([skin_warp(p) for p in v])
    # Smooth only the high-curvature hip transition, without erasing muscle detail.
    group=obj.vertex_groups.new(name='ArtHipRelax')
    for p in obj.data.vertices:
        x,y,z=p.co
        w=math.exp(-((z-.965)/.12)**4)*smooth(.16,.30,abs(x))
        if w>.001:group.add([p.index],.65*w,'REPLACE')
    mod=obj.modifiers.new('HipContourFinish','SMOOTH')
    mod.factor=.28;mod.iterations=7;mod.vertex_group=group.name
    f.apply(obj,mod);obj.vertex_groups.remove(obj.vertex_groups['ArtHipRelax'])
    obj.data.update()
    BODY_TREE=BVHTree.FromPolygons([p.co for p in obj.data.vertices],[tuple(p.vertices) for p in obj.data.polygons])
    f.TREE=BODY_TREE
    bad=('UpperArm','Forearm','Hand','Thumb','Index','Middle','Ring','Little','metacarpal')
    polys=[]
    for poly in obj.data.polygons:
        weight=sum(sum(g.weight for g in obj.data.vertices[i].groups if obj.vertex_groups[g.group].name.startswith(bad)) for i in poly.vertices)/len(poly.vertices)
        if weight<.20:polys.append(tuple(poly.vertices))
    BODY_ONLY_TREE=BVHTree.FromPolygons([p.co for p in obj.data.vertices],polys)
    SCULPT_REPORT['bodyVertices']=len(obj.data.vertices)
    SCULPT_REPORT['originalPaletteSRGB']=f.CFG['skin']
    return obj,v,definition,weights

def front(x,z,offset=.006):
    hit=BODY_ONLY_TREE.ray_cast(Vector((x,-2,z)),Vector((0,1,0)),4.)
    if hit[0] is not None:return hit[0].y-offset
    p,n,_,_=BODY_ONLY_TREE.find_nearest(Vector((x,-.14,z)))
    return p.y-offset

def face(v,definition):
    BASE_FACE(v,definition)
    # Existing lids are genuine facial geometry; these follow their new inclination.
    for obj in f.PARTS:
        if obj.name.startswith(('UpperEyeliner','LowerEyeliner','Lash.')):
            side=1 if '.L' in obj.name else -1
            for p in obj.data.vertices:
                eye=math.exp(-((abs(p.co.x)-.0564)/.050)**4-((p.co.z-1.8434)/.034)**4)
                p.co.z+=.16*(abs(p.co.x)-.0564)*eye
                p.co.y=f.front(p.co.x,p.co.z,.0014)
    remove(('Fang.','MouthCrease'))
    # An asymmetrical, narrow smirk. Small pointed canines, not white blocks.
    points=[(-.043,1.756),(-.028,1.753),(-.010,1.749),(0,1.7495),(.025,1.756),(.044,1.762)]
    f.face_line('MouthCrease',points,[.0001,.0007,.0007,.0008,.0009,.0001],'Ink',.0005)
    for sign in [-1,1]:
        x=sign*.0295;z=1.755+(sign>0)*.003
        y=f.front(x,z,.0017)
        obj=f.sweep('Fang.'+str(sign),[(x,y,z+.002),(x+sign*.0003,y-.0014,z-.0015),(x+sign*.001,y+.0002,z-.006)],
                    [.0026,.0018,.00008],[.0017,.0014,.00007],material='Fang',sides=16,steps=8)
        obj['bind_bone']='Jaw'
    # A subtle tear line and two catchlights preserve readability at game distance.
    for side,sign in [('L',1),('R',-1)]:
        center=Vector(v[definition['joints'][definition['bones']['eye.'+side]['head']]].mean(0))
        x,z=center.x,center.z
        f.face_line('Tearline.'+side,[(x+sign*dx,z+dz) for dx,dz in [(-.023,-.002),(-.009,-.005),(.010,-.002),(.025,.006)]],
                    [.00010,.00023,.00026,.00010],'Lip',.0004)
    # Add radial iris colour detail as vertex-coloured rings; portable in GLB.
    for side in ['L','R']:
        iris=bpy.data.objects.get('Iris.'+side)
        if iris is None:continue
        verts=np.array([p.co[:] for p in iris.data.vertices])
        center=verts.mean(0)
        material=b.MATS['Iris'].copy();material.name='IrisDetail.'+side
        col=iris.data.color_attributes.new(name='IrisPigment',type='FLOAT_COLOR',domain='POINT')
        light=np.array([.29,.32,.49]);dark=np.array([.085,.10,.17])
        for p in iris.data.vertices:
            x=(p.co.x-center[0])/.0114;z=(p.co.z-center[2])/.0122
            radius=min(1.,math.hypot(x,z));angle=math.atan2(z,x)
            spoke=.45+.15*math.sin(angle*37)+.13*math.sin(angle*71+radius*19)+.07*math.cos(angle*113-radius*8)
            blend=max(0,min(1,spoke))*(1-smooth(.73,1,radius))
            c=dark*(1-blend)+light*blend
            col.data[p.index].color=(*c,1)
        attr=material.node_tree.nodes.new('ShaderNodeVertexColor');attr.layer_name='IrisPigment'
        material.node_tree.links.new(attr.outputs['Color'],material.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
        iris.data.materials.clear();iris.data.materials.append(material)

def hair():
    BASE_HAIR()
    # Cap crown gaps and bury the parting roots in a continuous fitted scalp.
    cap=bpy.data.objects.get('HairScalp')
    if cap:
        for p in cap.data.vertices:
            t=smooth(1.87,1.99,p.co.z)
            p.co.z+=.012*t
            p.co.y+=.003*t
        normals(cap)
    for obj in f.PARTS:
        if obj.name.startswith('CrownWave'):
            for p in obj.data.vertices:
                hit,n,_,_=BODY_TREE.find_nearest(p.co)
                if hit is not None and p.co.z>1.96:
                    p.co.z-=.003
    # Preserve the approved face-framing locks, diversify long back waves.
    remove(('BackWave',))
    for layer,count in [(0,11),(1,9),(2,7)]:
        for j in range(count):
            u=2*j/(count-1)-1;sign=1 if u>=0 else -1
            phase=j*1.618+layer*.73
            rootz=1.975-layer*.064
            end=.94+.13*abs(u)+layer*.135+.035*math.sin(phase*1.3)
            swing=.017+.006*layer
            pts=[
                (u*.079,.045+.032*layer,rootz),
                (u*.133,.145+.025*layer,rootz-.16),
                (u*.205+swing*math.sin(phase),.203+.027*layer,rootz-.31),
                (u*.262-swing*math.sin(phase),.217+.033*layer,(rootz+end)/2),
                (u*.303+swing*math.sin(phase+.8),.213+.028*layer,end+.19),
                (u*.328+sign*.018,.184+.026*layer,end+.07),
                (u*.343+sign*.040,.163+.024*layer,end+.025),
                (u*.351+sign*.057,.151+.022*layer,end+.046)]
            width=.033+.004*layer+.003*math.sin(phase)
            widths=[.002,width*.82,width,width*1.12,width,width*.72,width*.37,.0001]
            depths=[.001,.019,.023,.026,.022,.015,.008,.0001]
            f.sweep(f'BackWave.{layer}.{j}',pts,widths,depths,material='Hair',sides=28,steps=12,grooves=.045)
    # Small independent curls break the identical comb-like silhouette.
    for sign in [-1,1]:
        for j in range(4):
            z=1.73-.19*j;x=sign*(.18+.040*j)
            pts=[(x,.15,z),(x+sign*.06,.12,z-.07),(x+sign*.10,.11,z-.11),(x+sign*.12,.09,z-.09)]
            f.sweep(f'SideCurl.{sign}.{j}',pts,[.001,.027,.020,.0001],[.001,.015,.011,.0001],sides=24,steps=14)

def make_clothes():
    # A single continuous mesh per halter panel runs from the front sash,
    # across the shoulder to the rear sash. No disconnected strap fragments.
    levels=[1.19,1.225,1.28,1.36,1.445,1.53,1.60,1.65]
    inners=[.047,.065,.107,.159,.183,.164,.126,.108]
    outers=[.148,.194,.304,.373,.382,.324,.227,.177]
    cross=42;long=100
    for sign in [-1,1]:
        rows=[];uvs=[]
        for i in range(long+1):
            t=i/long;z=1.19+(1.65-1.19)*t
            lo,hi=curve(z,levels,inners),curve(z,levels,outers)
            # Guard against silhouette exits at the outer breast edge.
            xs=np.linspace(0,.44,190)
            valid=[float(x) for x in xs if BODY_ONLY_TREE.ray_cast(Vector((x,-2,z)),Vector((0,1,0)),4.)[0] is not None]
            maxx=max(valid) if valid else hi
            hi=min(hi,maxx-.003)
            hi=max(hi,lo+.015)
            row=[]
            for j in range(cross+1):
                u=j/cross;x=lo+(hi-lo)*u
                y=front(x,z,.0075)
                fold=.0016*math.sin(5*math.pi*u+4*t)*math.sin(math.pi*t)**1.4
                fold+=.0030*math.sin(8*math.pi*u+t*3)*math.exp(-((t-.10)/.15)**2)
                row.append((sign*x,y-fold,z))
            rows.append(row)
        # Remove projection discontinuities while retaining clearance.
        grid=np.array(rows)
        for _ in range(10):
            new=grid.copy()
            new[1:-1,:,1]=.5*grid[1:-1,:,1]+.25*(grid[:-2,:,1]+grid[2:,:,1])
            grid=new
        for i in range(len(grid)):
            for j in range(cross+1):
                x,y,z=grid[i,j]
                hit=BODY_ONLY_TREE.ray_cast(Vector((abs(x),-2,z)),Vector((0,1,0)),4.)
                if hit[0] is not None:grid[i,j,1]=min(y,hit[0].y-.006)
        rows=grid.tolist()
        frontrow=grid[-1]
        # The shoulder bridge is fit with a downward ray, not a front ray that
        # can switch from collarbone to the far side of an armpit.
        rearrow=[]
        for j in range(cross+1):
            u=j/cross;x=sign*(.104+.064*u);y=.077
            hit=BODY_TREE.ray_cast(Vector((x,y,2.1)),Vector((0,0,-1)),.7)
            z=max(1.65,hit[0].z+.009 if hit[0] is not None else 1.66)
            rearrow.append((x,y,z))
        rearrow=np.array(rearrow)
        for i in range(1,29):
            t=i/28;row=[]
            for j in range(cross+1):
                point=frontrow[j]*(1-t)+rearrow[j]*t
                point[2]+=.020*math.sin(math.pi*t)
                hit=BODY_TREE.ray_cast(Vector((point[0],point[1],1.85)),Vector((0,0,-1)),.35)
                if hit[0] is not None:point[2]=max(point[2],hit[0].z+.009)
                row.append(tuple(point))
            rows.append(row)
        last=np.array(rows[-1])
        for i in range(1,86):
            t=i/85;row=[]
            for j in range(cross+1):
                u=j/cross;x=sign*((.104+.064*u)*(1-t)+(.073+.078*u)*t)
                z=last[j,2]*(1-t)+1.205*t
                hit=BODY_ONLY_TREE.ray_cast(Vector((x,2,z)),Vector((0,-1,0)),4.)
                y=(hit[0].y+.009) if hit[0] is not None else .08
                y+=.0015*math.cos(5*math.pi*u+2*t)*math.sin(math.pi*t)
                row.append((x,y,z))
            rows.append(row)
        vertices=[q for row in rows for q in row]
        faces=[]
        for i in range(len(rows)-1):
            for j in range(cross):
                k=i*(cross+1)+j
                faces.append((k,k+1,k+cross+2,k+cross+1))
        uv=[(j/cross,i/(len(rows)-1)) for i in range(len(rows)) for j in range(cross+1)]
        obj=f.mesh('ChestDrape.'+('L' if sign>0 else 'R'),vertices,faces,'Cloth',uv)
        normals(obj)
        thick=obj.modifiers.new('ContinuousHemThickness','SOLIDIFY')
        thick.thickness=.0022;thick.offset=0;f.apply(obj,thick)
        normals(obj)
    # Fabric below the sash: flowing diagonal swags, not a uniformly pleated apron.
    for back in [False,True]:
        nx,ny=56,106;verts=[];faces=[];uv=[]
        for i in range(ny+1):
            t=i/ny
            width=(.205-.030*t) if not back else (.135-.012*t)
            for j in range(nx+1):
                u=2*j/nx-1
                x=width*u+.018*t*(1 if not back else -.35)
                z=1.221-.86*t+(.060*abs(u)**1.8+.018*u)*smooth(.78,1,t)
                # Hip clearance blends naturally into the unsupported hem.
                y=-.174-.083*smooth(0,.20,t)+.022*t
                fold=0.
                for k,(offset,slope,amp) in enumerate([(.10,.12,.012),(.23,-.10,.016),(.39,.05,.009)]):
                    fold+=amp*math.exp(-((t-offset-slope*u)/(.040+.012*k))**2)
                fold+=.007*math.cos(3.2*math.pi*u+t*2.2)*smooth(.15,.55,t)
                fold+=.0022*math.sin(7.2*math.pi*u-t)*smooth(.2,.8,t)
                y-=fold
                if back:
                    y=-y-.066;z+=.04*t
                verts.append((x,y,z));uv.append(((u+1)*.5,t))
        for i in range(ny):
            for j in range(nx):
                k=i*(nx+1)+j;faces.append((k,k+1,k+nx+2,k+nx+1))
        obj=f.mesh('RearDrape' if back else 'FrontDrape',verts,faces,'Cloth',uv)
        normals(obj);thick=obj.modifiers.new('TurnedHem','SOLIDIFY');thick.thickness=.002;thick.offset=0;f.apply(obj,thick);normals(obj)
    # Refit the sash to the altered waist and overlap the upper drape edge.
    n,m=160,12;verts=[];uv=[];faces=[]
    for j in range(m+1):
        h=j/m;z=1.181+.073*h
        for k in range(n):
            th=2*math.pi*k/n
            direction=Vector((math.cos(th),math.sin(th),0))
            origin=Vector((0,-.060,z))
            hit,nor,_,_=BODY_ONLY_TREE.ray_cast(origin,direction,.8)
            if hit is None:
                point=Vector((.215*math.cos(th),-.063+.115*math.sin(th),z))
            else:
                point=hit+direction*(.011+.0025*math.sin(h*math.pi*5+th*2))
            # Place the garment under a genuine wrapping band at the centre front.
            if point.y<-.11:point.y=min(point.y,-.184)
            point.z+=.004*math.sin(th+.3)*(2*h-1)
            verts.append(tuple(point));uv.append((k/n,h))
    for j in range(m):
        for k in range(n):
            p=j*n+k;q=j*n+(k+1)%n;faces.append((p,q,q+n,p+n))
    obj=f.mesh('WaistSash',verts,faces,'Sash',uv);normals(obj)
    th=obj.modifiers.new('WrappedBeltThickness','SOLIDIFY');th.thickness=.003;th.offset=0;f.apply(obj,th)
    knot=Vector((.103,-.199,1.214))
    f.sphere('SashKnot',knot,(.018,.013,.020),'Sash')
    for sign in [-1,1]:
        pts=[tuple(knot+Vector((0,-.008,0))),tuple(knot+Vector((sign*.033,-.014,.015))),
             tuple(knot+Vector((sign*.041,-.016,-.003))),tuple(knot+Vector((sign*.008,-.010,-.009)))]
        f.sweep('SashLoop.'+str(sign),pts,[.005,.0045,.0043,.005],[.003]*4,material='Sash',sides=14,steps=13)
    for j in range(2):
        pts=[(.10+j*.012,-.206,1.213),(.105+j*.015,-.226,1.16),(.091+j*.020,-.257,1.08),(.083+j*.024,-.268,1.047+j*.025)]
        f.sweep('SashTie.'+str(j),pts,[.0057,.0052,.0048,.002],[.0025]*4,material='Sash',sides=12,steps=14)
    # Fix circular-sweep seam UVs before exporting normal textures.
    for obj in f.PARTS:
        if not obj.data.uv_layers:continue
        layer=obj.data.uv_layers.active
        for face in obj.data.polygons:
            us=[layer.data[i].uv.x for i in face.loop_indices]
            if us and max(us)-min(us)>.8:
                for li in face.loop_indices:
                    if layer.data[li].uv.x<.2:layer.data[li].uv.x+=1

def bind(body):
    BASE_BIND(body)
    for obj in f.PARTS:
        if obj.name.startswith('Tearline'):
            obj.vertex_groups.clear();g=obj.vertex_groups.new(name='Head');g.add(list(range(len(obj.data.vertices))),1.,'REPLACE')
        if obj.name.startswith('SideCurl'):
            side='L' if sum(p.co.x for p in obj.data.vertices)>0 else 'R'
            obj.vertex_groups.clear();g=obj.vertex_groups.new(name='Hair1.'+side);g.add(list(range(len(obj.data.vertices))),1.,'REPLACE')

def rig(v,definition,tail):
    result=BASE_RIG(v,definition,tail)
    # The earlier anatomical helper edit shared breast/spine landmark indices.
    # Restore a centred chest chain before inverse bind matrices are exported.
    bpy.context.view_layer.objects.active=result
    bpy.ops.object.mode_set(mode='EDIT')
    chest=result.data.edit_bones.get('Chest');upper=result.data.edit_bones.get('UpperChest')
    if chest and upper:
        midpoint=Vector((0,-.008,1.50));chest.tail=midpoint;upper.head=midpoint
    bpy.ops.object.mode_set(mode='OBJECT')
    return result

def fit_regions(out):
    doc=a.export_tissue_original(out) if hasattr(a,'export_tissue_original') else None
    if doc is None: raise RuntimeError('Missing original cage factory')
    verts=np.array([p.co[:] for p in f.BODY.data.vertices])
    for reg in doc['regions']:
        sign=1 if reg['name'].endswith('.L') else -1
        breast=reg['name'].startswith('breast')
        if breast:
            center=np.array([sign*.185,1.444,.164])
            radius=np.array([.238,.244,.284])
        else:
            center=np.array([sign*.175,.946,-.043])
            radius=np.array([.260,.252,.153])
        oldc=np.array(reg['center']);oldr=np.array(reg['radii'])
        q=(np.array(reg['nodes'])-oldc)/oldr
        reg['nodes']=(center+q*radius).tolist();reg['center']=center.tolist();reg['radii']=radius.tolist()
        reg['bone']='UpperChest' if breast else 'Pelvis'
        reg['fitVersion']='Character01-likeness-003'
        reg['youngModulus']=45000 if breast else 70000
        reg['poissonRatio']=.4999;reg['solverSubsteps']=16;reg['solverIterations']=16;reg['velocityDrag']=4.
    doc['limitations']=[
        'Fitted integration cages, not anatomical layers or measured biological materials.',
        'Single skeletal support per region with graded compliance; body/cloth self-contact remains separate work.'
    ]
    doc['authoring']={'reference':'original illustration controls proportions and palette',
                      'bodyVertices':len(verts),'version':'likeness-003',
                      'bodyRestSha256':hashlib.sha256(verts.astype('<f4').tobytes()).hexdigest()}
    (out/'tissue-regions.json').write_text(json.dumps(doc,separators=(',',':')))
    return doc

def stage():
    camera=BASE_STAGE()
    scene=bpy.context.scene
    scene.cycles.samples=f.CFG.get('render_samples',48)
    scene.view_settings.look='AgX - Medium High Contrast'
    scene.view_settings.exposure=-.22
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.075,.080,.10,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
    floor=bpy.data.objects.get('StudioFloor')
    if floor:floor.hide_render=True
    scene.render.film_transparent=False
    # Low-contrast studio background; the hair stays readable without a black void.
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.13,.16,1)
    for name in ['Skin','PlainSkin']:
        shader=b.MATS[name].node_tree.nodes.get('Principled BSDF')
        shader.inputs['Roughness'].default_value=.47
        shader.inputs['Specular IOR Level'].default_value=.24
        shader.inputs['Subsurface Weight'].default_value=.065
    for name in ['Hair','BrowHair']:
        if name in b.MATS:
            shader=b.MATS[name].node_tree.nodes.get('Principled BSDF')
            shader.inputs['Roughness'].default_value=.52
            shader.inputs['Specular IOR Level'].default_value=.23
    return camera

f.make_anatomy=anatomy
f.make_face=face
f.make_hair=hair
f.make_clothes=make_clothes
f.bind_all=bind
a.create_rig=rig
a.export_tissue_original=a.export_tissue
a.export_tissue=fit_regions
f.make_stage=stage

if __name__=='__main__':f.main()
