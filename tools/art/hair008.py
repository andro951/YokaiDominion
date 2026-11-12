"""Editable strand-opacity ribbons on the existing groom. No external texture dependency."""
from __future__ import annotations
import bpy
import numpy as np
from pathlib import Path
import tempfile

def coords(o):
 a=np.empty(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',a);return a.reshape(-1,3)
def linear(c):
 c=np.asarray(c);return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)

def texture():
 w,h=512,2048;v=np.linspace(0,1,h);rgba=np.zeros((h,w,4),dtype=np.float32);rng=np.random.default_rng(8008);yy=np.arange(h)
 for i in range(142):
  center=(i+.35+rng.uniform(-.25,.25))*w/142
  phase=rng.uniform(0,6.28);end=rng.uniform(.88,1.07)
  xx=center+1.7*np.sin(phase+v*5.3)+.75*np.sin(phase*2-v*10)
  fade=np.clip((end-v)/.025,0,1)*np.clip(v/.006,0,1)
  shade=rng.uniform(.59,.91);col=linear((shade*.97,shade*.99,min(1,shade*1.035)))
  for off in range(-2,3):
   ix=np.round(xx).astype(int)+off;ok=(ix>=0)&(ix<w)
   alpha=np.exp(-((ix-xx)/rng.uniform(.72,1.04))**2)*fade*rng.uniform(.76,1)
   take=ok & (alpha>rgba[yy,np.clip(ix,0,w-1),3])
   rgba[yy[take],ix[take],:3]=col;rgba[yy[take],ix[take],3]=alpha[take]
 image=bpy.data.images.new('Hair008_FibreOpacity',width=w,height=h,alpha=True);image.pixels.foreach_set(rgba.ravel())
 image.filepath_raw=str(Path(tempfile.mkdtemp(prefix='hair008_'))/'Hair008_FibreOpacity.png');image.file_format='PNG';image.save();image.pack();image.filepath='//textures/Hair008_FibreOpacity.png'
 return image

def material(image):
 m=bpy.data.materials.new('Hair008 | strand-opacity ivory');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF')
 tex=n.new('ShaderNodeTexImage');tex.image=image;tex.extension='CLIP';l.new(tex.outputs['Color'],bs.inputs['Base Color']);l.new(tex.outputs['Alpha'],bs.inputs['Alpha'])
 uv=n.new('ShaderNodeUVMap');uv.uv_map='StrandUV';l.new(uv.outputs['UV'],tex.inputs['Vector'])
 tan=n.new('ShaderNodeTangent');tan.direction_type='UV_MAP';tan.uv_map='StrandUV';l.new(tan.outputs[0],bs.inputs['Tangent'])
 bs.inputs['Roughness'].default_value=.44;bs.inputs['Specular IOR Level'].default_value=.30;bs.inputs['Anisotropic'].default_value=.65
 m.surface_render_method='DITHERED';m.use_backface_culling=False;m['portable_pbr_ready']=True;m['gltf_alpha_cutoff']=.30
 return m

def apply(body):
 mat=material(texture());collection=bpy.data.collections['03_HAIR'];count=0
 originals=[o for o in bpy.data.objects if o.type=='MESH' and not o.hide_render and o.name.startswith(('Back wave','Side S wave','Face wave','Crown sweep','Art008 inner flowing lock'))]
 for o in originals:
  p=coords(o)
  if len(p)==1218:rings,sides=76,16
  elif len(p)==890:rings,sides=74,12
  else:continue
  a=p[:rings*sides].reshape(rings,sides,3);centers=a.mean(1)
  axis=(a[:,0]-a[:,sides//2])*.5;depth=(a[:,sides//4]-a[:,3*sides//4])*.5
  for side in (-1,1):
   # Follow the outer face of each lock; the fine alpha ends extend its silhouette.
   vv=[];ff=[]
   for i,c in enumerate(centers):
    for u in (-1,1):vv.append(c+side*depth[i]*1.04+u*axis[i]*1.045)
    if i:ff.append((2*i-2,2*i-1,2*i+1,2*i))
   data=bpy.data.meshes.new('HairFibreRibbon');data.from_pydata(vv,[],ff);data.update();obj=bpy.data.objects.new('Hair008 fibres | '+o.name+(' front' if side<0 else ' back'),data);collection.objects.link(obj);data.materials.append(mat)
   uv=data.uv_layers.new(name='StrandUV')
   for f in data.polygons:
    f.use_smooth=True
    for li in f.loop_indices:
     j=data.loops[li].vertex_index;uv.data[li].uv=(j%2,(j//2)/(rings-1))
   obj['groom_source']=o.name;count+=1
  # Retain solid interior for depth and robustness, but soften its card-like edge.
  a[:]=centers[:,None,:]+(a-centers[:,None,:])*.94
  o.data.vertices.foreach_set('co',p.ravel());o.data.update()
 body['hair008_ribbons']=count;body['hair008_texture']='Packed RGBA strand opacity, editable ribbons and retained inner groom'
