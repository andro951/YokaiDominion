# Tissue solver baseline

This is an original C# implementation of tetrahedral stable Neo-Hookean elasticity in an XPBD-style integrator, not spring-bone motion. It is a research baseline, not yet calibrated anatomical tissue.

## Conventions and mechanics
Metres, kilograms, seconds; right-handed world coordinates with +Y up. Double-precision internal vectors/matrices, column-vector convention. A tetrahedron contributes one quarter of its density-times-rest-volume mass to each vertex. Rest-volume and tetrahedron orientation are validated.

The energy density is mu/2*(F:F-3)-mu*(J-1)+lambdaStable/2*(J-1)^2. Here mu=E/(2*(1+nu)), lambdaStable=lambdaLame+mu, J=det(F), and F=Ds*inverse(Dm). This parameter correction reproduces requested small-strain Lamé parameters.

Two compliant constraints are used per element: norm(F) and J-(1+mu/lambdaStable). Their compliances are 1/(mu*V0) and 1/(lambdaStable*V0), scaled by 1/h^2. A local coupled 2x2 XPBD update is used rather than sequentially projecting these two terms. This avoids spurious rest motion caused by temporarily unbalanced distortional and hydrostatic prestress. Multipliers are accumulated across position iterations and reset per substep.

The block solver is a project implementation choice. Validation includes finite-difference stress checks and unloaded-rest drift, rather than assuming it is correct because it follows a named method.

## Implemented
Hard and compliant translational attachments, explicit teleport/reset, fixed-step integration with substeps, analytic plane/capsule point contacts, simple friction, diagnostic volume/inversion checks, barycentric surface embedding, and exponential velocity drag. No Godot types are required by this library.

## Important limitations
- Uniform isotropic material; no anatomical compartments, skin membrane, fibre directions, or calibrated viscoelasticity.
- Translational support only at this milestone; rotational skeletal support is required before character integration.
- Discrete particle contacts, no continuous collision detection, self-collision, surface-triangle contact, or two-way rigid-body/cloth coupling.
- Velocity drag is not a biological damping model and damps bulk motion too.
- No proof of convergence, timestep independence, inversion recovery, or real-time performance. A fully collapsed element is diagnosed, not magically repaired.
- Finite-element locking and mesh-resolution sensitivity still require characterization.
- Surface embedding currently requires visible vertices inside the simulation volume; it refuses to guess bindings outside it.

## Research references
Macklin, Muller, Chentanez (2016), XPBD: Position-Based Simulation of Compliant Constrained Dynamics. https://matthias-research.github.io/pages/publications/XPBD.pdf

Macklin and Muller (2021), A Constraint-based Formulation of Stable Neo-Hookean Materials. https://matthias-research.github.io/pages/publications/neohookean.pdf

Smith, de Goes, Kim (2018), Stable Neo-Hookean Flesh Simulation. https://graphics.pixar.com/library/StableElasticity/

The papers are references; no third-party source code or paper files are redistributed here.
