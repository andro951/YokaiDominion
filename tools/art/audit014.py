"""Independent saved-file audit of Art014 face-only scope."""
import bpy,numpy as np,json,hashlib,argparse,sys
from pathlib import Path

def arr(collection,field,width,dtype=np.float32):
 a=np.empty(len(collection)*width,dtype=dtype);collection.foreach_get(field,a);return a.reshape(-1,width)
def digest(a):return hashlib.sha256(a.tobytes()).hexdigest()
def mesh_meta(o):
 m=o.data;uv={v.name:digest(arr(v.data,'uv',2)) for v in m.uv_layers};colors={v.name:digest(arr(v.data,'color',4)) for v in m.color_attributes}
 return {'loops':digest(arr(m.loops,'vertex_index',1,np.int32)),'edges':digest(arr(m.edges,'vertices',2,np.int32)),'uv':uv,'colors':colors,'materials':[m.name if m else None for m in m.materials]}
def others():
 result={}
 for o in bpy.data.objects:
  if o.type!='MESH' or o.name=='Body':continue
  result[o.name]={'vertices':digest(arr(o.data.vertices,'co',3)),'matrix':digest(np.array(o.matrix_world,dtype=np.float64)), 'mesh':mesh_meta(o),'hideRender':o.hide_render}
 return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
 bpy.ops.wm.open_mainfile(filepath=str(a.before.resolve()));before=arr(bpy.data.objects['Body'].data.vertices,'co',3);meta=mesh_meta(bpy.data.objects['Body']);extra=others()
 bpy.ops.wm.open_mainfile(filepath=str(a.after.resolve()));body=bpy.data.objects['Body'];after=arr(body.data.vertices,'co',3);assert before.shape==after.shape
 nonface=(before[:,2]<=1.685)|(before[:,2]>=1.840)|(abs(before[:,0])>=.113)|(before[:,1]>=-.025)
 assert np.array_equal(before[nonface],after[nonface]);assert meta==mesh_meta(body);assert extra==others();assert np.isfinite(after).all()
 delta=np.linalg.norm(after-before,axis=1);changed=delta>0
 report={'revision':body.get('art014'),'beforeSha256':hashlib.sha256(a.before.read_bytes()).hexdigest(),'afterSha256':hashlib.sha256(a.after.read_bytes()).hexdigest(),'allNonFaceBodyVerticesExactlyUnchanged':True,'nonFaceBodyVertexCount':int(nonface.sum()),'otherMeshObjectsExactlyUnchanged':len(extra),'bodyTopologyUvsColorsMaterialAssignmentsUnchanged':True,'finitePositions':True,'changedVertices':int(changed.sum()),'maximumDisplacementMetres':float(delta.max()),'changedOriginalBounds':[before[changed].min(0).tolist(),before[changed].max(0).tolist()],'scope':'Static geometry integrity and protected regions, not an artistic likeness score or animation test'}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2));print('ART014_SCOPE_AUDIT_PASS',json.dumps(report),flush=True)
if __name__=='__main__':main()
