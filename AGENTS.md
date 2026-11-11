# Development handoff

## User decisions
C# is strongly preferred. Use Godot .NET as the initial host, Blender for editable assets, and a portable C# numerical core. Develop the model and its advanced localized tissue runtime together. The user prioritizes quality over simple spring-bone shortcuts and has authorized work in both andro951/YokaiDominion and andro951/YokaiDominionTesting.

Original illustration controls sizes, hip shape, chest size, outfit and palette. Turnaround sheet is secondary fine-detail guidance only. Exact image hashes/roles are in assets/reference/manifest.json. The character is not named Astra by user approval. Do not normalize away exaggerated proportions. Full-resolution images remain conversation attachments; verify/recover those exact assets before likeness work rather than inventing their contents from this text.

## Resume procedure
Read docs/PROGRESS.md, docs/CHARACTER_CONTRACT.md, docs/SOLVER.md and docs/ROTATIONAL_SUPPORT.md. Inspect actual current repository heads before writing. The first engineering milestone is verified; next is original-reference proportions and an early deformation-ready rig, not more unrelated infrastructure.

Use small coherent commits and push regularly, before long/risky operations. Update progress with what actually ran, exact source SHA/run IDs, failures and next work. Never claim a submitted workflow passed without reading its result. Never force-reset over the user's work. Keep the testing repo pinned to an explicit production commit and avoid copying the production solver there.

## Validation
Run both C# executables; core workflow checks Windows/Linux. Godot workflow runs headless and software-rendered lab tests. Blender workflow creates .blend/.glb, validates streams/actual animation data, imports into Godot, samples bones and corrective weights, and renders a frame. Inspect actual rendered images. Artifact retention is finite: retain concise evidence in Git and package needed assets before relying on expiring files.

## Known environment
The originating chat container could not install .NET/Godot/Blender because download DNS failed. GitHub connector writes and hosted Actions worked. This is not a claim that local installation will always fail or that target hardware has been tested. Recheck capabilities in a new environment.

## Claims to avoid
No finished character/game exists at milestone 001. The block and calibration limb are fixtures, not anatomical or artistic deliverables. Uniform Neo-Hookean material, one rigid support per region, velocity drag and point contacts are not a production flesh model. No self-collision/CCD, skin layers, garment coupling, or target-GPU performance is validated. All scripts must preserve a usable non-simulated character fallback once the character exists.
