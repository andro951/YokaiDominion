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
    if z<1.22 and abs(x)<.47:
        levels=[.48,.60,.70,.80,.90,1.,1.05,1.12,1.22]
        amounts=[1.,1.015,1.065,1.040,.985,.985,1.025,1.055,1.]
        factor=curve(z,levels,amounts)
        x*=factor
        rear=math.exp(-((z-.885)/.105)**2)*smooth(-.015,.065,y)*smooth(.04,.15,abs(x))
        y+=.045*rear
        front_leg=smooth(-.045,-.15,y)*math.exp(-((z-.755)/.17)**4)
        thigh=math.exp(-((abs(x)-.255)/.11)**4)
        y-=.011*front_leg*thigh
    if z>1.69 and y<-.055:
        jaw=smooth(1.78,1.715,z)*smooth(1.69,1.715,z)
        x*=1-.13*jaw
        chin=math.exp(-((x/.04)**4+((z-1.713)/.025)**4))
        z-=.0045*chin;y-=.003*chin
        nose=math.exp(-((z-1.795)/.028)**4)*smooth(-.155,-.198,y)
        if abs(x)<.045:
            x*=1-.20*nose
            tip=math.exp(-(x/.014)**2)*math.exp(-((z-1.789)/.016)**2)
            z-=.0065*tip;y-=.006*tip
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
    for obj in f.PARTS:
        if obj.name.startswith(('UpperEyeliner','LowerEyeliner','Lash.')):
            for p in obj.data.vertices:
                eye=math.exp(-((abs(p.co.x)-.0564)/.050)**4-((p.co.z-1.8434)/.034)**4)
                p.co.z+=.16*(abs(p.co.x)-.0564)*eye
                p.co.y=f.front(p.co.x,p.co.z,.0014)
    remove(('Fang.','MouthCrease'))
    points=[(-.043,1.756),(-.028,1.753),(-.010,1.749),(0,1.7495),(.025,1.756),(.044,1.762)]
    f.face_line('MouthCrease',points,[.0001,.0007,.0007,.0008,.0009,.0001],'Ink',.0005)
    for sign in [-1,1]:
        x=sign*.0295;z=1.755+(sign>0)*.003
        y=f.front(x,z,.0017)
        obj=f.sweep('Fang.'+str(sign),[(x,y,z+.002),(x+sign*.0003,y-.0014,z-.0015),(x+sign*.001,y+.0002,z-.006)],
                    [.0026,.0018,.00008],[.0017,.0014,.00007],material='Fang',sides=16,steps=8)
        obj['bind_bone']='Jaw'
    for side,sign in [('L',1),('R',-1)]:
        center=Vector(v[definition['joints'][definition['bones']['eye.'+side]['head']]].mean(0))
        x,z=center.x,center.z
        f.face_line('Tearline.'+side,[(x+sign*dx,z+dz) for dx,dz in [(-.023,-.002),(-.009,-.005),(.010,-.002),(.025,.006)]],
                    [.00010,.00023,.00026,.00010],'Lip',.0004)
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
    add_ears()

