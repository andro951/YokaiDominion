"""Face-only Art014 on the immutable Art013 master; no generated-image proxy.
Shape lower face and cheeks, preserving everything outside the facial selection.
"""
from pathlib import Path
import argparse,hashlib,json,sys
import bpy
import numpy as np
REVISION='014-face-4'

def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def positions(o):
 a=np.empty(len(o.data.vertices)*3,dtype=np.float64);o.data.vertices.foreach_get('co',a);return a.reshape(-1,3)
def write(o,p):
 assert np.isfinite(p).all();o.data.vertices.foreach_set('co',p.ravel());o.data.update()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def deform(p):
 x,y,z=p.T;ax=np.abs(x);q=p.copy()
 gate=smooth(1.685,1.710,z)*(1-smooth(1.822,1.840,z))*(1-smooth(-.080,-.025,y))*(1-smooth(.086,.113,ax))
 # Preserve the lips, nostrils and nose itself, not just their separate details.
 mouth=(1-smooth(.027,.040,ax))*np.exp(-((z-1.749)/.013)**4)
 nose=(1-smooth(.024,.039,ax))*smooth(1.755,1.770,z)
 feature=np.maximum(mouth,nose);g=gate*(1-feature)
 jaw=np.exp(-((z-1.728)/.027)**2)*smooth(.012,.051,ax)
 q[:,0]-=np.sign(x)*.0035*jaw*g
 chin=np.exp(-((z-1.718)/.020)**2)*(1-smooth(.038,.065,ax))
 q[:,0]-=x*.14*chin*g
 q[:,1]+=.0012*chin*g
 q[:,2]+=(.002+.006*smooth(.008,.035,ax))*chin*g
 # Remove the high lateral shelf and refill the cut-in buccal plane gently.
 shelf=np.exp(-((ax-.075)/.024)**2-((z-1.801)/.024)**2)
 q[:,0]-=np.sign(x)*.0055*shelf*g
 hollow=np.exp(-((ax-.054)/.025)**2-((z-1.772)/.024)**2)
 q[:,1]-=.0040*hollow*g
 q[:,0]+=np.sign(x)*.0012*hollow*g
 q[:,1]+=.0010*shelf*g
 groove=np.exp(-(x/.032)**4-((z-1.731)/.009)**2)
 q[:,1]-=.0020*groove*g
 medial=np.exp(-((ax-.045)/.028)**2-((z-1.796)/.026)**2)
 q[:,1]-=.0025*medial*g
 return q,g

def apply():
 body=bpy.data.objects['Body'];assert not body.get('art014'),'Already edited'
 p=positions(body);q,g=deform(p)
 # Fair only the cheek/jaw planes, with a feathered zero mask at the features.
 x,y,z=p.T;ax=np.abs(x)
 weight=g*np.maximum(np.exp(-((ax-.059)/.031)**2-((z-1.784)/.029)**2),.18*np.exp(-((z-1.722)/.025)**2))
 edges=np.empty(len(body.data.edges)*2,dtype=np.int32);body.data.edges.foreach_get('vertices',edges);edges=edges.reshape(-1,2)
 subset=np.flatnonzero((weight>1e-8)|(g>0));look=np.full(len(p),-1,dtype=np.int32);look[subset]=np.arange(len(subset))
 keep=(look[edges[:,0]]>=0)&(look[edges[:,1]]>=0);e=look[edges[keep]]
 a=np.r_[e[:,0],e[:,1]];b=np.r_[e[:,1],e[:,0]];count=np.maximum(np.bincount(a,minlength=len(subset)),1)
 local=q[subset].copy();w=weight[subset]
 for _ in range(280):
  mean=np.column_stack([np.bincount(a,weights=local[b,k],minlength=len(subset))/count for k in range(3)])
  local+=.36*w[:,None]*(mean-local)
 q[subset]=local
 protected=g==0;assert np.array_equal(p[protected],q[protected])
 previous=body.data.attributes.new('art014_previous_position','FLOAT_VECTOR','POINT');previous.data.foreach_set('vector',p.ravel())
 write(body,q);body['art014']=REVISION;body['art014_scope']='Jaw and cheeks only; body, garment, eyes and separate accessories unchanged'
 bpy.context.scene['art_checkpoint']=REVISION
 return {'revision':REVISION,'bodyVertices':len(p),'changedVertices':int(np.count_nonzero(np.any(p!=q,axis=1))),'protectedVertices':int(protected.sum()),'protectedExactlyUnchanged':True,'maxDisplacementMetres':float(np.linalg.norm(q-p,axis=1).max()),'otherObjectsUnchanged':True,'rigUpdated':False,'runtimePhysicsUpdated':False}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);a=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);a.out.mkdir(parents=True,exist_ok=True)
 bpy.ops.wm.open_mainfile(filepath=str(a.source.resolve()));report=apply();bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0
 f=a.out.resolve()/'Character01_Art014.blend';bpy.ops.wm.save_as_mainfile(filepath=str(f),compress=True);bpy.ops.wm.open_mainfile(filepath=str(f));assert bpy.data.objects['Body']['art014']==REVISION
 report.update(sourceSha256=sha(a.source),savedBlendReopened=True,files={f.name:{'bytes':f.stat().st_size,'sha256':sha(f)}})
 (a.out/'manifest.json').write_text(json.dumps(report,indent=2));print('ART014_SAVED_REOPENED',flush=True)
if __name__=='__main__':main()
