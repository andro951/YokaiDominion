# YokaiDominion

C#-first character/game project: **Godot 4.7.2 .NET**, **Blender 4.5.3 LTS**, and an engine-independent **.NET 10** volumetric tissue runtime.

## Milestone 002: actual rigged character and tissue integration

An editable character prototype now exists, not just the earlier block/limb fixtures. It has an anatomical humanoid body, fantasy details, clothing, an exported skeleton, diagnostic poses, four volumetric tissue regions, and C# deformation of the visible character in Godot.

**This is a functional modeling/deformation prototype, NOT finished character art, anatomically calibrated flesh, a complete game, or final game-ready acceptance.** The reference likeness, shoulders, supported rest shape, collision handling and clothing require substantial refinement.

## Inspect or run

See [RUN_CHARACTER.md](docs/RUN_CHARACTER.md). The downloadable milestone bundle includes the editable `.blend`, exported `.glb`, tissue data, both source repositories, actual rendered previews, a Godot motion video, reports, references and selected CC0 authoring data. Its game asset directory is populated for inspection.

For a fresh Git clone, obtain the `character-blockout` artifact from authoring run **42971187686** and install it with `python tools/install_character_asset.py character-blockout.zip`. Then run `tools/Run-CharacterLab.ps1` with the path to Godot 4.7.2 .NET, or build/import/run `game/Scenes/CharacterLab.tscn` manually. The default project scene remains the simpler numerical laboratory.

Character controls: left-drag/wheel orbit and zoom; 1-8 diagnostic poses; Space controlled jump; P native-skin/tissue comparison; R reset; Tab pose-study playback. The pose study is not a locomotion or contact-aware animation set.

## Verified evidence

- Asset authoring revision: `95af2eb3f902dac56705f4b6d51f16589a8d8787`, full Blender/portable C#/Godot run **42971187686**, successful. Body: 13,380 authoring vertices, 26,756 triangles after export, 176 exported joints. Native topology, fingers and weight data are derived from a pinned CC0 base, not generated entirely from scratch.
- Corrected renderer/runtime revision: `409ae5f39de720bb12e36cb82050825975f596a9`, run **42973867993**, successful. This reuses the exact SHA-256-checked asset above and checks actual rendered colour pixels as well as the character.
- The controlled four-second character jump fixture drives **5,984 surface vertices**. Peak local volume change is approximately **4.19% in each breast cage** and **2.51% in each glute cage**, with zero inverted elements. These are fixture integrity results, not proof of anatomical realism.
- Eight imported pose samples, rest skin-transform agreement and native skinned fallback passed. Actual pose images and video were downloaded and inspected. Residual shoulder stretching, floating crouch feet and floor penetration in the diagnostic knockdown remain known quality failures.
- The existing **27 general numerical checks passed on Windows and Linux** at runtime revision `409ae5f`, run **42973868017**. This does not establish target-PC graphics performance.

Detailed source/run identities and limitations are in [milestone evidence](docs/evidence/milestone-002.json), [progress](docs/PROGRESS.md), and the companion testing repository. Generated workflow artifacts have finite retention (30 days for character builds); source, data hashes, reports and reproduction instructions remain in Git.

## Reference authority

The original single illustration controls body proportions, breast size, hip shape, silhouette, outfit and palette. The generated turnaround is secondary for hair/horns/face and missing views. The current prototype is not a new approved reference and must not replace the original target. The generated sheet's Astra label is not an approved character name; use Character01 internally.

Original/secondary image hashes and authority are in `assets/reference/manifest.json`. Full image bytes are included in the downloadable package, not currently in Git.

## Architecture and provenance

`src/Yokai.Tissue/` is portable C# without Godot dependencies. `game/` supplies skeletal-pose input and a CPU reference morph/skin/tissue rendering path. `tools/blender/build_character_anatomy.py` creates the current asset using selected CC0 graphical data; older procedural builders remain reproducible rejected baselines. See [THIRD_PARTY_ASSETS.md](docs/THIRD_PARTY_ASSETS.md). No upstream MakeHuman application code is imported.

The numerical assembly is optimized even in editor Debug builds; override `-p:Optimize=false` to step through its internals. The CPU mesh-rebuild path is not the final optimized game renderer. The companion YokaiDominionTesting repository tests a pinned production revision instead of copying the solver.

## Next quality work

Refine face, hair, horns, silhouette and clothing against the original; fix shoulder deformation with anatomical weights and real corrective shapes; fit tissue volumes and supported equilibrium rather than treating bounding cages as anatomical mass; implement body/garment contact and restraint; then validate dynamic actions and target-machine performance. The anatomical revision's two named corrective shapes are currently zero placeholders. Hair and free clothing are skinned, not physically simulated.

## Checkpoints

Push small coherent milestones during active work, including before risky operations. Preserve exact revisions, test evidence, failures and next actions. Do not weaken tests to hide defects. Do not commit credentials or licensed toolchain binaries. No development continues asynchronously after a response ends.
