# YokaiDominion

A C#-first 3D game project and reusable character/soft-tissue simulation package.

## Current status

Repository initialization and technical planning only. No character model, game implementation, or tissue simulator is delivered or validated yet. This README records the project requirements; it is not a claim that those features already exist.

## Character reference priority

The original single character illustration is the primary visual reference. Preserve its body proportions and silhouette, especially breast size and hip shape, its outfit, and its skin and material colors. Do not substitute the altered proportions or palette from the generated turnaround sheet.

The generated character sheet is a secondary reference for fine details such as hair, horns, face, and additional viewpoints. When the references disagree, the original image wins. Missing details may be designed as needed while staying consistent with the original.

The intended result is a stylized character with highly convincing physical movement, not a conversion to photorealistic human proportions.

## Technical direction

- Prefer C# for gameplay, runtime integration, and the portable simulation core.
- Recommended initial host under evaluation: Godot 4 .NET. The engine/setup is being settled before character implementation; no engine project has been created yet.
- Author editable character geometry, rigging, skinning, textures, and corrective shapes in Blender. Blender automation may use Python; that does not change the C# game/runtime requirement. GPU shaders, if needed, use the host's shader language.
- Develop the character and runtime simulation together. The deliverable is the model, simulation data, code, engine integration, tests, and documentation, not an unsupported mesh or a rendered image alone.
- Keep the numerical simulation independent of engine-specific node, scene, rendering, and physics types. Use a thin engine integration layer.
- Preserve a usable skinned-character fallback when advanced simulation is disabled. Reuse in another engine requires an adapter; runtime physics is not assumed to transfer automatically in a model file.

## Deformation and movement requirements

Prioritize localized volumetric soft tissue for the breasts and buttocks, with appropriate structural support, graded attachments, volume resistance, damping, and collision response. Preserve the firmer muscular foundation elsewhere. XPBD-style volumetric elasticity is a candidate, not a quality guarantee or a finalized implementation.

The mesh, deformation rig, corrective shapes, collision setup, and runtime must be tested together for running and stopping, jumping, running jumps, hard landings, ground slams, deep crouches, torso twists, high kicks and martial-arts poses, knockdowns, lying on the ground, and getting up. Evaluate clothing, hair, tail, and body contact separately and together. An attractive rest pose alone does not establish game readiness.

## Development order

1. Verify the development toolchain and a minimal engine integration.
2. Establish original-reference proportions and an early rigged body.
3. Validate difficult poses and localized tissue deformation in-engine.
4. Refine anatomy, topology, materials, clothing, hair, tail, and animations iteratively.
5. Package source assets, runtime data, reproducible builds, quality/performance settings, and documented validation results.

Do not finish a polished unrigged character before proving the deformation approach.

## Repository responsibilities

This repository is the source of truth for the game, reusable C# runtime, engine adapters, production assets, and project documentation.

[YokaiDominionTesting](https://github.com/andro951/YokaiDominionTesting) is the companion validation workspace. It should test a pinned revision of this repository rather than maintain a divergent copy of production simulation code.

## Checkpoint policy

Commit and push small, coherent milestones during active development, including before risky or lengthy operations. Record what changed, what was actually tested, what remains untested, known failures, and the next step. Mark incomplete checkpoints explicitly. Do not rely on the chat session or temporary working files as the only record of progress.

Do not add credentials, licenses, downloaded proprietary dependencies, or unapproved third-party assets to version control.