def hair():
    BASE_HAIR()
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
                if hit is not None and p.co.z>1.96:p.co.z-=.003
            for p in obj.data.vertices:
                hit,n,_,_=BODY_TREE.find_nearest(p.co)
                if hit is not None:
                    distance=(p.co-hit).dot(n)
                    if distance>.005:p.co-=n*(distance-.005)*.28
    # Broad overlapping S-curves: long continuous locks instead of rows of feathers.
    remove(('BackWave','SideCurl'))
    paths = [
        [(-.016,.005,1.997),(-.055,.102,1.87),(-.098,.165,1.66),(-.062,.189,1.46),(-.145,.184,1.28),(-.104,.164,1.08),(-.181,.125,.956),(-.203,.107,.951)],
        [(.018,.018,1.995),(.060,.112,1.85),(.104,.180,1.67),(.058,.211,1.48),(.142,.202,1.28),(.112,.177,1.06),(.191,.126,.936),(.204,.098,.956)],
        [(-.047,.028,1.978),(-.107,.105,1.83),(-.171,.182,1.65),(-.151,.213,1.47),(-.230,.202,1.30),(-.200,.171,1.13),(-.274,.115,1.026),(-.294,.084,1.049)],
        [(.057,.033,1.978),(.112,.119,1.82),(.180,.190,1.63),(.145,.216,1.43),(.231,.208,1.26),(.206,.164,1.08),(.284,.103,.995),(.307,.078,1.024)],
        [(-.086,.024,1.956),(-.146,.091,1.82),(-.231,.145,1.63),(-.213,.178,1.44),(-.296,.171,1.28),(-.265,.132,1.11),(-.337,.066,1.075),(-.355,.048,1.103)],
        [(.089,.035,1.952),(.157,.107,1.80),(.233,.156,1.61),(.217,.186,1.44),(.298,.164,1.27),(.270,.120,1.13),(.350,.063,1.092),(.366,.051,1.123)],
        [(-.109,.037,1.916),(-.193,.105,1.73),(-.278,.149,1.55),(-.251,.150,1.40),(-.337,.109,1.25),(-.331,.047,1.15),(-.383,.024,1.135),(-.399,.017,1.166)],
        [(.112,.045,1.925),(.198,.114,1.72),(.277,.151,1.54),(.252,.159,1.37),(.339,.112,1.23),(.324,.058,1.12),(.380,.019,1.085),(.398,.009,1.125)],
        [(-.082,.080,1.901),(-.147,.202,1.72),(-.193,.249,1.55),(-.144,.264,1.37),(-.183,.224,1.23),(-.167,.180,1.11),(-.225,.134,1.070),(-.245,.118,1.095)],
        [(.093,.082,1.905),(.159,.214,1.72),(.204,.257,1.53),(.154,.267,1.35),(.195,.230,1.20),(.170,.190,1.04),(.232,.145,.991),(.251,.123,1.017)],
    ]
    for j,pts in enumerate(paths):
        width=.037+(j%3)*.004
        f.sweep(f'BackWave.Finished.{j}',pts,[.004,width*.66,width,width*1.18,width*1.06,width*.90,width*.45,.00008],
                [.003,.022,.031,.036,.033,.025,.014,.00006],material='Hair',sides=26,steps=15,grooves=.032)
    fill_hair_volume()

