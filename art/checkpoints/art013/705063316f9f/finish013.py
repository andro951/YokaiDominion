"""Localized final-form review pass on the saved Art012 master.
Redistribute a small amount of contour into the lower breast, then fair existing
physically relaxed cloth. Never move shoulders/hips or use cloth to reshape body.
"""
from pathlib import Path
import argparse, hashlib, json, sys
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
REVISION='013-contour-drape-2'
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def positions(o):
 p=np.empty(len(o.data.vertices)*3,dtype=np.float64);o.data.vertices.foreach_get('co',p);return p.reshape(-1,3)
def set_positions(o,p):
 if not np.isfinite(p).all():raise ValueError('Nonfinite geometry')
 o.data.vertices.foreach_set('co',p.ravel());o.data.update()
def deform(p):
 x,y,z=p.T;ax=abs(x);q=p.copy()
 wall=np.interp(z,[1.25,1.30,1.35,1.40,1.45,1.50,1.55,1.60],[-.166,-.168,-.166,-.158,-.146,-.130,-.109,-.085])+.8*ax*ax
 free=smooth(.003,.065,wall-y)*smooth(1.275,1.31,z)*(1-smooth(1.52,1.59,z))*smooth(.012,.035,ax)*(1-smooth(.22,.26,ax))
 q[:,1]+=(.005*np.exp(-((z-1.46)/.062)**2)-.004*np.exp(-((z-1.342)/.048)**2))*free
 q[:,2]-=.006*np.exp(-((z-1.395)/.078)**2)*free
 return q

def edit(source,out):
 bpy.ops.wm.open_mainfile(filepath=str(source));body=bpy.data.objects['Body']
 if body.get('art013'):raise ValueError('Already processed')
 p=positions(body);q=deform(p)
 protected=(p[:,2]>=1.60)|(p[:,2]<=1.25)|(abs(p[:,0])>=.27)|(p[:,1]>=.02)
 assert np.array_equal(p[protected],q[protected])
 set_positions(body,q);body['art013']=REVISION
 # Float-vector deltas permit exact reconstruction without duplicating topology.
 for name,values in [('art013_previous_position',p),('art013_delta',q-p)]:
  at=body.data.attributes.new(name,'FLOAT_VECTOR','POINT');at.data.foreach_set('vector',values.ravel())
 bvh=BVHTree.FromPolygons([Vector(v) for v in q],[f.vertices[:] for f in body.data.polygons])
 reports=[]
 for name in ['Loose over-trapezius panel L','Loose over-trapezius panel R']:
  o=bpy.data.objects[name];before=positions(o);g=deform(before).reshape(242,33,3)
  # Keep the established over-trapezius route and cord endpoints unchanged.
  row=np.arange(242);weight=(smooth(3,13,row)*(1-smooth(87,101,row)))
  rear=smooth(146,160,row)*(1-smooth(226,239,row));weight=np.maximum(weight,.45*rear)
  for _ in range(28):
   old=g.copy();avg=(old[:-2]+old[2:])*.5;g[1:-1]+=.36*weight[1:-1,None,None]*(avg-old[1:-1])
   old=g.copy();g[:,1:-1]+=.12*weight[:,None,None]*((old[:,:-2]+old[:,2:])*.5-old[:,1:-1])
  # Add broad longitudinal folds along the cloth normal, with zero edge offset.
  # They sit outside the existing drape rather than squeezing the body.
  old=g.copy()
  for i in range(4,96):
   t=i/99.;envelope=float(weight[i]);u=np.linspace(0,1,33)
   width_tangent=np.gradient(old[i],axis=0);length_tangent=old[i+1]-old[i-1]
   normal=np.cross(width_tangent,length_tangent)
   normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-10)
   if normal[16,1]>0:normal=-normal
   broad=(.0035+.0015*np.sin(np.pi*t)**2)*envelope
   fold=broad*np.sin(np.pi*u)**.7*(.5+.5*np.cos(4*np.pi*u+.5*np.sin(2*np.pi*t)))
   g[i]+=normal*fold[:,None]
  # Only resolve inward intersections; do not turn the cloth into a skin-tight shell.
  corrected=0;worst=0.
  for i in range(4,101):
   for j in range(33):
    hit,normal,_,distance=bvh.find_nearest(Vector(g[i,j]))
    if hit is not None and distance<.025:
     signed=(Vector(g[i,j])-hit).dot(normal)
     if signed<.0022:
      g[i,j]+=np.array(normal)*(.0022-signed);corrected+=1;worst=max(worst,.0022-signed)
  after=g.reshape(-1,3);set_positions(o,after);o['art013']=REVISION
  reports.append({'name':name,'maxDisplacementMetres':float(np.linalg.norm(after-before,axis=1).max()),'clearanceCorrections':corrected,'maxClearanceCorrectionMetres':worst})
 bpy.context.scene['art_checkpoint']=REVISION
 bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0
 path=out/'Character01_Art013.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
 report={'revision':REVISION,'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'bodyVertices':len(p),'changedBodyVertices':int(np.any(q!=p,axis=1).sum()),'protectedVertices':int(protected.sum()),'protectedVerticesUnchanged':True,'maxBodyDisplacementMetres':float(np.linalg.norm(q-p,axis=1).max()),'garment':reports,'staticVisualOnly':True,'rigUpdated':False,'runtimePhysicsUpdated':False,'files':{path.name:{'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}}}
 bpy.ops.wm.open_mainfile(filepath=str(path));assert bpy.data.objects['Body']['art013']==REVISION
 report['savedBlendReopened']=True;(out/'manifest.json').write_text(json.dumps(report,indent=2));print('ART013_SAVED_REOPENED',flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);a.out.mkdir(parents=True,exist_ok=True);edit(a.source.resolve(),a.out.resolve())
