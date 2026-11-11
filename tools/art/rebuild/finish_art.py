"""Reproducible anatomical art master. No garment modifies the body mesh.
Usage: blender -b --python finish_art.py -- --source female-base.blend --out output
"""
from __future__ import annotations
import argparse,sys,math,json,hashlib,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import anatomy
from anatomy import smooth,gauss
from geometry import mesh,tube,ribbon,strand,catmull
from materials import palette,base,linear

P=argparse.ArgumentParser();P.add_argument('--source',type=Path,required=True);P.add_argument('--out',type=Path,required=True);P.add_argument('--views',default='front,portrait');P.add_argument('--samples',type=int,default=32);P.add_argument('--detail',type=int,default=1);P.add_argument('--body-only',action='store_true');P.add_argument('--export',action='store_true');P.add_argument('--width',type=int,default=950)
ARGS=P.parse_args(sys.argv[sys.argv.index('--')+1:]);OUT=ARGS.out.resolve();OUT.mkdir(parents=True,exist_ok=True)


def get_co(o):
    a=np.empty(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',a);return a.reshape(-1,3)
def source_co(o):
    a=np.empty(len(o.data.vertices)*3);o.data.attributes['source_position'].data.foreach_get('vector',a);return a.reshape(-1,3)

def refine_body(body):
    p=source_co(body);q=get_co(body);x,y,z=p.T;ax=np.abs(x);sg=np.where(x>=0,1.,-1.)
    front=1-smooth(-.06,-.015,y)
    # Rounded deltoids and diagonal clavicles, without widening the thorax.
    q[:,1]-=.0045*gauss(ax,.146,.045)*gauss(z,1.296,.041)*front
    clavz=1.335-.11*(ax-.05)
    q[:,1]-=.0035*gauss(z,clavz,.007)*smooth(.025,.05,ax)*(1-smooth(.126,.159,ax))*front
    q[:,2]-=.005*gauss(z,1.325,.035)*gauss(ax,.19,.042)
    # Gentle neck tendons, not a cylindrical pillar.
    scm=gauss(ax,.024+.36*(1.43-z),.010)*gauss(z,1.389,.052)*front
    q[:,1]-=.0025*scm
    # Anatomical abdominal groove and oblique transition.
    q[:,1]+=.0026*gauss(x,0,.008)*gauss(z,1.065,.071)*front
    # Mature face: subtly lifted outer eyelids, firmer cheek plane and smirk.
    face=(1-smooth(-.08,-.045,y))*smooth(1.44,1.46,z)
    q[:,1]-=.0018*gauss(ax,.046,.026)*gauss(z,1.502,.018)*face
    q[:,0]-=sg*.002*gauss(ax,.049,.026)*gauss(z,1.449,.035)*face
    corner=gauss(ax,.022,.010)*gauss(z,1.465,.008)*face
    q[:,2]+=(.0015+.0015*(x>0))*corner
    nose=gauss(z,1.494,.021)*(1-smooth(-.099,-.081,y))
    q[:,0]-=x*.13*nose
    # Preserve natural lip detail; no separate oversized lips.
    body.data.vertices.foreach_set('co',q.ravel());body.data.update()
    c=np.tile(np.array(linear((.43,.44,.515))), (len(p),1))
    def paint(mask,col):
        nonlocal c
        t=np.clip(mask,0,1)[:,None];c=c*(1-t)+np.array(linear(col))*t
    # Low-contrast complexion, lips, crease shading and eye makeup.
    lipzone=np.exp(-((x/.025)**8)-((z-1.467)/.0062)**6)*(1-smooth(-.096,-.075,y))
    paint(lipzone*.78,(.37,.31,.42))
    paint(gauss(ax,.033,.021)*gauss(z,1.545,.011)*face*.48,(.29,.27,.36))
    paint(gauss(ax,.033,.023)*gauss(z,1.523,.007)*face*.23,(.31,.295,.39))
    # Long tapered markings follow the arm surface rather than floating decals.
    mark=np.zeros(len(p))
    for cx,cz,wx,wz,angle in [(.162,1.314,.013,.022,-.5),(.185,1.293,.012,.025,-.65),(.205,1.268,.010,.025,-.65),(.223,1.24,.010,.024,-.65),(.266,1.045,.011,.030,-.6),(.285,1.010,.010,.032,-.6),(.301,.976,.009,.028,-.6)]:
        dx=ax-cx;dz=z-cz;u=dx*math.cos(angle)-dz*math.sin(angle);v=dx*math.sin(angle)+dz*math.cos(angle)
        leaf=(u/(wx*np.maximum(.1,1-(v/wz)**2)))**2+(v/wz)**2
        mm=(1-smooth(.7,1.05,leaf))*(1-smooth(.012,.045,y))
        mark=np.maximum(mark,mm)
    paint(mark,(.235,.225,.31))
    a=body.data.color_attributes.new(name='Complexion',type='FLOAT_COLOR',domain='POINT')
    a.data.foreach_set('color',np.c_[c,np.ones(len(p))].ravel());body.data.color_attributes.active_color=a
    body.data.materials.append(MAT['skin'])
    # The native topology and source UVs remain available for editing/baking.
    return body


def make_bvh(o):
    return BVHTree.FromPolygons([v.co for v in o.data.vertices],[p.vertices[:] for p in o.data.polygons],all_triangles=False)

def front_surface(x,z,pad=0.):
    hit,n,_,_=BODYBVH.ray_cast(Vector((x,-2,z)),Vector((0,1,0)),4)
    return (hit.y-pad) if hit else None

def face_point(x,z,pad=.0008):
    y=front_surface(x,z,pad)
    return (x,y if y is not None else -.14,z)


def scene_setup():
    sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1
    sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=ARGS.samples;sc.cycles.use_denoising=True
    sc.render.resolution_x=ARGS.width;sc.render.resolution_y=int(ARGS.width*1.3);sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG';sc.render.film_transparent=False
    sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=.25
    world=bpy.data.worlds.new('Studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.11,.13,.17,1);world.node_tree.nodes['Background'].inputs[1].default_value=.36;sc.world=world
    floor,bs=base('Studio floor',(.105,.12,.145),.8)
    bpy.ops.mesh.primitive_plane_add(size=2000,location=(0,0,-.005));o=bpy.context.object;o.name='STUDIO Ground';o.data.materials.append(floor)
    def area(name,loc,power,size,col,target=(0,0,1.1)):
        d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=col
        o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    area('STUDIO Key',(-3,-4,5),520,3.0,(1,.92,.86))
    area('STUDIO Fill',(3,-2,3.1),260,2.8,(.78,.85,1))
    area('STUDIO Rim',(1,2,4.2),720,2.2,(.85,.90,1))
    d=bpy.data.cameras.new('Review camera');o=bpy.data.objects.new('STUDIO Camera',d);bpy.context.collection.objects.link(o);sc.camera=o
    return o


def render_view(cam,name):
    views={
    'front':((0,-6,1.23),(0,0,1.12),2.50),
    'three-quarter':((3.3,-6,2.15),(0,0,1.12),2.52),
    'side':((6,-.08,1.35),(0,0,1.12),2.5),
    'back':((.1,6,1.4),(0,0,1.12),2.5),
    'portrait':((.28,-3,1.91),(0,-.035,1.86),.73),
    'torso':((1.1,-4,1.57),(0,-.04,1.42),1.08),
    'reference':((.6,-5,1.94),(0,-.05,1.54),1.38)}
    pos,target,scale=views[name];cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale
    bpy.context.scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)

body,eyes=anatomy.load_body(ARGS.source,ARGS.detail)
MAT=palette();refine_body(body);BODYBVH=make_bvh(body)
for eye in eyes:
 eye.data.materials.append(MAT['sclera'])
# Accessories are added by the finishing module when present.
if not ARGS.body_only:
    try:
        import finish_details
        finish_details.build(body,eyes,MAT,BODYBVH,front_surface)
    except ModuleNotFoundError as e:
        if e.name!='finish_details':raise
camera=scene_setup()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character01_ArtMaster.blend'),compress=True)
np.savez_compressed(OUT/'body-surface.npz',vertices=get_co(body),source=source_co(body))
for view in ARGS.views.split(','):
 if view:render_view(camera,view)
print('ART_PASS_COMPLETE',str(OUT))
