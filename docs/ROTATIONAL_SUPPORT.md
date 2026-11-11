# Rigid support and volume regression

## Skeletal transform convention
Each simulated tissue region accepts one rigid delta that maps its rest-space positions into world space: animatedBoneWorld * inverse(bindBoneWorld). Do not pass raw bone position as though it were a delta, and do not apply the character model transform twice. The C# RigidPose/Quaternion implementation uses double precision, right-handed rotations and shortest-path slerp.

Attachments interpolate the pose between fixed-step boundaries. Translation and rotation are supported; multi-bone-weighted attachments are not yet implemented. This milestone does not claim a complete humanoid adapter. Continuous motion must use Step; a teleport must use Teleport/ResetPose so it does not create artificial acceleration.

## Verified material experiment before this change
YokaiDominionTesting commit 20ada9ecae58144b6b9b974a196f7b2aca588140, Actions run 42957245209, using production ec943fc6301626a424d5d198736b5032710afdc1.

Holding E=6500 Pa, density=1000 kg/m^3, mesh, support trajectory, timestep, iterations and drag fixed, the 600-tick test measured:

- nu 0.48: peak local volume error 30.7232%, final 11.3849%.
- nu 0.49: peak 19.5142%, final 6.7873%.
- nu 0.495: peak 11.7007%, final 4.2858%.
- nu 0.499: peak 2.9068%, final 1.1593%.

All four cases were finite and had no inverted element samples. Therefore choose 0.499 for this laboratory fixture. This does not identify biological material properties. Near-incompressible locking, mesh dependence, stiffness convergence, skin layers and damping remain open validation tasks.

A regression gate now requires less than 5% peak and 2% end local volume change in this exact fixture, plus finite state and no inversion. These are explicitly laboratory limits, not a guarantee for arbitrary animation or contact. Rotation tests additionally exercise rest-state invariance, moving supports, pose inversion/composition and teleport velocity preservation.
