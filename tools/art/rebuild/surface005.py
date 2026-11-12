"""Final anatomical surface relief and surface-following markings."""
import math
import bpy
import numpy as np
from mathutils.bvhtree import BVHTree
from materials import linear
import finish_details

def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)

def finish_surface(body):
    n=len(body.data.vertices);src=np.empty(n*3);body.data.attributes['source_position'].data.foreach_get('vector',src);src=src.reshape(-1,3)
    q=np.empty(n*3);body.data.vertices.foreach_get('co',q);q=q.reshape(-1,3)
    x,y,z=src.T;ax=np.abs(x);front=1-smooth(-.095,-.065,y);ab=np.zeros(n)
    for height in (1.096,1.043):ab+=.004*np.exp(-((ax-.040)/.029)**4-((z-height)/.024)**4)
    groove=.0018*np.exp(-(x/.008)**2-((z-1.067)/.082)**4)
    for height in (1.071,1.018):groove+=.0013*np.exp(-((z-height)/.006)**2)*(1-smooth(.060,.080,ax))
    q[:,1]+=(groove-ab)*front;body.data.vertices.foreach_set('co',q.ravel());body.data.update()
    c=np.empty(n*4);body.data.color_attributes['Complexion'].data.foreach_get('color',c);c=c.reshape(-1,4)
    region=(ax>.13)&(z>.89)&(z<1.36);c[region,:3]=linear((.425,.433,.520));mark=np.zeros(n)
    for sign in (-1.,1.):
        points=src.copy();points[:,0]*=sign
        for a,b,centers in [((.165,.010,1.31),(.244,.010,1.07),[(.08,1.17,.075,.31),(.23,1.22,.083,.34),(.39,1.27,.095,.32)]),((.244,.010,1.07),(.343,-.017,.866),[(.20,1.10,.095,.32),(.43,1.19,.10,.32),(.66,1.25,.10,.30)])]:
            a=np.array(a);b=np.array(b);axis=b-a;length=np.linalg.norm(axis);axis/=length
            t=(points-a)@axis/length;radial=points-a-t[:,None]*length*axis
            lateral=np.array([1.,0,0]);lateral-=axis*(axis@lateral);lateral/=np.linalg.norm(lateral);anterior=np.cross(axis,lateral)
            if anterior[1]>0:anterior=-anterior
            phi=np.arctan2(radial@anterior,radial@lateral)
            for tc,pc,ht,hp in centers:
                u=(t-tc)/ht;v=np.arctan2(np.sin(phi-pc),np.cos(phi-pc))/hp;width=.74+.26*np.clip(u,-1,1);r=u*u+(v/width)**2
                w=(1-smooth(.84,1.0,r))*smooth(.115,.14,sign*x);mark=np.maximum(mark,w)
    mark*=region;c[:,:3]=c[:,:3]*(1-mark[:,None])+np.array(linear((.185,.185,.27)))*mark[:,None]
    body.data.color_attributes['Complexion'].data.foreach_set('color',c.ravel())
    bvh=BVHTree.FromPolygons([v.co for v in body.data.vertices],[p.vertices[:] for p in body.data.polygons])
    for o in bpy.data.objects:
        if o.type=='MESH' and o.name.startswith('Continuous neck fabric'):
            for i,v in enumerate(o.data.vertices):
                if i<33:continue
                h,no,_,distance=bvh.find_nearest(v.co)
                if h and distance<.035:v.co=h+no*.0045
            o.data.update()
    hair=bpy.data.materials.get('Hair | ivory silver')
    if hair:
        bs=hair.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.46
    body['clothing_shapes_body']=False;body['geometry_units']='metres'

def install():
    previous=finish_details.build
    def build(body,eyes,mat,bvh,front):
        previous(body,eyes,mat,bvh,front);finish_surface(body)
    finish_details.build=build
