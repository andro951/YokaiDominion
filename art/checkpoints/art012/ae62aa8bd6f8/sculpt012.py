"""Art012 chest reconstruction. Pinned Art011 master; no unrelated proportion edits."""
from __future__ import annotations
import bpy,numpy as np,math,json,hashlib,sys,argparse
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
REVISION='012-higher-root-hanging-mass-1'
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def read(o):
 a=np.empty(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',a);return a.reshape(-1,3)
def write(o,a):
 assert np.isfinite(a).all();o.data.vertices.foreach_set('co',a.ravel());o.data.update()
def deform(p):
 x,y,z=p.T;ax=abs(x);q=p.copy()
 wall=np.interp(z,[1.24,1.30,1.37,1.44,1.50,1.56,1.64,1.70],[-.152,-.165,-.165,-.149,-.128,-.098,-.055,-.045])+.75*ax*ax
 proj=np.maximum(wall-y,0)
 window=smooth(.012,.042,ax)*(1-smooth(.205,.27,ax))*smooth(1.24,1.29,z)*(1-smooth(1.59,1.68,z))*(1-smooth(-.07,-.035,y))
 fullness=smooth(.004,.105,proj)*window
 root_curve=np.interp(z,[1.24,1.29,1.34,1.40,1.48,1.53,1.59,1.68],[0,0,.010,.035,.072,.070,.038,0])
 q[:,2]+=root_curve*window-.082*fullness
 q[:,1]+=.27*proj*window
 q[:,0]-=np.sign(x)*.026*fullness
 upper=np.exp(-((z-1.525)/.062)**2)*np.exp(-((ax-.115)/.087)**4)*window
 q[:,1]-=.016*upper
 return q

def edit():
 body=bpy.data.objects['Body'];assert not body.get('art012'),'Do not double-apply'
 p=read(body);q=deform(p)
 e=np.empty(len(body.data.edges)*2,dtype=np.int32);body.data.edges.foreach_get('vertices',e);e=e.reshape(-1,2)
 a=np.r_[e[:,0],e[:,1]];b=np.r_[e[:,1],e[:,0]];count=np.maximum(np.bincount(a,minlength=len(p)),1)
 x,y,z=p.T;ax=abs(x)
 w=smooth(.012,.040,ax)*(1-smooth(.22,.27,ax))*smooth(1.265,1.31,z)*(1-smooth(1.57,1.66,z))*(1-smooth(-.08,-.035,y))
 for _ in range(30):
  for factor in (.40,-.405):
   avg=np.column_stack([np.bincount(a,weights=q[b,k],minlength=len(q))/count for k in range(3)])
   q+=factor*w[:,None]*(avg-q)
 protected=(z<=1.24)|(z>=1.68)|(ax>=.27)|(y>=-.035)
 assert np.array_equal(q[protected],p[protected])
 attr=body.data.attributes.new('art012_previous_position','FLOAT_VECTOR','POINT');attr.data.foreach_set('vector',p.ravel())
 attr=body.data.attributes.new('art012_delta','FLOAT_VECTOR','POINT');attr.data.foreach_set('vector',(q-p).ravel())
 write(body,q);body['art012']=REVISION;body['clothing_shapes_body']=False
 tree=BVHTree.FromPolygons([Vector(v) for v in q],[f.vertices[:] for f in body.data.polygons])
 cloth=[]
 for side in ['L','R']:
  o=bpy.data.objects['Loose over-trapezius panel '+side];old=read(o);g=deform(old).reshape(242,33,3)
  for i in range(100):
   for j in range(33):
    xx,yy,zz=g[i,j];hit,normal,_,_=tree.ray_cast(Vector((xx,-2,zz)),Vector((0,1,0)),4)
    if hit is not None:g[i,j,1]=min(yy,hit.y-.004)
  for i in range(1,95):
   t=i/99
   for j,u in enumerate(np.linspace(-1,1,33)):
    g[i,j,1]-=.0013*math.sin(math.pi*t)**2*(1+math.sin(3*math.pi*u+1.1*t))
  write(o,g.reshape(-1,3));o['art012']=REVISION;cloth.append(o.name)
 bpy.context.scene['art_checkpoint']=REVISION
 return {'revision':REVISION,'bodyVertices':len(p),'changedVertices':int(np.any(q!=p,axis=1).sum()),'protectedVerticesUnchanged':int(protected.sum()),'maxDisplacementMetres':float(np.linalg.norm(q-p,axis=1).max()),'clothPanels':cloth,'rigUpdated':False,'physicsUpdated':False,'userApproved':False}

def main():
 a=argparse.ArgumentParser();a.add_argument('--source',type=Path,required=True);a.add_argument('--out',type=Path,required=True);args=a.parse_args(sys.argv[sys.argv.index('--')+1:]);out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
 bpy.ops.wm.open_mainfile(filepath=str(args.source.resolve()));report=edit();bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0
 f=out/'Character01_Art012.blend';bpy.ops.wm.save_as_mainfile(filepath=str(f),compress=True);bpy.ops.wm.open_mainfile(filepath=str(f));assert bpy.data.objects['Body'].get('art012')==REVISION
 report.update(sourceSha256=hashlib.sha256(args.source.read_bytes()).hexdigest(),savedBlendReopened=True,files={f.name:{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}})
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print('ART012_SAVED_REOPENED',flush=True)
if __name__=='__main__':main()
