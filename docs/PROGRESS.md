# Progress: milestone 002 handoff

## Delivered

Actual editable Character01 .blend and animated GLB; anatomical body with separate fantasy details and clothing; 176-joint deformation skeleton including fingers; eight diagnostic poses; four tetrahedral tissue regions with graded supports; portable C# region-data loading and surface binding; a Godot morph/skin/tissue reference path and physics-disabled native-skin fallback; rendered pose/motion evidence; a safe asset installer and Windows launch script.

This is an engineering/modeling prototype, not final art or game-ready acceptance. The original illustration remains authoritative. Do not treat the current face, hair, costume edges or silhouette as approved.

## Verified checkpoints

- Asset: `95af2eb3f902dac56705f4b6d51f16589a8d8787`, run 42971187686. Blender authored source assets and renders. Portable C# cage checks passed. Godot headless and rendered pose/jump/fallback checks passed.
- Runtime/colour: `409ae5f39de720bb12e36cb82050825975f596a9`, run 42973867993. Reused the exact asset (GLB SHA256 f66da485c5d5fe62f02ecc7b905cfd6baffff055fd299d8a5935eb288cc17850), compiled optimized assemblies, passed pixel-based colour calibration and actual-character rendered checks.
- Core checks: same runtime revision, run 42973868017; 18 core plus 9 advanced checks passed on both Windows and Linux.
- Local installer checks: valid artifact installed; identical reinstall was idempotent; differing local content was preserved and overwrite refused; explicit force restored the artifact.

The final jump fixture reports 5,984 bound surface vertices, maximum rest-skin transform discrepancy 0.00008495 m, peak local volume error 4.1946% breast / 2.5084% glute, zero inversions, and peak surface displacement 0.1054 m. These quantities characterize this fixture only. Numerical boundedness does not imply believable tissue motion.

## Rejected attempts and corrections

The initial fused primitive body had severe overhead spikes. Independent GLB sampling showed 99.9th-percentile edge stretch above 100x. Smooth masks helped but retained unrelated pelvis/spine weights on distal arms. Anatomically limited chains improved that baseline, but fused fingers and joint topology still made it a poor final foundation.

The accepted *development foundation* now uses pinned CC0 MakeHuman graphical mesh/morph/rig/weight data, reshaped by our own authoring code. This is not an artistic acceptance. Independent sampled GLB audit now measures overhead p99.9 stretch 3.218x, crouch 1.831x, high kick 1.546x. The overhead maximum is still 7.823x and has 48 counted triangle-edge entries over 4x. Do not claim shoulder deformation is solved. No audit threshold was relaxed to hide this.

Initial tissue settings reached roughly 25% local volume error. Exposing solver iteration/substep settings, fitting the new cages and retuning material settings brought the controlled fixture below the provisional 5% volume-change goal. This was not a biological material calibration or a single-variable experiment across different geometry revisions.

Actual Godot renders exposed two colour bugs missed by structural checks: first an unused vertex-colour stream, then linear glTF colours displayed too dark by Compatibility rendering. The shared shader now handles OUTPUT_IS_SRGB explicitly. Rendered unshaded palette samples match the reference material within 2/255 per channel (skin exactly in that test). Do not substitute material-flag checks for pixel inspection.

## Unfinished / known failures

- Visual likeness, face/hair design, body sculpt detail, garment contour and reference proportion matching need refinement.
- Shoulder skinning/correctives are not accepted. The anatomical revision's named corrective keys contain zero offsets.
- Eight static pose imports are not a capable animation/controller suite. Crouch feet float and the diagnostic knockdown intersects the floor. No full-body IK or ragdoll controller.
- The four simulation meshes are coarse bounding volumes, not anatomical tissue layers. Their volume/mass, material values, support geometry and stress-free rest state are not biologically calibrated.
- The current model does not solve full body, garment, self or continuous collision; free garments and hair are only skinned. A chest patch following tissue is not garment restraint.
- CPU mesh rebuilding and solver quality settings have not been benchmarked on the user's Windows/GPU hardware. The launch script exists but has not been executed on that PC.

## Resume here

Read this file, CHARACTER_CONTRACT.md, ANATOMICAL_BASE_REVIEW.md and milestone-002.json. Inspect the actual .blend/GLB and previews before editing. Focus next on reference likeness and shoulder/hip deformation corrections, followed by fitted tissue volumes/support and contact. Do not add more unrelated infrastructure or label this prototype production-ready.

Recover generated assets from authoring run 42971187686 or the milestone bundle. The fast runtime regression pins that run and therefore requires its artifact while retained; after expiry regenerate with the full character authoring workflow and update the pin/hash explicitly. Full reproduction uses selected CC0 data at the immutable revision in THIRD_PARTY_ASSETS.md.

Source and measured summaries are on GitHub; the handoff archive includes both exact source repositories, source model, exported model, runtime data, selected authoring data with license, original references, previews and results. No asynchronous work is implied.
