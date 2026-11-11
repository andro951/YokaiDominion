# Character and runtime contract - draft 1

## Reference fidelity
Use the original illustration identified in assets/reference/manifest.json as the authority for body sizes, silhouette, outfit, and palette. The generated turnaround cannot overrule it. Establish size/profile decisions in a multi-view blockout before fine surface work. The artistically exaggerated shape stays; do not silently normalize anatomy. Do not bake illustration highlights/shadows into an inferred skin albedo.

## Asset components
Editable Blender source; continuous deformation-ready surface; separate garments/hair/horns/tail; game deformation skeleton separate from authoring controls; normalized skin weights; pose-corrective morph targets; animation clips; coarse tetrahedral tissue regions; surface embeddings; material/attachment masks; collider proxies; and engine-independent metadata.

## Coordinates
Use metres and identity object scales at export. Blender source is Z-up; glTF/Godot adapter is Y-up. Export converts the axis once. Simulation data must use the same exported rest-space convention as the skinned surface and bind matrices. Test the transform using a calibration asset; never compensate with unexplained 0.01/100 scale factors.

## Required rig capability
Root motion separated from hips; pelvis; articulated spine/chest; clavicles; upper/lower arms; forearm and upper-arm twist distribution; hands and fingers; thighs/calves; feet and toe roll; neck/head/jaw and facial deformation; controlled tail chain; hair controls. Bone quantity alone is not acceptance. Test poses and correctives determine quality.

## Tissue responsibility
Breasts and buttocks are primary compliant regions. Preserve muscular support elsewhere. The solver must ultimately support graded skeletal attachments, rest/support calibration, rotational motion and angular acceleration, material variation, robust contact, and clothing restraint. Runtime and asset data evolve together. A tissue-disabled skinned fallback must remain usable.

## Acceptance motions
Deep crouch, overhead reach, torso twist, high kick, running, abrupt stop/turn, jump, running jump, hard landing, ground slam, knockdown, prone/supine ground contact, and get-up. Record normal-speed and slow-motion views from multiple angles. Correct shoulder/hip deformation and convincing base animation precede claims of realistic secondary motion.

## What the calibration fixture is
The procedural limb in tools/blender exists only to prove that bones, skin weights, corrective shapes, and animation can be authored/exported and preserved. It is not a proposed body part, anatomical approximation, or visual-quality target for the character.

## Current missing production requirements
No final character model or retopology. No muscle/skin layers, calibrated tissue constants, fitted garments, hair/tail simulation, full-body ragdoll, triangle-level self-contact, continuous collision detection, or performance budget has been accepted. Treat these as open work, not implicit features of the baseline solver.
