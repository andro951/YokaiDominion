"""Human-scale anatomical surface detail and cool fantasy skin variation."""
import bpy
import numpy as np

def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def gauss(x,c,s):return np.exp(-((x-c)/s)**2)
def linear(c):
 c=np.asarray(c);return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)

def apply(body):
 n=len(body.data.vertices);p=np.empty(n*3);q=np.empty(n*3)
 body.data.attributes['source_position'].data.foreach_get('vector',p);body.data.vertices.foreach_get('co',q);p=p.reshape(-1,3);q=q.reshape(-1,3)
 x,y,z=p.T;ax=abs(x);front=1-smooth(-.065,-.018,y)
 # Broad muscle/tendon transitions; no extra breast or glute volume.
 for side in (-1,1):
  quad=gauss(x,side*.117,.044)*gauss(z,.646,.130)*front
  q[:,1]-=.0045*quad
  outer=gauss(x,side*.147,.036)*gauss(z,.668,.122)*front
  q[:,1]-=.0030*outer
  scm_x=side*(.020+.50*(z-1.35))
  scm=gauss(x,scm_x,.010)*gauss(z,1.388,.048)*(1-smooth(-.025,.012,y))
  q[:,1]-=.0018*scm
 body.data.vertices.foreach_set('co',q.ravel());body.data.update()
 ca=body.data.color_attributes.get('Complexion')
 if ca:
  c=np.empty(n*4);ca.data.foreach_get('color',c);c=c.reshape(-1,4)
  # Slight plum undertones on vascular/thin-skin areas retain the slate identity.
  facefront=1-smooth(-.065,-.025,y)
  cheek=gauss(ax,.045,.026)*gauss(z,1.502,.026)*facefront
  nose=gauss(x,0,.023)*gauss(z,1.493,.015)*(1-smooth(-.080,-.055,y))
  ear=smooth(.069,.088,ax)*gauss(z,1.52,.041)*gauss(y,-.045,.050)
  hand=gauss(ax,.350,.045)*gauss(z,.856,.051)
  knee=gauss(z,.455,.039)*gauss(ax,.112,.068)*front
  elbow=gauss(z,1.07,.035)*gauss(ax,.244,.040)
  warmth=np.clip(.18*cheek+.19*nose+.12*ear+.07*hand+.07*knee+.07*elbow,0,.30)
  tint=linear((.47,.405,.53));c[:,:3]=c[:,:3]*(1-warmth[:,None])+tint*warmth[:,None]
  # Very low-amplitude mottling; not baked directional light or muscle shadows.
  micro=.008*np.sin(x*319+z*113)*np.sin(y*227-z*149)+.004*np.cos(x*71+y*93+z*131)
  c[:,:3]*=1+micro[:,None];ca.data.foreach_set('color',c.ravel())
 rough=.51+.065*knee+.055*elbow-.055*nose-.025*cheek if ca else np.full(n,.51)
 rough+=.012*np.sin(x*493+z*349)*np.sin(y*457-z*179)
 rough=np.clip(rough,.39,.65)
 attr=body.data.attributes.get('AnatomicalRoughness') or body.data.attributes.new('AnatomicalRoughness','FLOAT','POINT');attr.data.foreach_set('value',rough)
 mat=bpy.data.materials.get('Skin | cool slate')
 if mat and mat.use_nodes:
  nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes.get('Principled BSDF')
  a=nodes.new('ShaderNodeAttribute');a.attribute_name='AnatomicalRoughness';links.new(a.outputs['Fac'],bs.inputs['Roughness'])
  bs.inputs['Subsurface Weight'].default_value=.065;bs.inputs['Subsurface Scale'].default_value=.0013
  pore=nodes.get('Art008 skin microstructure')
  if pore:pore.inputs['Scale'].default_value=1400
  bump=nodes.get('Art008 subtle pores')
  if bump:bump.inputs['Strength'].default_value=.14;bump.inputs['Distance'].default_value=.000075
 body['skin008']='Cool slate identity with subtle anatomical complexion and roughness variation; geometry retains muscular support and unsupported tissue form'
