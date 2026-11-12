"""Final complexion and garment/tail finishing on the actual art master."""
import math
import bpy
import numpy as np
from mathutils import Vector
from geometry import tube,mesh
from materials import linear,base
import finish_details

def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)

def apply_complexion(body):
    n=len(body.data.vertices);p=np.empty(n*3);body.data.attributes['source_position'].data.foreach_get('vector',p);p=p.reshape(-1,3)
    x,y,z=p.T;ax=np.abs(x);c=np.tile(np.array(linear((.425,.433,.520))),(n,1))
    def paint(w,col):
        nonlocal c
        w=np.clip(w,0,1)[:,None];c=c*(1-w)+np.array(linear(col))*w
    front=1-smooth(-.075,-.045,y)
    lips=np.exp(-((x/.025)**8)-((z-1.467)/.0062)**6)*(1-smooth(-.096,-.075,y));paint(lips*.8,(.34,.275,.37))
    paint(np.exp(-((ax-.033)/.024)**2-((z-1.544)/.009)**2)*front*.48,(.245,.235,.33))
    paint(np.exp(-((ax-.033)/.023)**2-((z-1.523)/.007)**2)*front*.20,(.32,.30,.40))
    mark=np.zeros(n)
    for cx,cz,wx,wz,angle in [(.163,1.315,.011,.017,-.62),(.183,1.291,.010,.021,-.62),(.205,1.263,.010,.023,-.53),(.262,1.056,.008,.027,-.52),(.285,1.013,.008,.027,-.52),(.305,.973,.007,.024,-.52)]:
        dx=ax-cx;dz=z-cz;u=dx*math.cos(angle)-dz*math.sin(angle);v=dx*math.sin(angle)+dz*math.cos(angle)
        vv=np.clip(v/wz,-1,1);width=wx*(.78+.22*vv);r=(u/width)**2+(v/wz)**2
        w=(1-smooth(.82,1.0,r))*(1-smooth(.006,.035,y));mark=np.maximum(mark,w)
    paint(mark,(.235,.225,.32))
    ear=smooth(.069,.081,ax)*np.exp(-((z-1.52)/.018)**2)*(1-smooth(-.02,.012,y));paint(ear*.38,(.33,.305,.42))
    a=body.data.color_attributes.get('Complexion');a.data.foreach_set('color',np.c_[c,np.ones(n)].ravel());body.data.color_attributes.active_color=a

def tail_opening():
    o=bpy.data.objects.get('Back hanging cloth')
    if o is None:return
    import bmesh
    bm=bmesh.new();bm.from_mesh(o.data);remove=[]
    for f in bm.faces:
        p=f.calc_center_median()
        if ((p.x-.031)/.035)**2+((p.z-.994)/.042)**2<1:remove.append(f)
    bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(o.data);bm.free();o.data.update()

def install():
    original=finish_details.build
    def build(body,eyes,mat,bvh,front):
        original(body,eyes,mat,bvh,front)
        apply_complexion(body);tail_opening()
        body['anatomy_basis']='Official Blender CC0 female; localized non-clothing-driven physique';body['art_revision']='005'
        for o in bpy.data.objects:
            if o.type=='MESH' and not o.name.startswith('STUDIO'):o['role']='anatomical_surface' if o==body else 'separate_character_detail'
    finish_details.build=build
