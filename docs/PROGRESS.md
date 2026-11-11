# Progress - milestone 001

## Completed and observed
The executable foundation is established. A portable C# volumetric simulation and a Godot .NET laboratory run through CI. Blender can create an editable rigged asset, export it with a corrective shape and animation, and Godot can import, sample and render those features.

The fixtures are deliberately simple. No actual character mesh or completed game has been produced.

## Evidence
- Bootstrap `809fef153337701459485c4c4c968060c91610b0`: Windows/Linux check passed, run 42955416399.
- Initial numerical core `9437302ce6353d6a3006d73e4ad0c9feaa473e59`: 18 checks passed on both OSes, run 42955998709.
- Current core `e9705b8bb049975cf3e4fe2b4b019938ebbe232e`: all 27 checks passed on both OSes, run 42958865072.
- Tuned Godot lab `adaaf334b7a0d623857fd3dac4a4ae2db35c1fa7`: compiled, ran headlessly, ran with Mesa/Xvfb, saved a frame that was downloaded and inspected, run 42958219773. At 600 ticks peak local volume change was 2.90681%, final 1.1593%, no inversion.
- Complete Blender/native Godot calibration `e9705b8bb049975cf3e4fe2b4b019938ebbe232e`: authored .blend, exported GLB, validated actual animation streams, sampled bone/morph motion in Godot headless and rendered modes; image downloaded and inspected, run 42958864946. Measured imported bend was 1.2961192 radians and corrective value 0.9901621 at the sampled middle time.
- Companion testing repo `b1d86c4ac241ba50b2a2ba2910e3d94689369084`: independent pinned 27 checks plus material sweep passed, run 42958498338.

Selected machine-readable evidence is in evidence/milestone-001.json. Full generated assets/logs are workflow artifacts; retention is 14 days.

## Problems found and corrected
The initial lab material changed local volume too much. The testing repo varied only Poisson ratio at fixed other inputs; nu=0.499 lowered peak local volume change from about 30.72% to 2.91%. Added explicit peak/end regression gates rather than relying only on finite state. This is fixture tuning, not biological calibration.

Adding rotational Step overloads exposed two target-typed-new ambiguities in older tests. Fixed by spelling V3 explicitly; no assertions were weakened.

Initial Blender export split bone and shape-key motion into separate clips. Native Godot checks caught the absent bone motion in the selected clip. Fixed SCENE export to merge object clips and used manual animation sampling. UV/tangent validation also caught polygon caps unsupported by Blender tangent generation; explicit triangle caps before skin/morph authoring resolved it. Final export has UVs, tangents and a combined bone/morph clip.

## Next milestone
Recover/verify the exact original and secondary reference images, then establish original-reference body proportions in a multi-view 3D blockout and an early full-body deformation rig. Introduce character-specific tetrahedral regions and graded supports alongside that rig; test difficult poses before final textures/topology polish. Do not substitute the calibration limb for anatomical work or keep expanding unrelated infrastructure.

## Outstanding quality requirements
No finished character likeness/topology/UVs, full-body rig, multi-bone support blending, anatomical layers/material fitting, cloth restraint, hair/tail dynamics, full-body ragdoll, robust triangle/self/continuous contact, or target-PC performance result. The debug mesh rebuild is not production deformation integration.

## Recovery and checkpoints
Source, tests, authoring scripts, requirements and measured summaries are committed regularly. Read AGENTS.md and CHARACTER_CONTRACT.md before continuing. Testing uses an immutable production pin, not copied solver code. Verify current heads and avoid overwriting user changes.

The original illustration controls sizes, silhouette, outfit and palette; the turnaround supplies secondary details only. Its Astra label is not an approved character name. Exact hashes are in assets/reference/manifest.json; image bytes remain conversation attachments and are included in the downloadable handoff package, not currently in Git.

The originating container could not install the tools; execution was performed through GitHub Actions. This is not a claim of local graphical/GPU execution. No asynchronous development continues after a response ends.
