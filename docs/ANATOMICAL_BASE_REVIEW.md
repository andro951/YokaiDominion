# Anatomical base refinement

The procedural voxel body was rejected as the final foundation because its fused fingers, face, joints and weight transitions were not adequate for the requested quality. The current authoring candidate uses the pinned MakeHuman CC0 base mesh, adult female morph data, skeleton and skin weights. No MakeHuman application logic is imported. See THIRD_PARTY_ASSETS.md and generated manifests for exact hashes.

Reference-specific shaping preserves the exaggerated design rather than treating realistic human proportions as a requirement. Native anatomical topology and individually weighted finger joints replace the fused primitive hands. The skinning fallback remains usable without the tissue solver.

Local actual Blender exports were independently sampled. Compared with the preceding procedural revision, the 99.9th-percentile edge stretch fell from approximately 6.90x to 3.23x for the overhead pose, 3.90x to 1.84x for crouch, and 4.24x to 1.55x for high kick. These are improvement measurements, NOT final acceptance: shoulder deformation and some contacts still need work. The baseline scripts are retained for reproduction.

The fitted chest garment now inherits anatomical body weights, rather than projecting across nearby arms. Free-hanging clothing and hair are still skinned placeholders. Corrective shape names in the new mesh are intentionally zero placeholders until anatomy-specific corrections are authored; do not claim they are functional corrections.

A render review also caught a Godot material issue: COLOR_0 was present, but the imported white-base material did not visibly use it. Explicit linear vertex-colour material setup is required in both the native and CPU-deformation rendering paths. Verification must include rendered colour, not just successful import.

Current asset remains a blockout/refinement prototype, not a finished likeness, anatomically calibrated simulation, or game-ready release.
