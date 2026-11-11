# Run the character prototype

## Requirements

Use Godot **4.7.2 .NET** and the **.NET 10 SDK**. The standard non-.NET Godot download cannot load these C# scripts. Blender is needed only to regenerate or edit the source model, not to run an already-generated asset.

## Ready-to-inspect milestone bundle

The milestone bundle includes both source repositories and places the generated GLB and tissue data in `source/YokaiDominion/game/Assets/Character01/`. The editable Blender file is separate under `assets/Character01/`. Do not mistake the still renders for the actual deliverable.

On Windows, from the production repository root:

`powershell -File tools/Run-CharacterLab.ps1 -GodotPath "C:\path\to\Godot_v4.7.2-stable_mono_win64.exe"`

The launcher builds C# with optimization, imports the asset, and opens `Scenes/CharacterLab.tscn`. Its Windows launch path still requires validation on the target PC; hosted Linux rendering is not a Windows GPU performance test.

## A fresh Git clone

Download the `character-blockout` artifact from the selected successful **Character blockout and deformation** Actions run. Install only the required asset files with:

`python tools/install_character_asset.py character-blockout.zip`

The installer validates the GLB header, schema and authoring revision. It refuses to overwrite a different local asset unless `--force` is explicitly supplied. Then run the launcher above, or manually build the C# project, import through the .NET editor, and run the CharacterLab scene. The project's default scene remains the simpler numerical laboratory used by other regression tests.

## Controls

- Drag with the left mouse button to orbit; use the wheel to zoom.
- 1 through 8 select the diagnostic poses.
- Space runs the controlled jump fixture.
- P switches between tissue deformation and the native skinned fallback.
- Tab plays the pose-study clip. This is not a polished animation set and is not an acceptance-tested contact sequence.
- R resets tissue to its authored rest shape.

## Regenerate the editable asset

Use Blender 4.5.3 LTS, the pinned CC0 graphical data documented in THIRD_PARTY_ASSETS.md, and `tools/blender/build_character_anatomy.py`. The bundle contains only the selected data files needed by this authoring script, not the third-party application source.

`blender --background --python-exit-code 1 --python tools/blender/build_character_anatomy.py -- --base-data PATH/TO/makehuman/data --out artifacts/character`

The numerical assembly and visible-mesh updater are an inspectable reference implementation, not the final optimized game renderer. Do not infer target-machine frame rate from a completed software-rendered CI sequence. Clothing, body contact, supported equilibrium, detailed anatomy and corrective shapes still require refinement.