def make_clothes():
    # One continuous front-to-back panel per side, with shoulder bridge and hem thickness.
    levels=[1.145,1.19,1.25,1.34,1.435,1.53,1.60,1.65]
    inners=[.054,.070,.107,.164,.186,.164,.126,.108]
    outers=[.166,.197,.293,.369,.383,.324,.227,.177]
    cross=42;long=100
    for sign in [-1,1]:
        rows=[]
        for i in range(long+1):
            t=i/long;z=1.145+(1.65-1.145)*t
            lo,hi=curve(z,levels,inners),curve(z,levels,outers)
            xs=np.linspace(0,.44,190)
            valid=[float(x) for x in xs if BODY_ONLY_TREE.ray_cast(Vector((x,-2,z)),Vector((0,1,0)),4.)[0] is not None]
            maxx=max(valid) if valid else hi
            hi=max(lo+.015,min(hi,maxx-.003))
            row=[]
            for j in range(cross+1):
                u=j/cross;x=lo+(hi-lo)*u;y=front(x,z,.0075)
                fold=.0016*math.sin(5*math.pi*u+4*t)*math.sin(math.pi*t)**1.4
                fold+=.0030*math.sin(8*math.pi*u+t*3)*math.exp(-((t-.10)/.15)**2)
                row.append((sign*x,y-fold,z))
            rows.append(row)
        grid=np.array(rows)
        for _ in range(10):
            new=grid.copy();new[1:-1,:,1]=.5*grid[1:-1,:,1]+.25*(grid[:-2,:,1]+grid[2:,:,1]);grid=new
        for _ in range(8):
            new=grid.copy()
            new[1:-1,1:-1,1]=.6*grid[1:-1,1:-1,1]+.1*(grid[:-2,1:-1,1]+grid[2:,1:-1,1]+grid[1:-1,:-2,1]+grid[1:-1,2:,1])
            grid=new
        for i in range(len(grid)):
            for j in range(cross+1):
                x,y,z=grid[i,j]
                hit=BODY_ONLY_TREE.ray_cast(Vector((abs(x),-2,z)),Vector((0,1,0)),4.)
                if hit[0] is not None:grid[i,j,1]=min(y,hit[0].y-.006)
        rows=grid.tolist();frontrow=grid[-1];rearrow=[]
        for j in range(cross+1):
            u=j/cross;x=sign*(.104+.064*u);y=.077
            hit=BODY_TREE.ray_cast(Vector((x,y,1.72)),Vector((0,0,-1)),.18)
            z=max(1.65,hit[0].z+.009 if hit[0] is not None else 1.66)
            rearrow.append((x,y,z))
        rearrow=np.array(rearrow)
        for i in range(1,29):
            t=i/28;row=[]
            for j in range(cross+1):
                point=frontrow[j]*(1-t)+rearrow[j]*t
                point[2]+=.020*math.sin(math.pi*t)
                hit=BODY_TREE.ray_cast(Vector((point[0],point[1],1.72)),Vector((0,0,-1)),.19)
                if hit[0] is not None:point[2]=max(point[2],hit[0].z+.009)
                row.append(tuple(point))
            rows.append(row)
        last=np.array(rows[-1])
        for i in range(1,86):
            t=i/85;row=[]
            for j in range(cross+1):
                u=j/cross;x=sign*((.104+.064*u)*(1-t)+(.073+.078*u)*t)
                z=last[j,2]*(1-t)+1.145*t
                hit=BODY_ONLY_TREE.ray_cast(Vector((x,2,z)),Vector((0,-1,0)),4.)
                y=(hit[0].y+.009) if hit[0] is not None else .08
                y+=.0015*math.cos(5*math.pi*u+2*t)*math.sin(math.pi*t)
                row.append((x,y,z))
            rows.append(row)
        vertices=[q for row in rows for q in row];faces=[]
        for i in range(len(rows)-1):
            for j in range(cross):
                k=i*(cross+1)+j;faces.append((k,k+1,k+cross+2,k+cross+1))
        uv=[(j/cross,i/(len(rows)-1)) for i in range(len(rows)) for j in range(cross+1)]
        obj=f.mesh('ChestDrape.'+('L' if sign>0 else 'R'),vertices,faces,'Cloth',uv);normals(obj)
        thick=obj.modifiers.new('ContinuousHemThickness','SOLIDIFY');thick.thickness=.0022;thick.offset=0;f.apply(obj,thick);normals(obj)
    for back in [False,True]:
        nx,ny=56,106;verts=[];faces=[];uv=[]
        for i in range(ny+1):
            t=i/ny;width=(.205-.030*t) if not back else (.135-.012*t)
            for j in range(nx+1):
                u=2*j/nx-1;x=width*u+.018*t*(1 if not back else -.35)
                z=1.165-.834*t+(.060*abs(u)**1.8+.018*u)*smooth(.78,1,t)
                y=-.157-.100*smooth(.025,.20,t)+.022*t
                fold=0.
                for k,(offset,slope,amp) in enumerate([(.13,.18,.020),(.28,-.15,.023),(.47,.08,.014)]):
                    fold+=amp*math.exp(-((t-offset-slope*u)/(.040+.012*k))**2)
                fold+=.007*math.cos(3.2*math.pi*u+t*2.2)*smooth(.15,.55,t)
                fold+=.0022*math.sin(7.2*math.pi*u-t)*smooth(.2,.8,t)
                y-=fold
                if back:y=-y-.066;z+=.04*t
                if t<.10:
                    hit=BODY_ONLY_TREE.ray_cast(Vector((x,2 if back else -2,z)),Vector((0,-1 if back else 1,0)),4.)
                    if hit[0] is not None:
                        target=hit[0].y+(.005 if back else -.005);mix=1-smooth(.01,.10,t)
                        y=y*(1-mix)+target*mix
                verts.append((x,y,z));uv.append(((u+1)*.5,t))
        for i in range(ny):
            for j in range(nx):
                k=i*(nx+1)+j;faces.append((k,k+1,k+nx+2,k+nx+1))
        obj=f.mesh('RearDrape' if back else 'FrontDrape',verts,faces,'Cloth',uv)
        normals(obj);thick=obj.modifiers.new('TurnedHem','SOLIDIFY');thick.thickness=.002;thick.offset=0;f.apply(obj,thick);normals(obj)
    knot=Vector((.103,-.199,1.150))
    f.sphere('SashKnot',knot,(.018,.013,.020),'Sash')
    for sign in [-1,1]:
        pts=[tuple(knot+Vector((0,-.008,0))),tuple(knot+Vector((sign*.033,-.014,.015))),
             tuple(knot+Vector((sign*.041,-.016,-.003))),tuple(knot+Vector((sign*.008,-.010,-.009)))]
        f.sweep('SashLoop.'+str(sign),pts,[.005,.0045,.0043,.005],[.003]*4,material='Sash',sides=14,steps=13)
    for j in range(2):
        pts=[(.10+j*.012,-.206,1.149),(.105+j*.015,-.226,1.096),(.091+j*.020,-.257,1.016),(.083+j*.024,-.268,.983+j*.025)]
        f.sweep('SashTie.'+str(j),pts,[.0057,.0052,.0048,.002],[.0025]*4,material='Sash',sides=12,steps=14)
    for obj in f.PARTS:
        if not obj.data.uv_layers:continue
        layer=obj.data.uv_layers.active
        for face in obj.data.polygons:
            us=[layer.data[i].uv.x for i in face.loop_indices]
            if us and max(us)-min(us)>.8:
                for li in face.loop_indices:
                    if layer.data[li].uv.x<.2:layer.data[li].uv.x+=1
    replace_sash()

