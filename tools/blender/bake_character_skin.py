"""Portable UV skin atlas. Cosmetic marks are texture pigment, never floating decals."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import bpy, numpy as np

def srgb(a):
    return np.where(a<=.0031308,12.92*a,1.055*np.maximum(a,0)**(1/2.4)-.055)

def smooth(lo,hi,a):
    t=np.clip((a-lo)/(hi-lo),0,1)
    return t*t*(3-2*t)

def rasterize_rest_uv(body, size):
    """Barycentric rest-position/pigment transfer, without ray-tracing scene lighting."""
    mesh=body.data
    if not mesh.uv_layers.active:raise ValueError('Body needs its authored UV map')
    attr=mesh.color_attributes.get('SkinPalette')
    if attr is None or attr.domain!='POINT':raise ValueError('Expected point-domain SkinPalette')
    mesh.calc_loop_triangles()
    coords=np.empty(len(mesh.vertices)*3,np.float32);mesh.vertices.foreach_get('co',coords);coords=coords.reshape(-1,3)
    pigments=np.empty(len(attr.data)*4,np.float32);attr.data.foreach_get('color',pigments);pigments=pigments.reshape(-1,4)[:,:3]
    uvs=np.empty(len(mesh.loops)*2,np.float32);mesh.uv_layers.active.data.foreach_get('uv',uvs);uvs=uvs.reshape(-1,2)
    colors=np.empty((size,size,3),np.float32);colors[:]=np.median(pigments,axis=0)
    positions=np.zeros((size,size,3),np.float32);valid=np.zeros((size,size),bool)
    for tri in mesh.loop_triangles:
        ids=np.array(tri.vertices,dtype=np.int32);uv=uvs[list(tri.loops)].copy();px=uv*size-.5
        lo=np.maximum(0,np.ceil(px.min(0)).astype(int));hi=np.minimum(size-1,np.floor(px.max(0)).astype(int))
        if np.any(lo>hi):continue
        a,b,c=px;ab=b-a;ac=c-a;det=ab[0]*ac[1]-ab[1]*ac[0]
        if abs(det)<1e-12:continue
        xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1,dtype=np.float32),np.arange(lo[1],hi[1]+1,dtype=np.float32))
        dx=xx-a[0];dy=yy-a[1];w1=(dx*ac[1]-dy*ac[0])/det;w2=(ab[0]*dy-ab[1]*dx)/det;w0=1-w1-w2
        inside=(w0>=-1e-5)&(w1>=-1e-5)&(w2>=-1e-5)
        if not np.any(inside):continue
        sl=(slice(lo[1],hi[1]+1),slice(lo[0],hi[0]+1));bary=np.stack((w0[inside],w1[inside],w2[inside]),axis=1)
        colors[sl][inside]=bary@pigments[ids];positions[sl][inside]=bary@coords[ids];valid[sl][inside]=True
    if np.count_nonzero(valid)<size*size*.10:raise ValueError('UV raster coverage unexpectedly low')
    print('UV_ATLAS_RASTERIZED',int(valid.sum()),'triangles',len(mesh.loop_triangles),flush=True)
    return colors,positions,valid

def dilate_atlas(colors,valid,iterations=10):
    """Filtered-texture seam padding with bounded scratch memory."""
    known=valid.copy()
    for _ in range(iterations):
        changed=False
        for target,source in [
            ((slice(1,None),slice(None)),(slice(None,-1),slice(None))),
            ((slice(None,-1),slice(None)),(slice(1,None),slice(None))),
            ((slice(None),slice(1,None)),(slice(None),slice(None,-1))),
            ((slice(None),slice(None,-1)),(slice(None),slice(1,None)))]:
            fill=(~known[target])&known[source]
            if np.any(fill):
                colors[target][fill]=colors[source][fill];known[target][fill]=True;changed=True
        if not changed:break

def bake_skin(body,out:Path,materials,eye_fields,png_writer,size=4096):
    out.mkdir(parents=True,exist_ok=True);old_material=body.data.materials[0]
    colors,positions,valid=rasterize_rest_uv(body,size);x,y,z=positions[:,:,0],positions[:,:,1],positions[:,:,2]
    pigment=np.array(materials['Markings'].diffuse_color[:3],np.float32);ink=np.array(materials['Ink'].diffuse_color[:3],np.float32)
    painted=np.zeros((size,size),np.float32)
    leaves=[
        ([(.290,1.622),(.332,1.604),(.351,1.574)],.013),
        ([(.346,1.638),(.376,1.614),(.377,1.584)],.011),
        ([(.315,1.581),(.344,1.553),(.349,1.525)],.010),
        ([(.368,1.525),(.384,1.482),(.378,1.450)],.009),
        ([(.447,1.299),(.479,1.270),(.488,1.243)],.012),
        ([(.468,1.246),(.493,1.216),(.497,1.189)],.010),
        ([(.501,1.193),(.520,1.167),(.519,1.149)],.007)]
    for sign in [-1,1]:
        for pts,w in leaves:
            pts=np.array(pts,np.float32);pts[:,0]*=sign
            bbox=(x>pts[:,0].min()-w*1.5)&(x<pts[:,0].max()+w*1.5)&(z>pts[:,1].min()-w*1.5)&(z<pts[:,1].max()+w*1.5)
            mask=valid&bbox&(y>-.175)&(y<.015);rows,cols=np.where(mask)
            if not len(rows):continue
            p=np.column_stack([x[mask],z[mask]]);dist=np.full(len(p),1.,np.float32);ts=np.linspace(0,1,40,dtype=np.float32)
            curve=(1-ts[:,None])**2*pts[0]+2*ts[:,None]*(1-ts[:,None])*pts[1]+ts[:,None]**2*pts[2]
            for j in range(len(curve)-1):
                ab=curve[j+1]-curve[j];t=np.clip(((p-curve[j])*ab).sum(1)/max(1e-12,float(ab@ab)),0,1)
                at=(j+t)/(len(curve)-1)
                # float32 sin(pi) may be slightly negative; fractional powers must be guarded.
                width=w*np.maximum(0,np.sin(np.pi*at))**.85
                distance=np.linalg.norm(p-(curve[j]+t[:,None]*ab),axis=1)-width;dist=np.minimum(dist,distance)
            alpha=(1-smooth(-.00035,.00035,dist))*smooth(-.175,-.14,y[mask])*(1-smooth(-.015,.015,y[mask]))
            painted[rows,cols]=np.maximum(painted[rows,cols],alpha)
    colors[:,:,:3]=colors[:,:,:3]*(1-painted[:,:,None])+pigment*painted[:,:,None]
    eyeliner=np.zeros((size,size),np.float32)
    for item in eye_fields:
        c=np.array(item['center']);sign=item['sign'];xs=np.array(item['xs']);upper=np.array(item['upper']);lower=np.array(item['lower'])
        dx=(x-c[0])*sign;mask=valid&(y<-.12)&(z>c[2]-.035)&(z<c[2]+.035)&(dx>xs[0])&(dx<xs[-1])
        if not np.any(mask):continue
        xx=dx[mask];zz=z[mask];top=np.interp(xx,xs,upper);bottom=np.interp(xx,xs,lower)
        u=(xx-xs[0])/(xs[-1]-xs[0]);width=.0010+.0037*u;dz=zz-top
        a1=smooth(-.0004,.0001,dz)*(1-smooth(width-.0004,width+.0006,dz));dz=bottom-zz
        a2=smooth(-.0003,.0001,dz)*(1-smooth(.00035,.0010,dz))*smooth(.15,.75,u)
        eyeliner[mask]=np.maximum(eyeliner[mask],np.maximum(a1,a2)*.96)
    colors[:,:,:3]=colors[:,:,:3]*(1-eyeliner[:,:,None])+ink*eyeliner[:,:,None]
    noise=np.sin(x*911+np.sin(y*517))*np.sin(z*1207+np.sin(x*313));variation=1+.0028*noise*(1-painted)*(1-eyeliner)
    colors[:,:,:3]*=variation[:,:,None]
    color_path=out/'Character01_Skin_BaseColor.png'
    if not np.isfinite(colors).all():raise ValueError('Nonfinite atlas pigmentation')
    dilate_atlas(colors,valid,12);png_writer(color_path,np.flipud(srgb(np.clip(colors,0,1))))
    rough=np.full((size,size),.57,np.float32)+noise*.012
    lips=valid&(np.abs(x)<.05)&(z>1.735)&(z<1.765)&(y<-.12);rough[lips]=.44;rough[eyeliner>.25]=.67
    if not np.isfinite(rough).all():raise ValueError('Nonfinite roughness atlas')
    rough_path=out/'Character01_Skin_Roughness.png';png_writer(rough_path,np.flipud(np.stack([rough,rough,rough],axis=2)))
    final=old_material.copy();final.name='Character01_Skin_PBR';shader=final.node_tree.nodes.get('Principled BSDF')
    for link in list(shader.inputs['Base Color'].links):final.node_tree.links.remove(link)
    tex=final.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(color_path),check_existing=False)
    tex.image.colorspace_settings.name='sRGB';tex.label='4096px authored skin, cosmetic liner and flush markings'
    final.node_tree.links.new(tex.outputs['Color'],shader.inputs['Base Color']);shader.inputs['Base Color'].default_value=(1,1,1,1)
    roughnode=final.node_tree.nodes.new('ShaderNodeTexImage');roughnode.image=bpy.data.images.load(str(rough_path),check_existing=False)
    roughnode.image.colorspace_settings.name='Non-Color';final.node_tree.links.new(roughnode.outputs['Color'],shader.inputs['Roughness'])
    shader.inputs['Subsurface Weight'].default_value=.065;shader.inputs['Specular IOR Level'].default_value=.24
    body.data.materials[0]=final
    # Prevent an imported COLOR_0 stream from multiplying the baked atlas twice.
    for attr in list(body.data.color_attributes):body.data.color_attributes.remove(attr)
    for image in [tex.image,roughnode.image]:image.pack()
    report={'resolution':[size,size],'method':'barycentric rest-space UV rasterization','lightingBaked':False,'cosmeticsInSkinTexture':True,
            'markedTexels':int(np.count_nonzero(painted>.5)),'eyelinerTexels':int(np.count_nonzero(eyeliner>.5)),'validTexels':int(np.count_nonzero(valid)),
            'textures':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [color_path,rough_path]}}
    (out/'skin-texture-manifest.json').write_text(json.dumps(report,indent=2));print('YOKAI_SKIN_ATLAS_BAKED',json.dumps(report))
    del positions,colors,painted,eyeliner,rough,noise,variation,x,y,z,valid
    import gc
    gc.collect()
    return report
