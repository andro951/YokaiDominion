"""Build and package the first MakeHuman study. Only review coverage is smoothed."""
import sys,json,hashlib,math
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build,review

def finish(out):
 path=out/'MakeHuman_Oni_Stage01.blend';bpy.ops.wm.open_mainfile(filepath=str(path));body=bpy.data.objects['MakeHuman_Oni_Body'];before=build.coords(body).copy()
 dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);m=ev.to_mesh();p=np.array([v.co[:] for v in m.vertices]);faces=[list(f.vertices) for f in m.polygons];ev.to_mesh_clear();bvh=BVHTree.FromPolygons([Vector(v) for v in p],faces)
 for side in [-1,1]:
  ob=bpy.data.objects['Review drape '+('L' if side>0 else 'R')];q=build.coords(ob).reshape(84,18,3)
  for i in range(84):
   z=q[i,0,2];cx=np.interp(z,[1.1,1.22,1.3,1.40,1.52],[.07,.095,.122,.105,.082]);width=np.interp(z,[1.1,1.22,1.3,1.43,1.52],[.035,.043,.058,.047,.030]);ys=[]
   for j,u in enumerate(np.linspace(-1,1,18)):
    x=side*(cx+width*u);hit,_,_,_=bvh.ray_cast(Vector((x,-.6,z)),Vector((0,1,0)),1.0);q[i,j,0]=x;ys.append(hit.y-.006 if hit is not None else np.nan)
   good=np.flatnonzero(np.isfinite(ys));assert len(good)>0
   ys=np.interp(np.arange(18),good,np.array(ys)[good]);q[i,:,1]=ys
  k=int(np.argmin(abs(q[:,0,2]-1.29)))
  for j,u in enumerate(np.linspace(-1,1,18)):
   t=np.linspace(0,1,k+1);yy=q[0,j,1]*(1-t)+q[k,j,1]*t-.007*np.sin(np.pi*t)
   q[:k+1,j,1]=np.minimum(q[:k+1,j,1],yy)
  for _ in range(12):
   r=q.copy();q[1:-1,:,1]=.6*r[1:-1,:,1]+.2*(r[:-2,:,1]+r[2:,:,1])
  ob.data.vertices.foreach_set('co',q.ravel());ob.data.update()
 ob=bpy.data.objects['Review lower cover'];q=build.coords(ob);edges={}
 for poly in ob.data.polygons:
  ids=poly.vertices[:]
  for a,b in zip(ids,ids[1:]+ids[:1]):
   e=tuple(sorted((a,b)));edges[e]=edges.get(e,0)+1
 adj={}
 for (a,b),num in edges.items():
  if num==1:adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
 for _ in range(18):
  old=q.copy()
  for i,ns in adj.items():
   point=.5*old[i]+.5*old[ns].mean(0);hit,n,_,_=bvh.find_nearest(Vector(point))
   if hit is not None:q[i]=np.array(hit)+np.array(n)*.0033
 ob.data.vertices.foreach_set('co',q.ravel());ob.data.update()
 assert np.array_equal(before,build.coords(body))
 review.setup();body['stage']='makehuman-stage01-3';body['native_body_not_sculpted']=True
 bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
 bpy.ops.wm.open_mainfile(filepath=str(path));assert bpy.data.objects['MakeHuman_Oni_Body'].data.shape_keys
 report=json.loads((out/'manifest.json').read_text());report['revision']='makehuman-stage01-3';report['temporaryCoverageSmoothed']=True;report['studioCameraAndLightsIncluded']=True;report['files'][path.name]=build.digest(path)
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print('MAKEHUMAN_STAGE01_FINAL_SAVED',flush=True)

if __name__=='__main__':
 build.main();a=sys.argv[sys.argv.index('--')+1:];out=Path(a[a.index('--out')+1]).resolve();finish(out)
