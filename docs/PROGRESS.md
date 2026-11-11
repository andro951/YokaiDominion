# Development checkpoints

## 001 - verified execution path
Production commit 809fef153337701459485c4c4c968060c91610b0 compiled and passed the initial volume check on Linux and Windows in Actions run 42955416399. This proves a basic C# build path, not the tissue solver.

The companion testing repository has an independent workflow checking an immutable production SHA.

## 002 - volumetric numerical baseline
Implemented engine-independent double-precision tetrahedral elasticity, coupled XPBD local solves, density-derived masses, hard/compliant translational attachments, plane/capsule contacts, reset/teleport, diagnostics, and barycentric surface binding. Added 18 executable checks plus JSON results. This checkpoint has not yet been executed at the moment of writing; inspect its actual CI result.

See SOLVER.md for mathematical conventions and explicit limitations. No claim of anatomical accuracy, game readiness, or GPU performance.

## Next
Resolve any failed numerical checks, add a Godot .NET laboratory and rendered smoke test, then add rotational skeletal attachments before beginning character deformation.

## Visual authority
Original illustration governs body proportions, silhouette, outfit and colors. The generated turnaround is secondary for detail. The character remains unnamed; its generated Astra label is not an approved naming decision.
