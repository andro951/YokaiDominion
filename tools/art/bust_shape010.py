"""Smooth 3-D anatomical landmark deformation; no cloth-driven shaping."""
import numpy as np

def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)

def deform(p):
 controls=[];delta=[]
 # Existing surface locations and sculpt strokes. Lowest attachment and abdomen
 # are anchored separately; the garment does not affect body vertex positions.
 strokes=[
  ((.126,-.240,1.363),(.023,-.105,.029)),
  ((.111,-.198,1.444),(.016,-.068,.022)),
  ((.120,-.222,1.412),(.022,-.088,.028)),
  ((.134,-.213,1.330),(.017,-.065,-.002)),
  ((.177,-.177,1.376),(.038,-.057,.009)),
  ((.066,-.208,1.382),(-.003,-.058,.014)),
  ((.177,-.143,1.438),(.023,-.040,.009)),
  ((.087,-.186,1.331),(.007,-.039,-.002)),
 ]
 def closest(point):
  point=np.asarray(point);return p[np.argmin(np.sum((p-point)**2,axis=1))]
 for side in (-1.,1.):
  for co,d in strokes:
   controls.append(closest((side*co[0],co[1],co[2])));delta.append((side*d[0],d[1],d[2]))
  for z in (1.255,1.285,1.305,1.535,1.565,1.590):
   for x in (.025,.065,.105,.145,.185,.225):
    controls.append(closest((side*x,-.125,z)));delta.append((0.,0.,0.))
  for z in (1.33,1.37,1.42,1.47,1.51):
   for x in (.016,.235):
    controls.append(closest((side*x,-.12,z)));delta.append((0.,0.,0.))
  for z in (1.34,1.40,1.46,1.52):
   for x in (.06,.13,.20):
    controls.append(closest((side*x,.015,z)));delta.append((0.,0.,0.))
 c=np.array(controls);d=np.array(delta)
 _,keep=np.unique(np.round(c,7),axis=0,return_index=True);c=c[keep];d=d[keep]
 radius=.076
 k=np.exp(-np.sum((c[:,None]-c[None,:])**2,axis=2)/radius**2)
 weights=np.linalg.solve(k+np.eye(len(c))*.0025,d)
 x,y,z=p.T;ax=np.abs(x)
 gate=smooth(1.255,1.30,z)*(1-smooth(1.535,1.590,z))*smooth(.008,.032,ax)*(1-smooth(.215,.26,ax))*(1-smooth(-.055,.005,y))
 q=p.copy();ids=np.flatnonzero(gate>0)
 for start in range(0,len(ids),4096):
  ix=ids[start:start+4096];kernel=np.exp(-np.sum((p[ix,None]-c[None,:])**2,axis=2)/radius**2)
  q[ix]+=(kernel@weights)*gate[ix,None]
 assert np.isfinite(q).all()
 return q
