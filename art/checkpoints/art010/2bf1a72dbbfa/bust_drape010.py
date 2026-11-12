"""Art010: larger dependent breast forms and over-trapezius loose cloth.
Edits the real Art008 master. No rig or physics acceptance is implied.
"""
from pathlib import Path
import argparse, hashlib, json, math, sys
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
REVISION='010-bust-trapezius-3'

def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def read(o):
 p=np.empty(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',p);return p.reshape(-1,3)
def write(o,p):
 if not np.isfinite(p).all():raise ValueError('Nonfinite geometry')
 o.data.vertices.foreach_set('co',p.ravel());o.data.update()
def edit():
 body=bpy.data.objects['Body']
 if body.get('art010'):raise ValueError('Refusing to apply chest enlargement twice')
 p=read(body);q=p.copy();x,y,z=p.T;ax=np.abs(x)
 changed=np.zeros(len(q),dtype=bool)
 attached=smooth(1.307,1.340,z)*(1-smooth(1.505,1.565,z))*(1-smooth(.185,.228,ax))*smooth(.020,.044,ax)
 # Integrate local expansion instead of extruding a hard patch. The abdomen and
 # breast-root attachment boundaries remain fixed, independently of clothing.
 for step in range(60):
  t=(step+.5)/60;xx,yy,zz=q.T;au=np.abs(xx);cx=.123+.020*t;cz=1.405+.010*t
  rho=np.sqrt(((au-cx)/(.117*(1+.28*t)))**2+((zz-cz)/(.145*(1+.25*t)))**2)
  mask=(1-smooth(.42,1.38,rho))*(1-smooth(-.102,-.060,yy))*smooth(.016,.040,au)*smooth(1.215,1.300,zz)*attached
  changed|=mask>0
  q[:,0]+=np.sign(xx)*(.025+.40*(au-cx))*mask/60
  q[:,1]+=(math.log(1.95)*(yy+.115)-.009)*mask/60
  q[:,2]+=(math.log(1.45)*(zz-1.370)+.009)*mask/60
 unchanged=~changed
 assert np.array_equal(p[unchanged],q[unchanged])
 attr=body.data.attributes.new('art010_previous_position','FLOAT_VECTOR','POINT');attr.data.foreach_set('vector',p.ravel())
 write(body,q);body['art010']=REVISION;body['clothing_shapes_body']=False
 body['asset_kind']='Visual master: enlarged bust and corrected drape; animation/physics not refitted'
 old=bpy.data.objects['Continuous loose neck-to-waist halter'];mat=old.data.materials[0]
 old.hide_render=True;old.hide_viewport=True;old['replaced_by']='Loose over-trapezius panels Art010'
 for c in list(old.users_collection):c.objects.unlink(old)
 bpy.data.collections['99_ARCHIVED_PARTS'].objects.link(old)
 bvh=BVHTree.FromPolygons([Vector(v) for v in q],[f.vertices[:] for f in body.data.polygons])
 def surf(x,z,rear=False):
  h,_,_,_=bvh.ray_cast(Vector((x,2 if rear else -2,z)),Vector((0,-1 if rear else 1,0)),4)
  if h:return h.y
  return None
 def top(x,y):
  h,_,_,_=bvh.ray_cast(Vector((x,y,1.73)),Vector((0,0,-1)),.35)
  if h:return h.z
  raise ValueError('Missing trapezius support')
 panels=[]
 for side in (-1,1):
  zs=np.array([1.197,1.235,1.285,1.33,1.40,1.48,1.55,1.598])
  centers=np.array([.085,.105,.153,.183,.193,.169,.132,.107])
  widths=np.array([.064,.055,.049,.048,.047,.041,.027,.024])
  front=[];guide=np.column_stack([zs,centers,widths])
  for t in np.linspace(0,1,100):
   tt=t*(len(guide)-1);k=min(int(tt),len(guide)-2);u0=tt-k
   a0=guide[max(0,k-1)];a1=guide[k];a2=guide[k+1];a3=guide[min(k+2,len(guide)-1)]
   z0,cx,w=.5*((2*a1)+(-a0+a2)*u0+(2*a0-5*a1+4*a2-a3)*u0*u0+(-a0+3*a1-3*a2+a3)*u0**3)
   row=[]
   for u in np.linspace(-1,1,33):
    xx=side*(cx+w*u);zz=z0+.0025*math.sin(math.pi*t)*u;yy=surf(xx,zz)
    if yy is None:
     h,n,_,_=bvh.find_nearest(Vector((xx,-.15,zz)));yy=float(h.y)
    fold=(.001+.0018*math.sin(math.pi*t)**2)*(1+math.sin(2.3*math.pi*u+2*t+.3*side))
    row.append([xx,yy-.006-fold,zz])
   front.append(row)
  a=np.array(front);obstacle=-a[:,:,1];depth=obstacle.copy()
  for _ in range(180):
   avg=depth.copy();avg[1:-1,1:-1]=.25*(depth[:-2,1:-1]+depth[2:,1:-1]+depth[1:-1,:-2]+depth[1:-1,2:])
   avg[1:-1,0]=.5*depth[1:-1,1]+.25*(depth[:-2,0]+depth[2:,0]);avg[1:-1,-1]=.5*depth[1:-1,-2]+.25*(depth[:-2,-1]+depth[2:,-1])
   depth=np.maximum(obstacle,avg)
  a[:,:,1]=-depth
  for j in range(33):
   k=int(np.argmin(a[:,j,1]));t=np.linspace(0,1,k+1)
   bridge=a[0,j,1]*(1-t)+a[k,j,1]*t-.005*np.sin(math.pi*t)
   a[:k+1,j,1]=np.minimum(a[:k+1,j,1],bridge)
  rear=[]
  for t in np.linspace(0,1,96):
   zz=1.598-(1.598-1.197)*t;cx=.107-.022*t;w=.025+.039*t**2;row=[]
   for u in np.linspace(-1,1,33):
    xx=side*(cx+w*u);yy=surf(xx,zz,True)
    if yy is None:raise ValueError('Missing back support')
    row.append([xx,yy+.006+.001*(1+math.sin(2.3*math.pi*u+1.4*t)),zz])
   rear.append(row)
  rear=np.array(rear);shoulder=[]
  for t in np.linspace(0,1,48):
   row=[]
   for j,u in enumerate(np.linspace(-1,1,33)):
    xx=a[-1,j,0];yy=(a[-1,j,1]+.006)*(1-t)+(rear[0,j,1]-.006)*t
    zz=top(xx,yy)+.005+.0006*math.sin(2*math.pi*u+.7*t)
    row.append([xx,yy,zz])
   shoulder.append(row)
  shoulder=np.array(shoulder);shoulder[0]=a[-1];shoulder[-1]=rear[0]
  v=np.concatenate([a[:-1],shoulder,rear[1:]])
  for seam in (99,146):
   for _ in range(8):
    src=v.copy()
    for i in range(seam-5,seam+6):
     w=.20*math.exp(-((i-seam)/3)**2);v[i]=src[i]*(1-w)+w*.5*(src[i-1]+src[i+1])
  nr,nc,_=v.shape;faces=[]
  for i in range(nr-1):
   for j in range(nc-1):
    k=i*nc+j;f=(k,k+1,k+nc+1,k+nc);faces.append(f if side>0 else f[::-1])
  mesh=bpy.data.meshes.new('Art010_ContinuousDrape');mesh.from_pydata(v.reshape(-1,3),[],faces);mesh.update()
  obj=bpy.data.objects.new('Loose over-trapezius panel '+('L' if side>0 else 'R'),mesh);bpy.data.collections['04_GARMENT'].objects.link(obj);mesh.materials.append(mat)
  uv=mesh.uv_layers.new(name='GarmentUV')
  for f in mesh.polygons:
   f.use_smooth=True
   for li in f.loop_indices:
    vi=mesh.loops[li].vertex_index;uv.data[li].uv=((vi%nc)/(nc-1),(vi//nc)/(nr-1))
  m=obj.modifiers.new('Soft fabric surface','SUBSURF');m.levels=m.render_levels=1
  m=obj.modifiers.new('Fabric thickness','SOLIDIFY');m.thickness=.0011;m.offset=0
  obj['construction']='Continuous front-to-back loose strip over upper trapezius. No transverse neck collar, cups, underband, or breast lift.'
  obj['role']='separate_character_detail';panels.append(obj.name)
 bpy.context.scene['art_checkpoint']=REVISION
 return {'revision':REVISION,'bodyVertices':len(q),'changedVertices':int(np.count_nonzero(changed)),'otherBodyVerticesUnchanged':True,'maxAddedProjectionMetres':float((p[:,1]-q[:,1]).max()),'newPanels':panels,'rigOrPhysicsUpdated':False}

def render(out,views,width,samples):
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=samples;scene.cycles.use_denoising=True;scene.cycles.device='CPU';scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
 camera=scene.camera
 shots={'front':((0,-5,1.30),(0,0,1.06),2.35),'three-quarter':((3,-6,2.1),(0,0,1.06),2.35),'side':((5,0,1.30),(0,0,1.06),2.35),'back':((.15,5,1.30),(0,0,1.06),2.35),'torso':((.15,-4,1.51),(0,-.04,1.44),.90),'shoulder':((.9,-2,2.1),(0,0,1.60),.66)}
 for view in views.split(','):
  loc,target,scale=shots[view];camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=scale
  scene.render.resolution_x=width;scene.render.resolution_y=round(width*(1.12 if view in ('torso','shoulder') else 1.3));scene.render.filepath=str(out/(view+'.png'));bpy.ops.render.render(write_still=True)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--render-only',action='store_true');ap.add_argument('--views',default='');ap.add_argument('--width',type=int,default=900);ap.add_argument('--samples',type=int,default=32)
 a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=a.out.resolve();out.mkdir(parents=True,exist_ok=True);bpy.ops.wm.open_mainfile(filepath=str(a.source.resolve()))
 if not a.render_only:
  report=edit();bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0;f=out/'Character01_Art010.blend';bpy.ops.wm.save_as_mainfile(filepath=str(f),compress=True);bpy.ops.wm.open_mainfile(filepath=str(f));assert bpy.data.objects['Body'].get('art010')==REVISION
  report.update({'savedBlendReopened':True,'sourceSha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),'files':{f.name:{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}}});(out/'manifest.json').write_text(json.dumps(report,indent=2));print('ART010_SAVED_REOPENED',flush=True)
 if a.views:render(out,a.views,a.width,a.samples)
if __name__=='__main__':main()
