"""Free-tissue sculpt relative to the chest wall; clothing never shapes the body."""
import numpy as np
REVISION='010-bust-trapezius-8'

def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)

def deform(p):
 """Expand projecting tissue while blending to the sternum and chest attachments."""
 x,y,z=p.T;ax=np.abs(x);q=p.copy()
 wall=np.interp(z,[1.28,1.32,1.37,1.40,1.44,1.48,1.52,1.56,1.60],[-.166,-.168,-.164,-.158,-.149,-.138,-.124,-.101,-.08])+.8*ax*ax
 projection=np.maximum(0,wall-y)
 free=smooth(.008,.038,projection)*smooth(.022,.045,ax)*(1-smooth(.192,.237,ax))*smooth(1.295,1.325,z)*(1-smooth(1.505,1.555,z))
 q[:,0]+=np.sign(x)*(.020+.45*(ax-.115))*free
 q[:,1]-=1.20*projection*free
 q[:,2]+=(.30*(z-1.395)-.005)*free
 assert np.isfinite(q).all()
 return q

def fair_surface(q,p,edges):
 """Local volume-conscious fairing removes stroke transitions, not body definition."""
 x,y,z=p.T;ax=np.abs(x)
 w=smooth(1.303,1.34,z)*(1-smooth(1.50,1.555,z))*smooth(.023,.047,ax)*(1-smooth(.19,.225,ax))*(1-smooth(-.115,-.075,y))
 a=np.r_[edges[:,0],edges[:,1]];b=np.r_[edges[:,1],edges[:,0]];count=np.maximum(np.bincount(a,minlength=len(q)),1)
 for _ in range(55):
  for factor in (.48,-.49):
   avg=np.column_stack([np.bincount(a,weights=q[b,k],minlength=len(q))/count for k in range(3)])
   q+=factor*w[:,None]*(avg-q)
 return q
