"""Audit a saved Art011 master without changing geometry.
Run: blender -b Character01_Art011.blend --python audit011.py -- OUTPUT_DIR
This is a sampled static surface audit, not dynamic collision certification.
"""
from pathlib import Path
import json
import sys
import bpy
import numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector


def main():
    if '--' not in sys.argv or len(sys.argv) <= sys.argv.index('--') + 1:
        raise ValueError('An output directory after -- is required')
    out = Path(sys.argv[sys.argv.index('--') + 1])
    out.mkdir(parents=True, exist_ok=True)
    body = bpy.data.objects.get('Body')
    if body is None or 'art011_previous_position' not in body.data.attributes:
        raise ValueError('Load the Art011 master, not the portable mesh or another revision')
    p = np.array([v.co[:] for v in body.data.vertices])
    old = np.empty(p.size)
    body.data.attributes['art011_previous_position'].data.foreach_get('vector', old)
    old = old.reshape(-1, 3)
    edges = np.array([e.vertices[:] for e in body.data.edges])
    current_lengths = np.linalg.norm(p[edges[:, 0]] - p[edges[:, 1]], axis=1)
    prior_lengths = np.linalg.norm(old[edges[:, 0]] - old[edges[:, 1]], axis=1)
    ratio = current_lengths / np.maximum(prior_lengths, 1e-10)
    protected = (old[:, 2] > 1.60) | (old[:, 2] < 1.25) | (abs(old[:, 0]) > .28) | (old[:, 1] > .02)
    report = {
        'revision': body['art011'],
        'bodyVertices': len(p),
        'protectedVerticesUnchanged': bool(np.array_equal(p[protected], old[protected])),
        'protectedVertexCount': int(protected.sum()),
        'edgeStretchP999': float(np.quantile(ratio, .999)),
        'edgeStretchMax': float(ratio.max()),
        'finiteGeometry': bool(np.isfinite(p).all()),
        'garment': {},
        'limitations': 'Every fourth evaluated cloth vertex; 3 cm nearest-surface window; 0.5 mm penetration threshold. Not a triangle-intersection or motion test.'
    }
    assert report['protectedVerticesUnchanged'] and report['finiteGeometry']
    bvh = BVHTree.FromPolygons([Vector(v) for v in p], [f.vertices[:] for f in body.data.polygons])
    deps = bpy.context.evaluated_depsgraph_get()
    for name in ('Loose over-trapezius panel L', 'Loose over-trapezius panel R'):
        obj = bpy.data.objects[name]
        evaluated = obj.evaluated_get(deps)
        mesh = evaluated.to_mesh()
        penetrations, near = [], 0
        try:
            for i in range(0, len(mesh.vertices), 4):
                point = evaluated.matrix_world @ mesh.vertices[i].co
                hit, normal, _, distance = bvh.find_nearest(point)
                if hit is None:
                    raise ValueError('Nearest body surface missing')
                signed = (point - hit).dot(normal)
                if distance < .03:
                    near += 1
                    if signed < -.0005:
                        penetrations.append({'index': i, 'depth': float(-signed), 'position': list(point)})
            report['garment'][name] = {
                'evaluatedVertices': len(mesh.vertices),
                'sampleStride': 4,
                'nearSurfaceSamples': near,
                'penetrationSampleCount': len(penetrations),
                'maxDepthMetres': max((item['depth'] for item in penetrations), default=0),
                'examples': sorted(penetrations, key=lambda item: item['depth'], reverse=True)[:8]
            }
        finally:
            evaluated.to_mesh_clear()
    (out / 'surface-audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
