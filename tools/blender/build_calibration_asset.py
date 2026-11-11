"""Generate an export-calibration limb, NOT the character.
Run: blender --background --python-exit-code 1 --python this_file.py -- --out artifacts/calibration
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import bpy
from mathutils import Vector


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    scene.frame_start, scene.frame_end = 1, 25
    scene.render.fps = 24

    segments, rings = 24, 17
    vertices = []
    for ring in range(rings):
        z = 0.8 * ring / (rings - 1)
        radius = 0.065 + 0.015 * math.sin(math.pi * z / 0.8)
        for j in range(segments):
            angle = 2 * math.pi * j / segments
            vertices.append((radius * math.cos(angle), radius * math.sin(angle), z))
    faces = []
    for ring in range(rings - 1):
        for j in range(segments):
            a = ring * segments + j
            b = ring * segments + (j + 1) % segments
            faces.append((a, b, b + segments, a + segments))
    faces.append(tuple(reversed(range(segments))))
    faces.append(tuple((rings - 1) * segments + j for j in range(segments)))
    data = bpy.data.meshes.new('CalibrationSurface')
    data.from_pydata(vertices, [], faces)
    data.update()
    mesh = bpy.data.objects.new('CalibrationLimb', data)
    bpy.context.collection.objects.link(mesh)
    for face in data.polygons:
        face.use_smooth = len(face.vertices) == 4
    mat = bpy.data.materials.new('CalibrationMatte')
    mat.diffuse_color = (0.16, 0.43, 0.5, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = mat.diffuse_color
    shader.inputs['Roughness'].default_value = 0.6
    data.materials.append(mat)

    arm_data = bpy.data.armatures.new('CalibrationRig')
    rig = bpy.data.objects.new('CalibrationRig', arm_data)
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    root = arm_data.edit_bones.new('Root')
    root.head, root.tail = (0, 0, -0.05), (0, 0, 0)
    upper = arm_data.edit_bones.new('Upper')
    upper.head, upper.tail, upper.parent = (0, 0, 0), (0, 0, 0.4), root
    lower = arm_data.edit_bones.new('Lower')
    lower.head, lower.tail, lower.parent = (0, 0, 0.4), (0, 0, 0.8), upper
    lower.use_connect = True
    bpy.ops.object.mode_set(mode='OBJECT')
    mesh.parent = rig
    modifier = mesh.modifiers.new('Skin', 'ARMATURE')
    modifier.object = rig
    up = mesh.vertex_groups.new(name='Upper')
    lo = mesh.vertex_groups.new(name='Lower')
    for i, (_, _, z) in enumerate(vertices):
        blend = max(0.0, min(1.0, (z - 0.30) / 0.20))
        blend = blend * blend * (3 - 2 * blend)
        if blend < 1:
            up.add([i], 1 - blend, 'REPLACE')
        if blend > 0:
            lo.add([i], blend, 'REPLACE')
    mesh.shape_key_add(name='Basis')
    correction = mesh.shape_key_add(name='JointVolumeCorrective')
    for point in correction.data:
        amount = 0.22 * math.exp(-((point.co.z - 0.4) / 0.10) ** 2)
        point.co.x *= 1 + amount
        point.co.y *= 1 + amount
    pose = rig.pose.bones['Lower']
    pose.rotation_mode = 'XYZ'
    for frame, angle, value in [(1, 0.0, 0.0), (13, math.radians(75), 1.0), (25, 0.0, 0.0)]:
        pose.rotation_euler = (0, 0, angle)
        pose.keyframe_insert(data_path='rotation_euler', frame=frame, group='Lower')
        correction.value = value
        correction.keyframe_insert(data_path='value', frame=frame)

    # Cameras and lights remain in the editable Blender source, not the GLB selection.
    bpy.ops.object.camera_add(location=(1.25, -2.4, 1.15))
    camera = bpy.context.object
    camera.name = 'PreviewCamera'
    target = Vector((-0.08, 0, 0.38))
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = 1.15
    scene.camera = camera
    bpy.ops.object.light_add(type='AREA', location=(1.5, -2, 2.5))
    light = bpy.context.object
    light.data.energy = 250
    light.data.shape = 'DISK'
    light.data.size = 3
    light.rotation_euler = (target - light.location).to_track_quat('-Z', 'Y').to_euler()
    scene.world.color = (0.15, 0.15, 0.15)
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 16
    scene.render.resolution_x = 640
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = True

    scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(out / 'calibration.blend'))
    bpy.ops.object.select_all(action='DESELECT')
    mesh.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.gltf(
        filepath=str(out / 'calibration.glb'), export_format='GLB',
        use_selection=True, export_yup=True, export_apply=False,
        export_animations=True, export_animation_mode='SCENE',
        export_frame_range=True, export_force_sampling=True,
        export_skins=True, export_morph=True, export_morph_animation=True,
        export_cameras=False, export_lights=False,
    )
    for frame, name in [(1, 'rest'), (13, 'bend')]:
        scene.frame_set(frame)
        scene.render.filepath = str(out / f'{name}.png')
        bpy.ops.render.render(write_still=True)
    scene.frame_set(1)
    manifest = {
        'schemaVersion': 1, 'purpose': 'export-calibration fixture, not a character',
        'blender': bpy.app.version_string, 'units': 'metres',
        'sourceUpAxis': 'Z', 'gltfUpAxis': 'Y',
        'bones': [b.name for b in arm_data.bones],
        'shapeKeys': [k.name for k in mesh.data.shape_keys.key_blocks],
        'vertices': len(data.vertices), 'frames': [1, 25],
        'files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file()},
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('YOKAI_BLENDER_CALIBRATION_PASS')


if __name__ == '__main__':
    main()
