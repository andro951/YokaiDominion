# Character prototype review log

## dcc7e539: integration passes, quality rejected
The actual Blender/Godot character pipeline completed, including skeleton/morph sampling, visible tissue displacement and physics-off fallback. That was an integration result, not a quality acceptance.

Independent exported-skin audit and real overhead renders revealed residual large stretches (99.9th percentile about 41x in overhead). Distal hand and forearm vertices incorrectly retained pelvis/spine weights. Truncating unrelated influences made discontinuities worse. The jump fixture also reached 25.5% local breast-cage volume change and 0.319 m surface displacement, far above the proposed volume target. These results remain failures to improve, not realistic flesh.

The following revision replaces nearest-bone mixtures on the body with anatomically limited two-bone chains, makes distal arms fully follow arm bones, aligns limb roll axes, and fixes world-vs-local root translation in authored crouch/jump poses. The original image's head-to-bust and bust-to-hip proportions motivate lowering/reducing the first excessively high/tall bust geometry, without normalizing away the approved exaggerated design. Fitted cages and draped chest panels change with that geometry. Numerical settings are now explicit data and can be independently swept.

Outstanding: dedicated finger weights, twist distribution, anatomical retopology, accurate face/hair design, pose-dependent contact, full garment restraint and anatomically fitted constitutive response. Eight sampled pose import checks are not full-body movement certification.