def bind(body):
    BASE_BIND(body)
    bind_hair_ears()
    for obj in f.PARTS:
        if obj.name.startswith('Tearline'):
            obj.vertex_groups.clear();g=obj.vertex_groups.new(name='Head');g.add(list(range(len(obj.data.vertices))),1.,'REPLACE')
        if obj.name.startswith('SideCurl'):
            side='L' if sum(p.co.x for p in obj.data.vertices)>0 else 'R'
            obj.vertex_groups.clear();g=obj.vertex_groups.new(name='Hair1.'+side);g.add(list(range(len(obj.data.vertices))),1.,'REPLACE')

def rig(v,definition,tail):
    result=BASE_RIG(v,definition,tail)
    bpy.context.view_layer.objects.active=result
    bpy.ops.object.mode_set(mode='EDIT')
    chest=result.data.edit_bones.get('Chest');upper=result.data.edit_bones.get('UpperChest')
    if chest and upper:
        midpoint=Vector((0,-.008,1.50));chest.tail=midpoint;upper.head=midpoint
    bpy.ops.object.mode_set(mode='OBJECT')
    return result

def fit_regions(out):
    doc=a.export_tissue_original(out) if hasattr(a,'export_tissue_original') else None
    if doc is None:raise RuntimeError('Missing original cage factory')
    verts=np.array([p.co[:] for p in f.BODY.data.vertices])
    for reg in doc['regions']:
        sign=1 if reg['name'].endswith('.L') else -1
        breast=reg['name'].startswith('breast')
        if breast:
            center=np.array([sign*.185,1.444,.164]);radius=np.array([.238,.244,.284])
        else:
            center=np.array([sign*.175,.946,-.043]);radius=np.array([.260,.252,.178])
        oldc=np.array(reg['center']);oldr=np.array(reg['radii']);q=(np.array(reg['nodes'])-oldc)/oldr
        reg['nodes']=(center+q*radius).tolist();reg['center']=center.tolist();reg['radii']=radius.tolist()
        reg['bone']='UpperChest' if breast else 'Pelvis';reg['fitVersion']='Character01-likeness-003'
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
    camera=BASE_STAGE();scene=bpy.context.scene
    scene.cycles.samples=f.CFG.get('render_samples',48)
    scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.38
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.13,.16,1)
    floor=bpy.data.objects.get('StudioFloor')
    if floor:floor.hide_render=True
    scene.render.film_transparent=False
    for name in ['Skin','PlainSkin']:
        shader=b.MATS[name].node_tree.nodes.get('Principled BSDF')
        shader.inputs['Roughness'].default_value=.57
        shader.inputs['Specular IOR Level'].default_value=.24
        shader.inputs['Subsurface Weight'].default_value=.065
    for name in ['Hair','BrowHair']:
        if name in b.MATS:
            shader=b.MATS[name].node_tree.nodes.get('Principled BSDF')
            shader.inputs['Roughness'].default_value=.52;shader.inputs['Specular IOR Level'].default_value=.23
    cloth=b.MATS['Cloth'];shader=cloth.node_tree.nodes.get('Principled BSDF')
    for link in list(shader.inputs['Normal'].links):cloth.node_tree.links.remove(link)
    shader.inputs['Roughness'].default_value=.84;shader.inputs['Sheen Weight'].default_value=.15
    return camera

