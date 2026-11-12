"""Art011. Local chest fullness and soft trapezius drape; preserve other anatomy.
Applies only to the verified Art010 model. Saves editable bytes before rendering.
"""
from pathlib import Path
import argparse,hashlib,json,sys,math
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
REVISION='011-fullness-drape-3'

def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def read(o):
 p=np.empty(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',p);return p.reshape(-1,3)
def write(o,p):
 assert np.isfinite(p).all();o.data.vertices.foreach_set('co',p.ravel());o.data.update()
def deform(p):
 x,y,z=p.T;ax=np.abs(x);q=p.copy()
 wall=np.interp(z,[1.25,1.30,1.35,1.40,1.45,1.50,1.55,1.60],[-.166,-.168,-.166,-.158,-.146,-.130,-.109,-.085])+.8*ax*ax
 projection=np.maximum(wall-y,0)
 gate=smooth(1.265,1.315,z)*(1-smooth(1.505,1.575,z))*smooth(.015,.045,ax)*(1-smooth(.238,.276,ax))
 free=smooth(.002,.070,projection)*gate
 q[:,0]+=np.sign(x)*(.004+.075*(ax-.125))*free
 q[:,1]-=(.012+.065*projection)*free
 q[:,2]-=.010*free*(1-smooth(1.40,1.53,z))
 return q

def edit():
 body=bpy.data.objects['Body']
 if body.get('art011'):raise ValueError('Refuse duplicate edit')
 p=read(body);q=deform(p)
 e=np.empty(len(body.data.edges)*2,dtype=np.int32);body.data.edges.foreach_get('vertices',e);e=e.reshape(-1,2)
 a=np.r_[e[:,0],e[:,1]];b=np.r_[e[:,1],e[:,0]];n=np.maximum(np.bincount(a,minlength=len(q)),1)
 x,y,z=p.T;ax=np.abs(x)
 weight=smooth(.018,.040,ax)*(1-smooth(.100,.155,ax))*smooth(1.30,1.35,z)*(1-smooth(1.515,1.56,z))*(1-smooth(-.14,-.09,y))
 for _ in range(16):
  for k in (.43,-.44):
   avg=np.column_stack([np.bincount(a,weights=q[b,i],minlength=len(q))/n for i in range(3)])
   q+=k*weight[:,None]*(avg-q)
 protected=(p[:,2]>1.60)|(p[:,2]<1.25)|(np.abs(p[:,0])>.28)|(p[:,1]>.02)
 assert np.array_equal(p[protected],q[protected])
 attr=body.data.attributes.new('art011_previous_position','FLOAT_VECTOR','POINT');attr.data.foreach_set('vector',p.ravel())
 attr=body.data.attributes.new('art011_delta','FLOAT_VECTOR','POINT');attr.data.foreach_set('vector',(q-p).ravel())
 write(body,q);body['art011']=REVISION;body['clothing_shapes_body']=False
 bvh=BVHTree.FromPolygons([Vector(v) for v in q],[f.vertices[:] for f in body.data.polygons])
 panels=[]
 for side in ('L','R'):
  o=bpy.data.objects['Loose over-trapezius panel '+side];before=read(o)
  assert len(before)==242*33,('unexpected drape topology',len(before))
  grid=deform(before).reshape(242,33,3)
  sign=1 if side=='L' else -1
  # Preserve the continuous strip and waist attachment. Widen the chest panel
  # toward its inner edge while following the already enlarged body.
  for i in range(99):
   t=i/99.;z=grid[i,:,2].mean();w=float(smooth(1.25,1.33,z)*(1-smooth(1.48,1.56,z)))
   for j,u in enumerate(np.linspace(-1,1,33)):
    grid[i,j,0]-=sign*.006*w*(1-u)/2
    xx,yy,zz=grid[i,j]
    h,no,_,_=bvh.ray_cast(Vector((xx,-2,zz)),Vector((0,1,0)),4)
    if h is not None:grid[i,j,1]=min(yy,h.y-.004)
  # The upper strip rests on the trapezius, not on an upright neck collar.
  # Slight asymmetric folds read as cloth; only the inner edge approaches neck.
  for i in range(92,154):
   t=(i-92)/61.;envelope=math.sin(math.pi*t)**2
   for j,u in enumerate(np.linspace(-1,1,33)):
    point=grid[i,j]
    point[0]+=sign*.0015*envelope*(1-u)/2
    # Use the existing continuous shoulder arc. A vertical ray can hit the
    # neck instead of the trapezius, producing a narrow upright spike.
    point[2]-=.0012*envelope
    point[2]+=.00045*envelope*math.sin(2.25*math.pi*u+.8*t+.15*sign)
  # Fair the front/shoulder/back joins without changing endpoint attachment.
  for seam in (99,146):
   for _ in range(10):
    old=grid.copy()
    for i in range(seam-7,seam+8):
     w=.22*math.exp(-((i-seam)/4.)**2);grid[i]=old[i]*(1-w)+.5*w*(old[i-1]+old[i+1])
  write(o,grid.reshape(-1,3));o['art011']=REVISION
  o['construction']='Loose continuous over-trapezius strip; no throat collar. Body shaped first. Only waist cord is cinched.'
  panels.append(o.name)
 bpy.context.scene['art_checkpoint']=REVISION
 return {'revision':REVISION,'changedBodyVertices':int(np.count_nonzero(np.any(q!=p,axis=1))),'protectedVerticesUnchanged':int(np.count_nonzero(protected)),'maxAddedProjectionMetres':float(np.max(p[:,1]-q[:,1])),'maxLoweringMetres':float(np.max(p[:,2]-q[:,2])),'panels':panels,'rigOrPhysicsUpdated':False}

def render(out,views,width,samples):
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=samples;s.cycles.use_denoising=True;s.cycles.device='CPU';s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
 cam=s.camera
 shots={'front':((0,-5,1.30),(0,0,1.06),2.35),'three-quarter':((3,-6,2.1),(0,0,1.06),2.35),'side':((5,0,1.30),(0,0,1.06),2.35),'back':((.15,5,1.30),(0,0,1.06),2.35),'torso':((.15,-4,1.51),(0,-.04,1.44),.90),'shoulder':((.9,-2,2.1),(0,0,1.60),.66)}
 for name in views.split(','):
  loc,target,scale=shots[name];cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale
  s.render.resolution_x=width;s.render.resolution_y=round(width*(1.12 if name in ('torso','shoulder') else 1.3));s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--render-only',action='store_true');ap.add_argument('--views',default='');ap.add_argument('--width',type=int,default=850);ap.add_argument('--samples',type=int,default=24);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
 bpy.ops.wm.open_mainfile(filepath=str(a.source.resolve()))
 if not a.render_only:
  report=edit();bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0;f=out/'Character01_Art011.blend';bpy.ops.wm.save_as_mainfile(filepath=str(f),compress=True);bpy.ops.wm.open_mainfile(filepath=str(f));assert bpy.data.objects['Body'].get('art011')==REVISION
  report.update(savedBlendReopened=True,sourceSha256=hashlib.sha256(a.source.read_bytes()).hexdigest(),files={f.name:{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}});(out/'manifest.json').write_text(json.dumps(report,indent=2));print('ART011_SAVED_REOPENED',flush=True)
 if a.views:render(out,a.views,a.width,a.samples)
if __name__=='__main__':main()
