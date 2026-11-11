# Development checkpoints

## 001 - verified execution path
809fef153337701459485c4c4c968060c91610b0 compiled and passed the bootstrap check on Linux and Windows in Actions run 42955416399.

## 002 - numerical core verified
9437302ce6353d6a3006d73e4ad0c9feaa473e59 passed 18 numerical checks on Linux and Windows (run 42955998709). The core implements tetrahedral stable Neo-Hookean elasticity with coupled XPBD projection, mass distribution, attachments, discrete contact and surface embedding.

## 003 - real Godot execution/render verified
8a97326999b7ad1de1a1d6c3719a13962bd114a9 compiled, imported, ran headlessly and produced an actual software-rendered screenshot (run 42956320270). The downloaded image was inspected. The initial nu=0.48 fixture was too compressible, despite passing the original finite-state smoke check.

## 004 - Blender export verified
At ec943fc6301626a424d5d198736b5032710afdc1, Blender 4.5.3 authored an editable three-bone calibration limb, corrective shape and animation, rendered rest/bend previews and exported GLB (run 42956777143). Independent GLB validation confirmed skin weights, morph target and bone/morph animation channels. The bent preview was inspected. This fixture is NOT the character model.

## 005 - rotational support
Added double-precision quaternion poses, rigid support motion, pose-aware reset and impulse-free rigid teleport. Nine additional tests cover rotation and a volume envelope. The first CI attempt failed at compile time because two old tests used target-typed new() that became ambiguous after the pose overload was added. This follow-up makes those arguments explicitly V3; no assertions were weakened.

## 006 - native asset integration and volume gates
Added native Godot import validation for the Blender GLB: skeleton resolution, skin binds, animated bone rotation and corrective morph sampling, with optional actual engine screenshot. Its execution result must still be checked.

The testing repository's one-variable material study (run 42957245209) found peak local volume change of 30.7232% at nu=0.48 and 2.9068% at nu=0.499, with no inversions in either. The lab now uses nu=0.499 and gates peak volume change below 5% and final change below 2%. These are fixture limits, not anatomical validation.

## Next
Confirm the corrected full 27-check suite and the native import/render workflow. Then begin original-reference character proportion blockout, rigging and localized simulation data. No finished character model, final anatomy, clothes/hair/tail physics, target-GPU performance or game has been delivered.

## Recovery and reference authority
Original illustration governs body proportions, silhouette, outfit and colors. Generated turnaround is secondary detail guidance, not a substitute. The generated Astra heading is not an approved character name. Full-resolution reference bytes remain in the conversation; their exact hashes and roles are recorded in assets/reference/manifest.json.

Progress is checkpointed through GitHub, not left only in the chat container. Local .NET/Godot/Blender installation is unavailable; execution is verified through Actions. Generated binaries/images are workflow artifacts; source generators and evidence summaries remain in Git.