def add_ears():
    for sign in [-1,1]:
        outline=[(sign*.105,-.048,1.842),(sign*.149,-.050,1.863),(sign*.207,-.068,1.933),
                 (sign*.174,-.073,1.924),(sign*.126,-.077,1.899),(sign*.102,-.065,1.888)]
        boundary=f.spline(outline+[outline[0]],12)[:-1];center=Vector((sign*.133,-.060,1.884))
        verts=[tuple(center+Vector((0,.004,0)))];uv=[(.5,.5)];rings=7;n=len(boundary)
        for k in range(1,rings+1):
            t=k/rings
            for j,p in enumerate(boundary):
                v=center.lerp(p,t);v.y-=.008*math.sin(math.pi*t)**.7
                verts.append(tuple(v));uv.append((.5+.48*t*math.cos(2*math.pi*j/n),.5+.48*t*math.sin(2*math.pi*j/n)))
        faces=[]
        for j in range(n):faces.append((0,1+j,1+(j+1)%n))
        for k in range(rings-1):
            for j in range(n):
                p=1+k*n+j;q=1+k*n+(j+1)%n;faces.append((p,q,q+n,p+n))
        obj=f.mesh('PointedEar.'+('L' if sign>0 else 'R'),verts,faces,'PlainSkin',uv)
        normals(obj);mod=obj.modifiers.new('EarThickness','SOLIDIFY');mod.thickness=.004;mod.offset=0;f.apply(obj,mod);normals(obj)
        verts=[];faces=[];uv=[];rings=6
        for k in range(rings+1):
            t=.12+.66*k/rings
            for j,p in enumerate(boundary):
                v=center.lerp(p,t);v.y-=.009*math.sin(math.pi*t)**.7+.001
                verts.append(tuple(v));uv.append((j/n,k/rings))
        for k in range(rings):
            for j in range(n):
                p=k*n+j;q=k*n+(j+1)%n;faces.append((p,q,q+n,p+n))
        obj=f.mesh('EarConcha.'+str(sign),verts,faces,'Markings',uv);normals(obj)

