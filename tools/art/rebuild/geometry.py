from __future__ import annotations
import bpy, math
import numpy as np
from mathutils import Vector


def mesh(name, vertices, faces, mat=None, uvs=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    if mat:
        data.materials.append(mat)
    for poly in data.polygons:
        poly.use_smooth = True
    if uvs is not None:
        uv = data.uv_layers.new(name='UVMap')
        for loop in data.loops:
            uv.data[loop.index].uv = uvs[loop.vertex_index]
    return obj


def catmull(points, n=80):
    p = np.array(points, dtype=float)
    t = np.linspace(0, len(p)-1, n)
    i = np.clip(t.astype(int), 0, len(p)-2)
    u = (t-i)[:, None]
    a, b, c, d = p[np.maximum(i-1, 0)], p[i], p[i+1], p[np.minimum(i+2, len(p)-1)]
    return .5*((2*b)+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u)


def tube(name, points, radii, mat, n=80, sides=16, flatten=1., ripple=0., cap=True):
    centers = catmull(points, n)
    t = np.linspace(0, 1, n)
    rad = np.interp(t, np.linspace(0, 1, len(radii)), radii)
    verts, uvs, faces = [], [], []
    last = None
    for j, c in enumerate(centers):
        tangent = centers[min(j+1, n-1)]-centers[max(j-1, 0)]
        tangent /= max(np.linalg.norm(tangent), 1e-12)
        if last is None:
            axis = np.array([1., 0, 0])
            if abs(tangent@axis) > .95:
                axis = np.array([0., 1, 0])
            u = axis-tangent*(axis@tangent)
            u /= np.linalg.norm(u)
        else:
            u = last-tangent*(last@tangent)
            u /= max(np.linalg.norm(u), 1e-12)
        v = np.cross(tangent, u)
        last = u
        for k in range(sides):
            th = 2*math.pi*k/sides
            radius = rad[j]*(1+ripple*math.sin(t[j]*math.pi*70))
            co = c+radius*(math.cos(th)*u+flatten*math.sin(th)*v)
            verts.append(co.tolist())
            uvs.append((k/sides, t[j]))
        if j:
            for k in range(sides):
                a = (j-1)*sides+k
                b = (j-1)*sides+(k+1)%sides
                faces.append((a, b, b+sides, a+sides))
    if cap:
        verts.extend([centers[0].tolist(), centers[-1].tolist()])
        uvs.extend([(.5, 0), (.5, 1)])
        for k in range(sides):
            faces.append((len(verts)-2, (k+1)%sides, k))
            a = (n-1)*sides
            faces.append((len(verts)-1, a+k, a+(k+1)%sides))
    return mesh(name, verts, faces, mat, uvs)


def ribbon(name, grid, mat, thickness=.0015, subdiv=1):
    arr = np.array(grid)
    n, m, _ = arr.shape
    verts = arr.reshape(-1, 3).tolist()
    faces = []
    uvs = [(i/(m-1), j/(n-1)) for j in range(n) for i in range(m)]
    for j in range(n-1):
        for i in range(m-1):
            a = j*m+i
            faces.append((a, a+1, a+1+m, a+m))
    obj = mesh(name, verts, faces, mat, uvs)
    if subdiv:
        mod = obj.modifiers.new('Silk surface', 'SUBSURF')
        mod.levels = subdiv
        mod.render_levels = subdiv
    if thickness:
        mod = obj.modifiers.new('Fabric thickness', 'SOLIDIFY')
        mod.thickness = thickness
        mod.offset = 0
    return obj


def strand(name, points, widths, mat, n=60, sides=12, depth=.3, phase=0):
    """Tapered hair lock using parallel transport through curved tips."""
    centers = catmull(points, n)
    t = np.linspace(0, 1, n)
    width = np.interp(t, np.linspace(0, 1, len(widths)), widths)
    verts, faces, uvs = [], [], []
    last = previous_tangent = None
    for j, c in enumerate(centers):
        tangent = centers[min(n-1, j+1)]-centers[max(0, j-1)]
        tangent /= max(np.linalg.norm(tangent), 1e-12)
        if last is None:
            lateral = np.array([1., 0, 0])
            if abs(lateral@tangent) > .9:
                lateral = np.array([0., 0, 1.])
            lateral -= tangent*(lateral@tangent)
            lateral /= np.linalg.norm(lateral)
        else:
            kvec = np.cross(previous_tangent, tangent)
            cosine = float(previous_tangent@tangent)
            lateral = last+np.cross(kvec,last)+np.cross(kvec,np.cross(kvec,last))/max(1+cosine,1e-8)
            lateral -= tangent*(lateral@tangent)
            lateral /= max(np.linalg.norm(lateral),1e-12)
        normal = np.cross(tangent,lateral)
        last, previous_tangent = lateral, tangent
        for k in range(sides):
            angle = 2*math.pi*k/sides
            ridge = 1+.035*math.cos(6*angle+phase)
            point = c+width[j]*ridge*(math.cos(angle)*lateral+depth*math.sin(angle)*normal)
            verts.append(point.tolist())
            uvs.append((k/sides,t[j]))
        if j:
            for k in range(sides):
                a = (j-1)*sides+k
                b = (j-1)*sides+(k+1)%sides
                faces.append((a,b,b+sides,a+sides))
    verts.extend([centers[0].tolist(),centers[-1].tolist()])
    uvs.extend([(.5,0),(.5,1)])
    for k in range(sides):
        faces.append((len(verts)-2,(k+1)%sides,k))
        a = (n-1)*sides
        faces.append((len(verts)-1,a+k,a+(k+1)%sides))
    return mesh(name,verts,faces,mat,uvs)
