"""Portable body geometry with explicit UV integrity checks.
UNSUBDIV was rejected: its low mesh had UV area 16.63 in one tile vs 0.636
on the source. Collapse with UV/material/seam delimiters measured 0.629.
"""
import time
import bpy
import numpy as np

def select_only(o):
 bpy.ops.object.select_all(action='DESELECT');o.hide_set(False);o.hide_viewport=False;o.select_set(True);bpy.context.view_layer.objects.active=o

def uv_area(mesh):
 mesh.calc_loop_triangles();uv=mesh.uv_layers.active
 p=np.empty(len(uv.data)*2);uv.data.foreach_get('uv',p);p=p.reshape(-1,2)
 t=np.empty(len(mesh.loop_triangles)*3,dtype=np.int32);mesh.loop_triangles.foreach_get('loops',t);t=t.reshape(-1,3)
 q=p[t];u=q[:,1]-q[:,0];v=q[:,2]-q[:,0];area=np.abs(u[:,0]*v[:,1]-u[:,1]*v[:,0])*.5
 return {'sum':float(area.sum()),'maxTriangle':float(area.max()),'minUV':p.min(0).tolist(),'maxUV':p.max(0).tolist(),'triangles':len(t)}

def prepare_body(body):
 select_only(body);uv=body.data.uv_layers.active
 original=np.empty(len(uv.data)*2);uv.data.foreach_get('uv',original);original=original.reshape(-1,2)
 shifted=original-original.min(0);shifted/=max(float(shifted.max())+1e-6,1.)
 uv.data.foreach_set('uv',shifted.ravel());body.data.update();print('PACK_ATLAS_BEGIN',time.time(),flush=True)
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.select_all(action='SELECT')
 bpy.ops.uv.pack_islands(udim_source='CLOSEST_UDIM',shape_method='AABB',rotate=False,scale=True,margin=.004)
 bpy.ops.object.mode_set(mode='OBJECT');body.data.update()
 source_area=uv_area(body.data)
 if min(source_area['minUV'])<-.0001 or max(source_area['maxUV'])>1.0001:raise RuntimeError('UVs outside portable atlas')
 if not 0<source_area['sum']<1.01:raise RuntimeError('Source atlas overlaps or has no usable area')
 print('PACK_ATLAS_END',time.time(),flush=True)
 high=body;high.name='Body_SculptSource';low=high.copy();low.data=high.data.copy();low.name='Body';bpy.context.collection.objects.link(low);select_only(low)
 dec=low.modifiers.new('UV-preserving portable body','DECIMATE');dec.decimate_type='COLLAPSE';dec.ratio=.40;dec.use_collapse_triangulate=True;dec.delimit={'UV','SEAM','MATERIAL'}
 bpy.ops.object.modifier_apply(modifier=dec.name)
 measured=uv_area(low.data);relative=abs(measured['sum']/source_area['sum']-1)
 fallback=False
 if relative>.03 or measured['maxTriangle']>.002:
  # Preserve visual correctness over an arbitrary triangle budget.
  bad=low.data;low.data=high.data.copy();bpy.data.meshes.remove(bad)
  measured=uv_area(low.data);fallback=True
 for f in low.data.polygons:f.use_smooth=True
 report={'sourceUvMin':original.min(0).tolist(),'sourceUvMax':original.max(0).tolist(),'sourceVertices':len(high.data.vertices),'portableVertices':len(low.data.vertices),'sourceAtlas':source_area,'portableAtlas':measured,'keptFullResolutionFallback':fallback,'method':'COLLAPSE with UV, seam and material delimiters'}
 print('PORTABLE_UV_VALIDATED',report,flush=True)
 return low,high,report
