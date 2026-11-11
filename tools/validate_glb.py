"""Independent structural and animation validation of the calibration GLB.
This does not replace native engine import and rendered deformation inspection.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import struct


def validate(path: Path) -> dict:
    raw = path.read_bytes()
    if len(raw) < 20:
        raise ValueError('Truncated GLB')
    magic, version, size = struct.unpack_from('<4sII', raw)
    if magic != b'glTF' or version != 2 or size != len(raw):
        raise ValueError('Invalid GLB header')
    offset, document, binary = 12, None, None
    while offset < size:
        if offset + 8 > size:
            raise ValueError('Truncated chunk header')
        length, kind = struct.unpack_from('<II', raw, offset)
        offset += 8
        if offset + length > size:
            raise ValueError('Chunk exceeds GLB bounds')
        chunk = raw[offset:offset + length]
        if kind == 0x4E4F534A:
            document = json.loads(chunk)
        elif kind == 0x004E4942:
            binary = chunk
        offset += length
    if document is None or binary is None:
        raise ValueError('Missing JSON/BIN chunk')
    skins = document.get('skins', [])
    if not skins or max(len(s.get('joints', [])) for s in skins) < 3:
        raise ValueError('Three-bone skeleton was not exported')
    if not any('skin' in n for n in document.get('nodes', [])):
        raise ValueError('No skinned node')

    def accessor(index: int):
        a = document['accessors'][index]
        view = document['bufferViews'][a['bufferView']]
        components = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
        code = {5121: 'B', 5123: 'H', 5125: 'I', 5126: 'f'}[a['componentType']]
        fmt = '<' + code * components
        packed = struct.calcsize(fmt)
        stride = view.get('byteStride', packed)
        start = view.get('byteOffset', 0) + a.get('byteOffset', 0)
        end = view.get('byteOffset', 0) + view['byteLength']
        for i in range(a['count']):
            at = start + i * stride
            if at + packed > end or at + packed > len(binary):
                raise ValueError('Accessor exceeds buffer bounds')
            value = struct.unpack_from(fmt, binary, at)
            if a.get('normalized') and code != 'f':
                maximum = {'B': 255, 'H': 65535, 'I': 4294967295}[code]
                value = tuple(v / maximum for v in value)
            yield value

    skinned = morphs = vertices = 0
    for mesh in document.get('meshes', []):
        for primitive in mesh.get('primitives', []):
            attributes = primitive['attributes']
            if not {'POSITION', 'NORMAL', 'TANGENT', 'TEXCOORD_0'} <= attributes.keys():
                raise ValueError('Missing geometry, normal, tangent or UV stream')
            for p in accessor(attributes['POSITION']):
                if not all(math.isfinite(v) for v in p):
                    raise ValueError('Non-finite geometry')
                vertices += 1
            if 'JOINTS_0' in attributes and 'WEIGHTS_0' in attributes:
                skinned += 1
                for weights in accessor(attributes['WEIGHTS_0']):
                    if abs(sum(weights) - 1) > 1e-4 or min(weights) < 0:
                        raise ValueError('Invalid skin weight normalization')
            morphs += len(primitive.get('targets', []))
    if not skinned or not morphs:
        raise ValueError('Skin or corrective morph targets lost during export')
    animations = document.get('animations', [])
    combined = [a for a in animations if {'rotation', 'weights'} <= {c['target']['path'] for c in a['channels']}]
    if len(combined) != 1:
        raise ValueError('Expected one combined bone/morph clip; separate object clips are not accepted')
    motion = correction = False
    for channel in combined[0]['channels']:
        target = channel['target']
        node = document['nodes'][target['node']]
        samples = list(accessor(combined[0]['samplers'][channel['sampler']]['output']))
        if target['path'] == 'rotation' and node.get('name') == 'Lower':
            motion = any(sum((a-b)**2 for a, b in zip(v, samples[0])) > 0.1 for v in samples)
        if target['path'] == 'weights':
            correction = max(v[0] for v in samples) > 0.9 and min(v[0] for v in samples) < 0.05
    if not motion or not correction:
        raise ValueError('Combined clip does not actually bend the joint and animate its corrective')
    return {'passed': True, 'vertices': vertices, 'skins': len(skins), 'morphTargets': morphs,
            'combinedAnimation': combined[0].get('name'), 'actualJointMotion': motion,
            'actualCorrectiveMotion': correction, 'uvAndTangentsPresent': True}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('glb', type=Path)
    p.add_argument('--report', type=Path)
    args = p.parse_args()
    report = validate(args.glb)
    text = json.dumps(report, indent=2)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding='utf-8')
