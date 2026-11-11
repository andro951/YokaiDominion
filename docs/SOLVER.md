# Tissue solver baseline

Original C# implementation of tetrahedral stable Neo-Hookean elasticity in an XPBD-style integrator. This is a research baseline, not calibrated anatomical flesh and not a spring-bone effect.

## Conventions and mechanics
Metres, kilograms, seconds; right-handed coordinates with +Y up; double-precision vectors/matrices and column-vector transforms. Each tetrahedron contributes one quarter of density times rest volume to each vertex. Mesh input is copied and validated; negative orientation is normalized.

Energy density is `mu/2*(F:F-3)-mu*(J-1)+lambdaStable/2*(J-1)^2`, with `mu=E/(2*(1+nu))`, `lambdaStable=lambdaLame+mu`, `J=det(F)` and `F=Ds*inverse(Dm)`. The correction matches the requested small-strain Lame parameters.

Each element uses compliant constraints `norm(F)` and `J-(1+mu/lambdaStable)`, with compliances `1/(mu*V0)` and `1/(lambdaStable*V0)`, scaled by `1/h^2`. A coupled local 2x2 XPBD update balances distortional and hydrostatic prestress at rest. Multipliers accumulate within a substep and reset at its start. The coupled update is a project implementation choice validated with stress finite differences and rest-drift tests; a method's name does not substitute for verification.

## Implemented
Mass lumping; hard/compliant attachments to one rigid support pose per region; fixed-step substeps; pose interpolation; impulse-free reset/teleport; analytic plane/capsule point contact; simple friction; volume/inversion/finite-state diagnostics; barycentric surface embedding; exponential velocity drag. The library contains no Godot types.

Animated support uses `animatedBoneWorld * inverse(bindBoneWorld)`. Rotation is double-precision shortest-path quaternion interpolation. See [ROTATIONAL_SUPPORT.md](ROTATIONAL_SUPPORT.md) for conventions and measured fixture results.

## Important limitations
- Uniform isotropic material, not anatomical compartments, skin membrane, fibres or calibrated viscoelasticity.
- One rigid support per body/region. Multi-bone-weighted attachments and full character adapter remain open work.
- Discrete particle contacts, not continuous, self or surface-triangle collision; no two-way rigid-body/cloth coupling. Contact limitations must be resolved before realistic falls are claimed.
- Velocity drag also damps bulk motion and is not a biological damping model.
- No established mesh/timestep convergence, locking analysis, general inversion recovery or target hardware performance.
- Fully collapsed elements remain visible through diagnostics; the implementation does not fabricate recovery.
- Embedding currently requires visible vertices inside the simulation volume and rejects outside points.
- The Godot fixture rebuilds a small debug ArrayMesh every rendered frame. It is not the production skinning/deformation path.

## Numerical gates
18 core plus 9 advanced executable checks. The fixed 162-tetrahedron jump fixture requires no inverted/non-finite elements, less than 5% peak local volume change, and less than 2% at its endpoint. These are documented fixture limits, not biological tolerances or a promise for arbitrary motion. Materials require character-specific calibration later.

## Research references
Macklin, Muller, Chentanez (2016), XPBD: Position-Based Simulation of Compliant Constrained Dynamics: https://matthias-research.github.io/pages/publications/XPBD.pdf

Macklin and Muller (2021), A Constraint-based Formulation of Stable Neo-Hookean Materials: https://matthias-research.github.io/pages/publications/neohookean.pdf

Smith, de Goes, Kim (2018), Stable Neo-Hookean Flesh Simulation: https://graphics.pixar.com/library/StableElasticity/

Papers are references; no third-party source or paper files are redistributed here.
