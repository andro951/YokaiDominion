# YokaiDominion

C#-first game and reusable character/deformation project. Initial host: **Godot 4.7.2 .NET**, with **Blender 4.5.3 LTS** authoring and an engine-independent .NET 10 tissue core.

## Current milestone: executable foundation

The build/test/asset pipeline now runs, rather than being only a design proposal. There is a working volumetric tissue laboratory, 27 numerical checks, and an actual Blender-to-Godot rig/morph animation calibration test.

**There is not yet a finished game or character model.** The block and bent limb in test screenshots are engineering fixtures, not the character or the intended visual-quality target. Passing these tests does not establish anatomical realism or production readiness.

## Verified results

- The 18 core and 9 advanced C# checks passed on Windows and Linux at `e9705b8bb049975cf3e4fe2b4b019938ebbe232e`, Actions run [42958865072](https://github.com/andro951/YokaiDominion/actions/runs/42958865072).
- The Godot tissue scene compiled, ran headlessly, and produced an inspected software-rendered frame at `adaaf334b7a0d623857fd3dac4a4ae2db35c1fa7`, run [42958219773](https://github.com/andro951/YokaiDominion/actions/runs/42958219773). In its fixed jump fixture, maximum local volume change was about 2.91%, ending at 1.16%, with no inverted elements.
- Blender authored an editable rigged calibration asset, exported its skin/morph animation, and Godot successfully sampled and rendered it at `e9705b8bb049975cf3e4fe2b4b019938ebbe232e`, run [42958864946](https://github.com/andro951/YokaiDominion/actions/runs/42958864946). The imported corrective and bone motion were checked, not merely the presence of an animation file.

See [development progress](docs/PROGRESS.md) and [retained milestone evidence](docs/evidence/milestone-001.json). Generated .blend/.glb files, screenshots and full logs are available as workflow artifacts with 14-day retention. The source needed to regenerate them and durable result summaries stay in Git.

## Run the current laboratory

Install .NET 10 SDK and **Godot 4.7.2 .NET**, not the non-C# edition. From the repository root:

`dotnet run --project tests/Yokai.Tissue.Checks -c Release`

`dotnet run --project tests/Yokai.Tissue.AdvancedChecks -c Release`

`dotnet build game/YokaiDominion.csproj -c Debug`

Open `game/project.godot` in the matching .NET editor and run the main scene. Space: jump; T: turn; D: drop; R: reset; P: pause; right-drag/wheel: camera. Full headless/render/export reproduction is in [GETTING_STARTED.md](docs/GETTING_STARTED.md).

## Repository layout

- `src/Yokai.Tissue/`: portable, double-precision tetrahedral elasticity and support/contact code; no Godot dependency.
- `game/`: C# Godot laboratory and native asset-import checks.
- `tests/`: executable numerical regression suites.
- `tools/blender/`: editable asset-generation/export calibration scripts.
- `tools/validate_glb.py`: independent exported-file checks.
- `docs/`: decisions, evidence, limitations, character contract and next steps.
- `assets/reference/manifest.json`: exact original/secondary image hashes and authority rules. Full-resolution reference image bytes have not been committed through this connector workflow.

[YokaiDominionTesting](https://github.com/andro951/YokaiDominionTesting) checks an immutable production SHA and contains characterization experiments, not a divergent copy of the solver.

## Character direction and reference authority

The original illustration governs proportions, especially breast size and hip shape, silhouette, outfit, skin and material colors. The generated turnaround is secondary guidance for hair, horns, face and missing viewpoints. It must not overwrite the original's sizes or palette. The generated sheet's Astra label is not an approved character name.

Preserve the stylized design while pursuing convincing physical behavior. Author the character, deformation rig, skinning, corrective shapes, internal tissue regions and runtime integration together. The major soft regions are breasts and buttocks, supported by firmer underlying anatomy. See [CHARACTER_CONTRACT.md](docs/CHARACTER_CONTRACT.md).

## What is still missing

Original-reference character geometry and deformation rig; graded/multi-bone anatomical attachments; calibrated material/skin layers and damping; robust surface/self/continuous collision; clothing restraint; hair/tail simulation; full-body animations/ragdoll; target-PC performance measurements; gameplay and production packaging.

The current solver is a uniform isotropic research baseline with discrete particle contacts. It is not a complete flesh/cloth system. See [SOLVER.md](docs/SOLVER.md).

## Checkpoints

Commit and push small, coherent milestones during active work. Keep tested, submitted and unfinished work distinct. Record failures and fixes without weakening tests to hide defects. Preserve exact source/run IDs and a resumable next step. Do not commit credentials, licensed tools, or unapproved third-party assets.
