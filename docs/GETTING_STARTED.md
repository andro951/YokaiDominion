# Run milestone 001

This is an executable physics/asset pipeline, NOT the finished game or character.

## Toolchain
.NET 10 SDK; Godot 4.7.2 **.NET** edition; Blender 4.5.3 LTS only for asset generation. The pure C# tests do not require Godot or Blender. Windows and Linux numerical builds have passed; engine/render workflows currently run on Linux hosted runners.

## C# tests
From the repository root, run `dotnet run --project tests/Yokai.Tissue.Checks -c Release`, then `dotnet run --project tests/Yokai.Tissue.AdvancedChecks -c Release`. There are 18 core and 9 advanced checks. Any failure exits nonzero. Reports go to `artifacts/core-results.json` and `artifacts/advanced-results.json`.

## Interactive Godot lab
Run `dotnet build game/YokaiDominion.csproj -c Debug`. Open `game/project.godot` with Godot 4.7.2 .NET and run the main scene, or invoke its executable with `--path game` from the repository root.

Space: jump-shaped support trajectory. T: turn support. D: free-drop fixture. R: reset attached fixture. P: pause. Right-drag/wheel: orbit/zoom. Escape: exit. The teal plate is an attachment reference, not simulated cloth. The purple block is an engineering fixture, not character anatomy.

Headless check: `godot --headless --path game -- --smoke`.
Rendered check: `godot --path game --audio-driver Dummy -- --smoke --capture=/absolute/path/lab.png`.
Linux software render: prefix the rendered command with `LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a`.

Replace `godot` with the actual .NET binary path. Success requires the `YOKAI_GODOT_SMOKE_PASS` marker and acceptable diagnostics, not exit zero alone. The smoke test runs 600 physics ticks.

## Editable Blender calibration asset
Run `blender --background --python-exit-code 1 --python tools/blender/build_calibration_asset.py -- --out artifacts/calibration` from the root. This produces editable `calibration.blend`, exported `calibration.glb`, rest/bend previews and a hash manifest. It is a three-bone test limb, not the character.

Run `python tools/validate_glb.py artifacts/calibration/calibration.glb --report artifacts/calibration/glb-validation.json` to check geometry streams, normalized skinning and a combined bone/morph clip with actual changing values.

To check the native engine import, copy the GLB to `game/Assets/Calibration/calibration.glb`, build the Godot C# project, then import with `godot --headless --editor --path game --import`. Run `godot --headless --path game res://Scenes/ImportCalibration.tscn -- --report=/absolute/path/import.json`. For a rendered check, omit `--headless` and add `--capture=/absolute/path/import.png` after the argument separator. The marker must be `YOKAI_NATIVE_ASSET_IMPORT_PASS`.

## GitHub validation
The `CSharp core checks`, `Godot integration and rendered smoke`, and `Blender to Godot asset calibration` workflows reproduce these paths. Runs retain JSON, logs, renders and generated calibration assets for 14 days. Code and evidence summaries remain versioned. The testing repository independently runs against `production.ref` and archives the exact source pair.

## Reference images
`assets/reference/manifest.json` identifies the exact original/secondary uploads by hash and role. They are not silently replaced by a different image or by the calibration fixture. Full-resolution bytes have not been committed through this connector workflow; the handoff archive includes them. They are needed before character likeness work.

## Evidence boundaries
Headless checks prove execution, not appearance. A rendered screenshot must be inspected. Hosted CPU/software-render timing does not establish GTX 1080 performance. Passing calibration import is not proof that a future full-body rig, tissue, cloth, hair or tail meets the project's quality goals.