def fill_hair_volume():
    levels=[.99,1.07,1.20,1.40,1.60,1.78,1.92,1.99]
    widths=[.015,.16,.275,.260,.220,.145,.090,.001]
    centers=[.10,.105,.12,.13,.13,.090,.025,-.055]
    depths=[.001,.045,.055,.060,.055,.060,.060,.001]
    verts=[];faces=[];uv=[];nr=100;ns=72
    for i in range(nr+1):
        z=levels[0]+(levels[-1]-levels[0])*i/nr
        w=max(.0001,curve(z,levels,widths));cy=curve(z,levels,centers);dep=max(.0001,curve(z,levels,depths))
        for j in range(ns):
            th=2*math.pi*j/ns;x=w*math.cos(th);y=cy+dep*math.sin(th)
            hit=BODY_ONLY_TREE.ray_cast(Vector((x,2,z)),Vector((0,-1,0)),4.)
            if hit[0] is not None:y=max(y,hit[0].y+.009)
            y+=.0028*math.sin(th*12+(z-1)*9)*smooth(-.1,.5,math.sin(th))
            verts.append((x,y,z));uv.append((j/ns,i/nr))
    for i in range(nr):
        for j in range(ns):
            p=i*ns+j;q=i*ns+(j+1)%ns;faces.append((p,q,q+ns,p+ns))
    for start,reverse in [(0,True),(nr*ns,False)]:
        for j in range(1,ns-1):
            face=(start,start+j,start+j+1);faces.append(tuple(reversed(face)) if reverse else face)
    obj=f.mesh('HairUnderflow',verts,faces,'HairShadow',uv);normals(obj)

def replace_sash():
    remove(('WaistSash',));n,m=160,14;verts=[];faces=[];uv=[]
    for j in range(m+1):
        h=j/m;z=1.116+.070*h
        for k in range(n):
            th=2*math.pi*k/n;direction=Vector((math.cos(th),math.sin(th),0));origin=Vector((0,-.050,z))
            hit,normal,_,_=BODY_ONLY_TREE.ray_cast(origin+direction,-direction,2.)
            radius=(hit-origin).dot(direction) if hit is not None else .22
            radius=max(.065,radius)+.014+.0015*math.sin(5*math.pi*h+1.8*math.sin(th))
            point=origin+direction*radius;point.z+=.003*math.sin(th+.5)
            verts.append(tuple(point));uv.append((k/n,h))
    for j in range(m):
        for k in range(n):
            p=j*n+k;q=j*n+(k+1)%n;faces.append((p,q,q+n,p+n))
    obj=f.mesh('WaistSash',verts,faces,'Sash',uv);normals(obj)
    mod=obj.modifiers.new('FabricBandThickness','SOLIDIFY');mod.thickness=.003;mod.offset=0;f.apply(obj,mod)
    # Move paired shell vertices together so contact correction retains thickness.
    for obj in f.PARTS:
        if not obj.name.startswith('ChestDrape'):continue
        count=len(obj.data.vertices)//2
        for k in range(count):
            pair=[obj.data.vertices[k],obj.data.vertices[k+count]];closest=[]
            for p in pair:
                hit,normal,_,distance=BODY_TREE.find_nearest(p.co)
                closest.append(((p.co-hit).dot(normal),normal,distance))
            sd,normal,distance=min(closest,key=lambda q:q[0])
            if distance<.04 and sd<.005:
                for p in pair:p.co+=normal*(.005-sd)
        normals(obj)

def bind_hair_ears():
    for obj in f.PARTS:
        if obj.name.startswith(('PointedEar','EarConcha')):
            obj.vertex_groups.clear();vg=obj.vertex_groups.new(name='Head');vg.add(list(range(len(obj.data.vertices))),1.,'REPLACE')
        if obj.name=='HairUnderflow':
            obj.vertex_groups.clear()
            groups={name:obj.vertex_groups.new(name=name) for name in ['Head','Hair0.L','Hair1.L','Hair2.L','Hair0.R','Hair1.R','Hair2.R']}
            for p in obj.data.vertices:
                sign='L' if p.co.x>=0 else 'R';names=['Head','Hair0.'+sign,'Hair1.'+sign,'Hair2.'+sign];heights=[1.89,1.71,1.46,1.18]
                values=[math.exp(-((p.co.z-h)/.19)**2) for h in heights];den=sum(values)
                for name,w in zip(names,values):
                    if w/den>.001:groups[name].add([p.index],w/den,'REPLACE')
                items=list(p.groups);total=sum(g.weight for g in items)
                for g in items:obj.vertex_groups[g.group].add([p.index],g.weight/total,'REPLACE')

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
