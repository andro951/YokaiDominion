"""Small, reversible art edit on an existing .blend; never rebuild the anatomy.
Run in Blender: --python this_file.py -- --source model.blend --out output
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import bpy
from mathutils import Vector


def body_hash() -> str:
    body = bpy.data.objects.get('Body')
    if body is None or body.type != 'MESH':
        raise RuntimeError('Expected the existing Body mesh; refusing a different asset')
    import array
    coordinates = array.array('f', [0.0]) * (len(body.data.vertices) * 3)
    body.data.vertices.foreach_get('co', coordinates)
    return hashlib.sha256(coordinates.tobytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    source = args.source.resolve()
    bpy.ops.wm.open_mainfile(filepath=str(source))
    before_body = body_hash()
    cords = [o for o in bpy.context.scene.objects if o.type == 'MESH'
             and ('cord' in o.name.lower() or 'waist knot' in o.name.lower())
             and not o.hide_render]
    if not cords:
        raise RuntimeError('No visible cord meshes: ' + ', '.join(o.name for o in bpy.data.objects))
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    camera = scene.camera
    if camera is None:
        raise RuntimeError('Expected saved review camera')
    camera.data.type = 'ORTHO'
    camera.location = (0.45, -2.5, 1.38)
    camera.rotation_euler = (Vector((0.02, -0.12, 1.13)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.ortho_scale = 0.54
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.filepath = str(out / 'cord-before.png')
    bpy.ops.render.render(write_still=True)
    # Restrict geometry changes to the cord and tie. Body and garment remain untouched.
    records = []
    for obj in cords:
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
        modifier = obj.modifiers.get('Art007 cord rounding')
        if modifier is None:
            modifier = obj.modifiers.new('Art007 cord rounding', 'SUBSURF')
        modifier.levels = 1
        modifier.render_levels = 1
        modifier.subdivision_type = 'CATMULL_CLARK'
        records.append({'name': obj.name, 'sourceVertices': len(obj.data.vertices), 'modifier': modifier.name})
    # Preserve the dark cord colour while adding restrained fibre relief.
    originals = {slot.material for o in cords for slot in o.material_slots if slot.material}
    for original in originals:
        material = original.copy()
        material.name = original.name + ' | Art007 woven cord'
        material.use_nodes = True
        nodes, links = material.node_tree.nodes, material.node_tree.links
        bsdf = nodes.get('Principled BSDF')
        if bsdf is None:
            raise RuntimeError('Cord material has no Principled surface')
        for link in list(bsdf.inputs['Roughness'].links):
            links.remove(link)
        bsdf.inputs['Roughness'].default_value = 0.68
        bsdf.inputs['Specular IOR Level'].default_value = 0.25
        texcoord = nodes.new('ShaderNodeTexCoord')
        noise = nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 2600.0
        noise.inputs['Detail'].default_value = 2.0
        bump = nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = 0.22
        bump.inputs['Distance'].default_value = 0.00012
        links.new(texcoord.outputs['Object'], noise.inputs['Vector'])
        links.new(noise.outputs['Fac'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
        for obj in cords:
            for slot in obj.material_slots:
                if slot.material == original:
                    slot.material = material
    assert body_hash() == before_body, 'Unexpected anatomy change'
    body = bpy.data.objects['Body']
    body['asset_kind'] = 'Unfinished visual art; small cord refinement; not final likeness or runtime acceptance'
    scene['checkpoint_note'] = 'Art007: rounded cord/knot geometry and subtle fibre relief; anatomy unchanged.'
    # Save the complete editable model BEFORE rendering the remaining previews.
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(out / 'Character01_Cord007.blend'), compress=True)
    scene.render.filepath = str(out / 'cord-after.png')
    bpy.ops.render.render(write_still=True)
    camera.location = (3.2, -6.0, 2.55)
    camera.rotation_euler = (Vector((0.0, 0.0, 1.06)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.ortho_scale = 2.48
    scene.render.resolution_x = 850
    scene.render.resolution_y = 1100
    scene.render.filepath = str(out / 'three-quarter.png')
    bpy.ops.render.render(write_still=True)
    # Reopen the saved file to prove the geometry edit was saved, not just rendered.
    bpy.ops.wm.open_mainfile(filepath=str(out / 'Character01_Cord007.blend'))
    assert body_hash() == before_body
    for record in records:
        assert bpy.data.objects[record['name']].modifiers.get(record['modifier']) is not None
    report = {'status': 'small art edit, not finished character', 'blender': bpy.app.version_string,
              'sourceBlendSha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'bodyCoordinatesSha256': before_body, 'anatomyUnchanged': True,
              'savedBlendReopened': True, 'editedObjects': records,
              'files': {p.name: {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                        for p in out.iterdir() if p.suffix in ('.blend', '.png')}}
    (out / 'manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('YOKAI_CORD007_EDIT_AND_REOPEN_PASS')


if __name__ == '__main__':
    main()
