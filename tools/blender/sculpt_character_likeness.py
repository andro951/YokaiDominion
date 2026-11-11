"""Continuous silhouette sculpt and finished horn roots for Character01.
Preserves the base mesh's face, hand topology and authored skeletal weight data.
"""
from pathlib import Path
import sys, math
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import likeness_tailoring as t
f=t.f;b=f.b;a=f.a;p=t.p;r=t.r


def update_tree(obj):
 obj.data.update();f.TREE=BVHTree.FromPolygons([q.co for q in obj.data.vertices],[tuple(q.vertices) for q in obj.data.polygons])


def anatomy(path):
 obj,v,definition,weights=p.old_body(path)
 def warp(co):
  x,y,z=co;ax=abs(x)
  if z>1.69:
   jaw=f.ss(1.84,1.74,z)*f.ss(1.68,1.73,z)*f.ss(.035,-.055,y)
   x*=1-.13*jaw
   if ax>.10 and 1.80<z<1.92 and y>-.095:
    ear=f.ss(.105,.145,ax);x=x*(1-ear)+math.copysign(.108,x)*ear
  if z<.62:
   cx=math.copysign(.18,x);amount=.10*math.exp(-((z-.34)/.19)**4)
   x=cx+(x-cx)*(1+amount);y=(y+.015)*(1+amount)-.015
  return x,y,z
 for q in obj.data.vertices:q.co=warp(q.co)
 v=np.array([warp(q) for q in v])
 # A radial sculpt preserves the continuous, deformable source topology.
 for q in obj.data.vertices:
  x,y,z=q.co;s=1 if x>=0 else -1
  if 1.14<z<1.72 and y<-.04 and abs(x)<.44:
   old=Vector((s*.175,-.095,1.385));radii=Vector((.215,.300,.255))
   direction=Vector(((x-old.x)/radii.x,(y-old.y)/radii.y,(z-old.z)/radii.z))
   if direction.length>.01:
    direction.normalize()
    target=Vector((s*.182+direction.x*.214,-.110+direction.y*.315,1.442+direction.z*.225))
    alpha=f.ss(-.040,-.165,y)*f.ss(1.14,1.24,z)*(1-f.ss(1.64,1.72,z))*(1-f.ss(.36,.44,abs(x)))*(.25+.75*f.ss(.006,.040,abs(x)))
    q.co=q.co.lerp(target,alpha)
 g=obj.vertex_groups.new(name='TemporaryAttachmentBlend')
 for q in obj.data.vertices:
  x,y,z=q.co
  w=f.ss(-.27,-.12,y)*(1-f.ss(-.055,.015,y))*f.ss(1.17,1.28,z)*(1-f.ss(1.65,1.72,z))*(1-f.ss(.38,.44,abs(x)))
  if w>.001:g.add([q.index],w,'REPLACE')
 sm=obj.modifiers.new('ContinuousPectoralAttachment','SMOOTH');sm.factor=.45;sm.iterations=14;sm.vertex_group=g.name;f.apply(obj,sm);obj.vertex_groups.remove(obj.vertex_groups['TemporaryAttachmentBlend'])
 for face in obj.data.polygons:face.use_smooth=True
 for side,s in [('L',1),('R',-1)]:
  bone=definition['bones']['breast.'+side]
  for name,position in [(bone['head'],(s*.188,-.10,1.50)),(bone['tail'],(s*.188,-.36,1.45))]:
   ids=definition['joints'][name];mean=v[ids].mean(0);v[ids]+=np.array(position)-mean
 f.BODY=obj;update_tree(obj);return obj,v,definition,weights
f.make_anatomy=anatomy


def horns_tail():
 tail=f.make_horns_tail_baseline()
 for o in list(f.PARTS):
  if o.name.startswith('Horn.'):
   f.PARTS.remove(o);bpy.data.objects.remove(o,do_unlink=True)
 for s in [-1,1]:
  points=[(s*.072,-.153,1.907),(s*.084,-.174,1.936),(s*.111,-.153,1.990),(s*.132,-.109,2.063),(s*.123,-.060,2.123),(s*.097,-.022,2.169)]
  f.sweep('Horn.'+str(s),points,[.002,.035,.045,.032,.016,.0001],[.002,.025,.034,.028,.014,.0001],material='Horn',sides=36,steps=15,grooves=.02)
 b.MATS['Horn'].node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.55
 return tail
f.make_horns_tail_baseline=f.make_horns_tail;f.make_horns_tail=horns_tail


if __name__=='__main__':f.main()
