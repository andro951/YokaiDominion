"""Character details fitted to the current anatomical surface, never vice versa."""
import bpy, math, random
import numpy as np
from mathutils import Vector
from geometry import mesh,tube,ribbon,strand,catmull
from materials import base,linear


def coords(o):
    a=np.empty(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',a);return a.reshape(-1,3)


def colour_mesh(o, colors, name='DetailColour', rough=.3):
    m,bs=base(name,(1,1,1),rough)
    a=o.data.color_attributes.new(name='Colour',type='FLOAT_COLOR',domain='POINT')
    a.data.foreach_set('color',np.c_[np.array(colors),np.ones(len(colors))].ravel())
    node=m.node_tree.nodes.new('ShaderNodeVertexColor');node.layer_name='Colour'
    m.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color'])
    o.data.materials.clear();o.data.materials.append(m)
    return m


def eyes_and_face(body,eyes,mat,bvh,front):
    for eye in eyes:
        co=coords(eye);center=(co.min(0)+co.max(0))*.5
        radius=float(np.median((co.max(0)-co.min(0))*.5))
        # Coloured iris lies on a spherical cap, not a flat disk over the eyelids.
        riris=.0070;rpupil=.00265
        gaze=np.array((-.015 if center[0]>0 else .015,-1.,.18));gaze/=np.linalg.norm(gaze)
        right=np.cross(gaze,[0.,0.,1.]);right/=np.linalg.norm(right);up=np.cross(right,gaze)
        vv=[];ff=[];cols=[]
        rings=24;segs=96
        for j in range(rings):
            r=.00002+(riris-.00002)*j/(rings-1)
            h=math.sqrt(max(1e-9,radius**2-r*r))+.00012
            for k in range(segs):
                a=2*math.pi*k/segs
                vv.append(center+gaze*h+r*(math.cos(a)*right+math.sin(a)*up))
                fiber=(math.sin(a*43+r*1400)+.45*math.sin(a*79-r*4500)+.3*math.sin(a*121+r*750))/1.75
                t=r/riris
                c=np.array((.48,.43,.71))*(.75+.22*fiber)
                if r<rpupil:c=np.array((.023,.018,.040))
                elif r<rpupil+.00035:c=np.array((.30,.235,.45))*(1+.2*fiber)
                if t>.87:c*=max(.14,(1-t)/.13)
                cols.append(linear(c))
                if j:
                    p=(j-1)*segs+k;q=(j-1)*segs+(k+1)%segs;ff.append((p,q,q+segs,p+segs))
        o=mesh('Iris.'+eye.name,vv,ff);colour_mesh(o,cols,'Iris | amethyst fibres '+eye.name,.20)
        eye.data.materials.clear();eye.data.materials.append(mat['sclera'])
    # Brows and lid lines are projected onto the real facial surface.
    def project(pts,pad=.0006):
        result=[]
        for x,z in pts:
            y=front(x,z,pad)
            result.append((x,y if y is not None else -.16,z))
        return result
    for s in (-1,1):
        xs=np.array([.017,.025,.038,.051,.063])
        zs=np.array([1.847,1.850,1.853,1.857,1.856])
        ctr=project([(s*x,z) for x,z in zip(xs,zs)],.0010)
        tube('Brow.'+str(s),ctr,[.0012,.0032,.0030,.0021,.0002],mat['brow'],n=48,sides=10,flatten=.4)
        for j in range(22):
            t=j/21
            x=s*(.020+.040*t);z=np.interp(t,[0,.25,.55,.8,1],zs)
            points=project([(x-.0009*s,z-.001),(x+.0005*s,z+.0018)],.0017)
            tube('Brow hair',points,[.00016,.00004],mat['brow'],n=4,sides=4)
        pts=[(s*.015,1.824),(s*.022,1.829),(s*.033,1.832),(s*.045,1.8325),(s*.056,1.828),(s*.063,1.8305)]
        tube('Upper liner.'+str(s),project(pts,.0010),[.0003,.0006,.0010,.0012,.0011,.00007],mat['lash'],n=64,sides=8,flatten=.45)
        for j in range(5):
            x=.044+j*.003;z=1.831-.4*(x-.044)
            pts=project([(s*x,z),(s*(x+.003),z+.0025),(s*(x+.006),z+.0037)],.0012)
            tube('Outer eyelash',pts,[.00036,.0002,.000025],mat['lash'],n=12,sides=5)
    for s in (-1,1):
        x=s*.0250;z=1.742;y=front(x,z,.0014)
        if y is None:continue
        tube('Canine.'+str(s),[(x,y,z+.003),(x+s*.0005,y-.0015,z-.0008),(x+s*.0007,y-.001,z-.0055)],[.0018,.0015,.00005],mat['teeth'],n=12,sides=12)


def horns_tail(mat):
    for s in (-1,1):
        points=[(s*.071,-.023,1.913),(s*.099,-.029,1.953),(s*.126,-.022,2.007),(s*.137,-.003,2.063),(s*.128,.012,2.112),(s*.104,.017,2.147)]
        tube('Horn.'+str(s),points,[.038,.035,.027,.020,.011,.0002],mat['horn'],n=84,sides=28,flatten=.79,ripple=.008)
    tailpts=[(0,.14,1.03),(.035,.22,.96),(.13,.28,.87),(.25,.29,.83),(.37,.26,.89),(.43,.19,1.06),(.448,.10,1.25),(.455,.063,1.35)]
    tube('Tail',tailpts,[.024,.021,.019,.016,.014,.011,.008,.005],mat['horn'],n=150,sides=20)
    grid=[]
    for j,t in enumerate(np.linspace(0,1,30)):
        width=.050*math.sin(math.pi*t)**.8
        row=[]
        for k,a in enumerate(np.linspace(0,2*math.pi,24,endpoint=False)):
            row.append((.455+width*math.cos(a),.063+.011*math.sin(a)*math.sin(math.pi*t),1.33+.18*t))
        grid.append(row)
    vv=np.array(grid).reshape(-1,3);faces=[]
    for j in range(29):
        for k in range(24):
            a=j*24+k;b=j*24+(k+1)%24;faces.append((a,b,b+24,a+24))
    mesh('Tail spade',vv,faces,mat['horn'])


def garment(body,mat,bvh,front):
    outputs=[]
    knots=np.array([0,.12,.25,.39,.51,.62,.76,1.])
    zz=np.array([1.669,1.610,1.535,1.46,1.39,1.32,1.245,1.155])
    xx=np.array([.048,.068,.104,.145,.162,.148,.113,.076])
    ww=np.array([.014,.022,.040,.069,.081,.070,.049,.063])
    for s in (-1,1):
        grid=[]
        for i,t in enumerate(np.linspace(0,1,105)):
            center=np.interp(t,knots,xx);half=np.interp(t,knots,ww);z0=np.interp(t,knots,zz)
            row=[]
            for j,u in enumerate(np.linspace(-1,1,35)):
                x=s*(center+half*u)
                z=z0+.006*math.sin(math.pi*t)*u+.004*math.sin(2*math.pi*t)*u*u
                y=front(x,z,.010)
                if y is None:
                    for offset in np.linspace(.002,.06,24):
                        y=front(x-s*offset,z,.010)
                        if y is not None:break
                if y is None:y=-.035 if t<.2 else -.13
                if t>.54:
                    bridge=np.interp(t,[.54,.70,.88,1],[-.238,-.214,-.168,-.142])
                    y=min(y,bridge)
                y-=.0014*math.sin(3.5*math.pi*u+.9*t)+.0006*math.sin(6.7*math.pi*u-2*t)
                gathers=(math.exp(-t*7)+math.exp(-(1-t)*7))
                y-=.0022*gathers*math.sin(5*math.pi*u+.5*t)
                row.append((x,y,z))
            grid.append(row)
        o=ribbon('Neck-draped panel.'+str(s),grid,mat['cloth'],thickness=.0013,subdiv=1);outputs.append(o)
        for index in (0,-1):
            edge=[tuple(np.array(row[index])+np.array([0,-.00045,0])) for row in grid]
            tube('Folded panel edge',edge,[.0007]*2,mat['cloth'],n=100,sides=6)
    # Continuous neck-to-nape bridges remove the cut-off floating strap ends.
    for s in (-1,1):
        path=[(s*.048,-.065,1.667),(s*.061,-.045,1.683),(s*.070,-.006,1.693),(s*.064,.037,1.680),(s*.043,.072,1.663),(0,.084,1.65)]
        o=strand('Neck fabric bridge.'+str(s),path,[.014,.015,.016,.018,.023,.026],mat['cloth'],n=66,sides=14,depth=.10)
        outputs.append(o)
    grid=[]
    for t in np.linspace(0,1,45):
        a=-math.pi/2+math.pi*t
        row=[]
        for u in np.linspace(-1,1,7):
            x=(.060+.016*u)*math.sin(a);y=.025+(.062+.016*u)*math.cos(a);z=1.666-.016*math.cos(a)+.004*u
            row.append((x,y,z))
        grid.append(row)
    outputs.append(ribbon('Nape drape',grid,mat['cloth'],.0013,1))
    for back in (False,True):
        grid=[]
        for t in np.linspace(0,1,110):
            row=[]
            for u in np.linspace(-1,1,55):
                half=.155*(1-.11*t)+.008*math.sin(t*math.pi)
                x=u*half+.009*math.sin(math.pi*t)*t
                z=1.154-.77*t-.025*t**8*(1-u*u)+.009*math.sin(u*4+1)*t**9
                y0=(-.151 if not back else .16)+(-.035 if not back else .04)*math.sin(math.pi*min(1,t*1.5))
                wave=(.004+.010*t)*(math.sin(3.2*math.pi*u+.5*t)+.32*math.sin(6.8*math.pi*u-1.7*t))
                y=y0+wave
                if not back:
                    skin=front(x,z,.009)
                    if skin is not None:y=min(y,skin)
                else:
                    hit,_,_,_=bvh.ray_cast(Vector((x,2,z)),Vector((0,-1,0)),4)
                    if hit:y=max(y,hit.y+.009)
                row.append((x,y,z))
            grid.append(row)
        o=ribbon('Rear hanging panel' if back else 'Front hanging panel',grid,mat['cloth'],.0014,1);outputs.append(o)
        for side in (0,-1):
            tube('Apron rolled hem',[row[side] for row in grid],[.0008,.0008],mat['cloth'],n=100,sides=6)
        tube('Apron bottom hem',grid[-1],[.001,.001],mat['cloth'],n=60,sides=6)
    pts=[];n=180
    for a in np.linspace(0,2*math.pi,n):
        d=Vector((math.cos(a),math.sin(a),0));start=d*1.0;start.z=1.158
        hit,normal,_,_=bvh.ray_cast(start,-d,2.)
        if hit:p=hit+normal*.0065
        else:p=Vector((.15*math.cos(a),.13*math.sin(a),1.158))
        p.z=1.158+.0015*math.sin(2*a);pts.append(tuple(p))
    tube('Waist cord',pts,[.0052,.0052],mat['cord'],n=180,sides=12)
    arr=np.array(pts)
    for phase in (0,math.pi):
        q=[]
        for i,p in enumerate(arr):
            a=2*math.pi*i/(n-1);radial=np.array((math.cos(a),math.sin(a),0));b=phase+a*45
            q.append(p+.0050*(math.cos(b)*radial+math.sin(b)*np.array((0,0,1))))
        tube('Cord twisted fibre',q,[.0011,.0011],mat['cord'],n=500,sides=5)
    y=-.161;cx=.065;cz=1.158
    knot=[(cx-.014,y,cz),(cx+.012,y-.006,cz+.009),(cx+.017,y-.007,cz-.007),(cx-.008,y-.005,cz-.012),(cx-.014,y,cz)]
    tube('Waist knot',knot,[.005,.005],mat['cord'],n=65,sides=12)
    tube('Cord end long',[(cx+.004,y-.005,cz),(cx+.016,y-.015,cz-.07),(cx+.005,y-.019,cz-.155),(cx+.01,y-.014,cz-.20)],[.004,.0035,.0032,.002],mat['cord'],n=60,sides=10)
    tube('Cord end short',[(cx+.011,y-.005,cz),(cx+.037,y-.017,cz-.055),(cx+.04,y-.012,cz-.115)],[.004,.0035,.002],mat['cord'],n=45,sides=10)
    return outputs


def hair(body,mat):
    rng=random.Random(7704);out=[]
    hairmat=mat['hair']
    capverts=[];capfaces=[];nv=46;nu=80
    for j,t in enumerate(np.linspace(0,1,nv)):
        for k,a in enumerate(np.linspace(0,2*math.pi,nu,endpoint=False)):
            maxtheta=1.51+.38*(math.sin(a)+1)/2
            th=.015+t*maxtheta
            capverts.append((.108*math.sin(th)*math.cos(a),.004+.090*math.sin(th)*math.sin(a),1.845+.111*math.cos(th)))
            if j:
                p=(j-1)*nu+k;q=(j-1)*nu+(k+1)%nu;capfaces.append((p,q,q+nu,p+nu))
    out.append(mesh('Hair fitted scalp',capverts,capfaces,hairmat))
    coremat,bs=base('Hair | inner silver',(.62,.65,.71),.5)
    levels=[(1.935,.045,.068,.032),(1.85,.075,.108,.048),(1.74,.106,.151,.047),(1.62,.14,.185,.042),(1.48,.174,.211,.041),(1.34,.205,.228,.033),(1.17,.233,.188,.026),(1.065,.243,.090,.012),(1.025,.247,.005,.002)]
    cv=[];cf=[]
    for j,(z,cy,rx,ry) in enumerate(levels):
        for k in range(64):
            a=2*math.pi*k/64
            cv.append((rx*math.cos(a),cy+ry*math.sin(a),z+.009*math.cos(5*a)*math.sin(math.pi*j/(len(levels)-1))))
            if j:
                p=(j-1)*64+k;q=(j-1)*64+(k+1)%64;cf.append((p,q,q+64,p+64))
    core=mesh('Hair continuous inner volume',cv,cf,coremat);sub=core.modifiers.new('Smooth silhouette','SUBSURF');sub.levels=sub.render_levels=2;out.append(core)
    guides=[]
    for layer,count in enumerate((13,11,9)):
        for j in range(count):
            f=2*j/(count-1)-1;phase=j*1.17+layer*.6
            endz=(1.00,1.21,1.40)[layer]+.10*abs(f)+.035*math.sin(j*1.6)
            pts=[]
            for i,t in enumerate(np.linspace(0,1,11)):
                x=f*(.075+.19*t)+.025*math.sin(t*math.pi*3.2+phase)*math.sin(math.pi*t)
                x+=np.sign(f)*.035*t**5
                y=.048+.15*t+.043*math.sin(math.pi*t)+layer*.014+.019*math.sin(4.4*math.pi*t+phase)*math.sin(math.pi*t)
                z=1.939*(1-t)+endz*t
                if z<1.22:y=max(y,.245)
                pts.append((x,y,z))
            w=.032+.006*math.cos(j*1.12)
            guides.append((f'Mane {layer}-{j}',pts,[.012,w*.7,w,w,w*.94,w*.88,w*.7,w*.53,w*.33,w*.16,.0003],.47))
    for s in (-1,1):
        for j in range(7):
            f=j/6
            pts=[(s*(.052+.03*f),-.008+.045*f,1.948-.014*f),(s*(.092+.02*f),-.022+.07*f,1.89-.01*f),(s*(.127+.014*f),.004+.085*f,1.81-.02*f),(s*(.16+.018*f),.033+.09*f,1.72-.03*f),(s*(.175+.04*f),.09+.06*f,1.61-.04*f),(s*(.226+.03*f),.11+.06*f,1.54-.06*f),(s*(.252+.035*f),.11+.08*f,1.53-.08*f)]
            guides.append((f'Side wave {s} {j}',pts,[.008,.021,.032,.038,.031,.017,.0003],.52))
        for j in range(2):
            f=j
            pts=[(s*(.006+.01*f),-.103+.018*f,1.961-.004*f),(s*(.042+.007*f),-.133+.012*f,1.94-.01*f),(s*(.083+.014*f),-.149+.012*f,1.902-.018*f),(s*(.099+.014*f),-.145+.033*f,1.835-.02*f),(s*(.102+.015*f),-.130+.06*f,1.775-.035*f),(s*(.117+.020*f),-.105+.065*f,1.744-.04*f),(s*(.158+.025*f),-.082+.05*f,1.753-.045*f)]
            guides.append((f'Forelock {s} {j}',pts,[.007,.018,.022,.022,.019,.012,.0003],.48))
        for j in range(10):
            f=j/9
            pts=[(s*.002,-.101+.16*f,1.955-.018*f),(s*.037,-.105+.175*f,1.966-.022*f),(s*.077,-.08+.17*f,1.943-.026*f),(s*.106,-.028+.14*f,1.90-.045*f),(s*.112,.025+.12*f,1.84-.06*f),(s*.126,.06+.12*f,1.784-.06*f)]
            guides.append((f'Crown wave {s} {j}',pts,[.004,.013,.022,.025,.024,.010],.55))
    for i,(name,pts,widths,depth) in enumerate(guides):
        o=strand(name,pts,widths,hairmat,n=68,sides=18,depth=depth,phase=i*.47);out.append(o)
    return out


def resolve_cloth(clothes,bvh):
    """Remove skin penetration only, without shrinkwrapping loose cloth to the body."""
    for o in clothes:
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
        for m in list(o.modifiers):
            if m.type=='SUBSURF':bpy.ops.object.modifier_apply(modifier=m.name)
        for _ in range(3):
            for v in o.data.vertices:
                hit,n,_,distance=bvh.find_nearest(v.co)
                if hit is None or distance>.12:continue
                separation=(v.co-hit).dot(n)
                if separation<.0040:v.co=hit+n*.0040
            o.data.update()


def build(body,eyes,mat,bvh,front):
    eyes_and_face(body,eyes,mat,bvh,front)
    horns_tail(mat)
    from mathutils.bvhtree import BVHTree
    src=np.empty(len(body.data.vertices)*3);body.data.attributes['source_position'].data.foreach_get('vector',src);src=src.reshape(-1,3)
    torsofaces=[p.vertices[:] for p in body.data.polygons if all(abs(src[k,0])<.19 for k in p.vertices)]
    torso=BVHTree.FromPolygons([v.co for v in body.data.vertices],torsofaces)
    def front_torso(x,z,pad=0):
        hit,_,_,_=torso.ray_cast(Vector((x,-2,z)),Vector((0,1,0)),4)
        return hit.y-pad if hit else None
    clothes=garment(body,mat,torso,front_torso)
    resolve_cloth(clothes,bvh)
    hair(body,mat)
