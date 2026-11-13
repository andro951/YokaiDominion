# Art014 actual-mesh face review

## Scope
The user requested work on the actual 3D jaw and cheeks after another image-generation response. No image generator or paid 3D generator is used for this revision. Start from the retained Art013 body. This is a face-only mesh correction, not a new body design or a general claim of production-ready character quality.

## Repeatable evidence
`tools/art/review014.py` extends the fixed lights and world from `review013.py` with close-up face-front, face-quarter, face-side and opposite-quarter views. Every comparison keeps camera, framing, lighting, exposure, transform and render seed fixed. Draft reviews used 600 pixels / 16 samples; delivery comparisons use 800 pixels / 32 samples on both sides. Generated concept images are not completion evidence.

## Observed iterations
- Art013 baseline: broad flat chin, hard lower-face corners, pronounced diagonal cheek-to-lower-cheek transition. In profile the chin/under-jaw line is nearly flat and blocky.
- Pass 1: jaw narrowing alone made the face look pinched while retaining harsh cheek transitions. Rejected as a delivery result; the unfinished model was still checkpointed.
- Pass 2: more local cheek padding and contour changes did not sufficiently unify the cheek surfaces. Rejected in favor of broader fairing rather than stacking more localized bulges.
- Pass 3: broad constrained cheek fairing removed much of the sharp transition, but the side view showed a recessed chin. Rejected for profile balance even though the cheek area improved.
- Retained pass 4 (`014-face-4`): reduce chin retreat and chin smoothing, retain rounded corners and a tapered lower-face outline, keep the gentler cheek transition. Reviewed in front, quarter and side; no new body/clothing reshaping was used to produce the result.

The retained pass is a modeler-reviewed improvement to the requested areas, not user approval or an exact reproduction of a generated reference. It does not imply completion of unrelated eye design, hair-groom quality, materials, animation, physics or optimization.

## Integrity checks
An independent saved-file comparison (`tools/art/audit014.py`) checks actual loaded geometry rather than trusting edit metadata. It asserts that every body vertex outside the facial region is exactly unchanged, that all other mesh-object positions/topology/UVs/colors/material assignments/transforms/render visibility are unchanged, and that body topology, UVs, color layers and material assignments survive. Master and portable files are checked separately.

The portable export transfers the actual finalized face displacement including fairing; it does not merely re-run the initial proportional deformation and omit the sculpt smoothing. Existing vertex albedo is retained. Actual GLB reimported portrait renders are checked separately from master renders.

## Save/recovery method
Keep source and unfinished model checkpoints. Actual Blender and GLB bytes are committed to `art-checkpoints` using ordinary Git on the Actions runner before long renders. The runner downloads files at their immutable asset commits, verifies SHA-256/size and reopens Blender. Read the final manifest and readback file for exact binary identities; a source commit alone is not a backed-up model.
