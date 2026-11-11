# Run the current development milestone

This is a physics laboratory, NOT the finished game or character.

## Requirements
- .NET 10 SDK (global.json accepts the newest stable feature band).
- Godot 4.7.2 .NET. The standard/non-.NET editor will not run C#.
- Windows x64 or Linux x64 for the initial validation targets.

## Numerical checks (no Godot required)
From the repository root: `dotnet run --project tests/Yokai.Tissue.Checks -c Release`.
The executable exits nonzero for any failure and writes artifacts/core-results.json. No test framework packages are required.

## Interactive lab
Run `dotnet build game/YokaiDominion.csproj -c Debug`, then open game/project.godot in the matching .NET editor and press F6/F5, or launch the Godot executable with `--path game` from the repository root.

Space: move the support through a jump-shaped trajectory. D: reset as a free falling block. R: reset to attached. P: pause. Right-drag and mouse wheel: orbit/zoom. Escape: exit.

The teal plate is a kinematic attachment reference, not a simulated garment. The purple block is a numerical fixture, not character anatomy. The lab is deliberately small so failed deformation is easy to inspect.

## Automated scene checks
- Headless numerical/engine integration: `godot --headless --path game -- --smoke`.
- Rendered check on a display: `godot --path game -- --smoke --capture=/absolute/path/lab.png`.
- Linux software render: prefix the latter command with `LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a`.

Use your actual .NET Godot binary path in place of `godot`. The runner must see YOKAI_GODOT_SMOKE_PASS, not merely process exit zero.

## Evidence levels
Core checks prove only their stated invariants. Headless Godot execution proves the C# scene can run. A captured frame proves an image was rendered, but must still be visually inspected. Software rendering says nothing about actual GTX 1080 performance, production mesh skinning, or anatomical realism.

Generated reports and screenshots are workflow artifacts, not checked-in generated noise. Persistent progress, exact run IDs, and limitations belong in docs/PROGRESS.md.
