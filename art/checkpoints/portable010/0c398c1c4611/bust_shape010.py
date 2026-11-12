"""Anatomical contour remap with separately anchored chest and abdomen.
The garment is fitted afterward and never lifts or centers the body geometry.
"""
import numpy as np
REVISION='010-bust-trapezius-10'

def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)

def deform(p):
 x,y,z=p.T;ax=np.abs(x);q=p.copy()
 d=np.column_stack([(ax-.120)/.087,(y+.166)/.078,(z-1.379)/.093])
 r=np.linalg.norm(d,axis=1);n=d/np.maximum(r[:,None],1e-8)
 wall=np.interp(z,[1.28,1.32,1.37,1.40,1.44,1.48,1.52,1.56,1.60],[-.166,-.168,-.164,-.158,-.149,-.138,-.124,-.101,-.08])+.8*ax*ax
 projection=np.maximum(0,wall-y)
 free=smooth(.003,.027,projection)*smooth(.015,.040,ax)*(1-smooth(.190,.235,ax))*smooth(1.295,1.325,z)*(1-smooth(1.485,1.555,z))
 target=p.copy()
 target[:,0]=np.sign(x)*(.142+n[:,0]*.106*(1-.22*np.maximum(n[:,2],0)))
 target[:,1]=-.171+n[:,1]*.165*(1-.50*np.maximum(n[:,2],0))
 target[:,2]=1.391+n[:,2]*np.where(n[:,2]>=0,.123,.112)
 q+=(target-p)*free[:,None]
 assert np.isfinite(q).all()
 return q

def fair_surface(q,p,edges):
 """Restricted alternating fairing preserves unrelated body geometry."""
 x,y,z=p.T;ax=np.abs(x)
 w=smooth(1.303,1.34,z)*(1-smooth(1.50,1.555,z))*smooth(.023,.047,ax)*(1-smooth(.19,.225,ax))*(1-smooth(-.115,-.075,y))
 a=np.r_[edges[:,0],edges[:,1]];b=np.r_[edges[:,1],edges[:,0]];count=np.maximum(np.bincount(a,minlength=len(q)),1)
 for _ in range(55):
  for factor in (.48,-.49):
   avg=np.column_stack([np.bincount(a,weights=q[b,k],minlength=len(q))/count for k in range(3)])
   q+=factor*w[:,None]*(avg-q)
 return q
