# Development handoff

## Current character checkpoint — read first
The retained breast/top visual revision is **Art013**, documented in `docs/CHARACTER_ART013.md` and `docs/ART013_VISUAL_REVIEW.md`. Art011 was explicitly rejected for excessive separation, too-low attachment and horizontal projection. Do not restore it as the current model. The interrupted Art012 reconstruction/drape was recovered from GitHub and refined into Art013.

Current actual master on `art-checkpoints`: immutable binary-save commit `25dcf94c1c583894ea6868d61cc976100f5a9004`, path `art/checkpoints/art013/705063316f9f/Character01_Art013.blend`, SHA-256 `b3b17ad6fd91a210d231058fe7229e3308e5539d76bc1a58b7e9e4ccbab6aa66`. Verified PBR Blender/GLB: commit `38edb00f0bb1e0c228c89b5af3a5d9f26e105f56`, directory `art/checkpoints/portable013/98ac3d6ed90a/`. Check current heads for later work before editing. These remain static visual assets, not newly rigged or physics-integrated characters. Modeler review is not user approval.

Latest anatomical corrections: keep intended large size, reduce excessive lateral displacement, raise and blend the upper attachment without lifting the whole mass, and distribute fullness downward into a hanging lower contour rather than pushing it straight forward. Preserve the rest of the body. Latest top instruction: cloth goes naturally **over the upper trapezius**, with only its inner edge beside the neck. No throat band, horseshoe collar or bra-like support. The approved generated full-body image is a reference only, never evidence of mesh changes. No paid AI generation without new authorization; the user rejected paying for fal.

## Mandatory visual review
The user requires actual screenshots from multiple angles while editing and an explicit comparison: does this look better than before? Use `tools/art/review013.py`, which fixes cameras, lighting, background, color management, render seed and framing and records hashes. Front/quarter/side/shoulder/full and optional cropped body-only views are available. Compare the same angles/settings; inspect actual images and reject regressions. Do not substitute generated images or declare artistic completion because code/export checks pass.

## Mandatory checkpoint method (user requirement; proven by Cord007)
During active work, save unfinished changes to GitHub every 5–10 minutes, targeting five minutes. Save before long renders. Do not wait for a milestone or final quality.

1. For small UTF-8 source files, use the connected GitHub create_file/update_file actions. Fetch the current blob SHA before an update and read the committed content back. Do not construct blobs/trees/refs for routine small updates.
2. For actual .blend, .glb, textures and previews, use ordinary Git on the GitHub Actions runner. Restore a pinned editable asset, execute the committed edit script, pack dependencies and save the .blend. Commit the real binary bytes to the existing art-checkpoints branch. Save the model BEFORE rendering; push that model immediately, then commit previews separately when ready.
3. Verify the asset branch commit exists. Download files at that immutable commit, compare SHA-256 and byte counts with the pre-upload manifest, then reopen the downloaded .blend in Blender. A saved script, local file, Git object or expiring Actions artifact alone does NOT count as a backed-up editable model.
4. Record source commit, asset commit, asset path/hash, known failures and next step. No force pushes. Use a unique checkpoint path so other work is not overwritten. Confirm success rather than assuming a queued workflow completed.

Proven implementation: .github/workflows/cord007-upload.yml and tools/art/cord_checkpoint007.py. Evidence: docs/checkpoints/cord007-upload-result.md. Cord007 source workflow commit 579a33ba410567bd5ffac651e590b8d4247a0120; successful run 43149344061. Actual editable model is at art/checkpoints/cord007/Character01_Cord007.blend on art-checkpoints, immutable asset commit 1f2e230192c93b3a9084ba759e023b34faa0476c, SHA-256 a10153251e3296d6055849bbdfc77db6cabe818a485ed19aabc84a5ddc155b3b. This is a post-processing edit of Art006; rebuilding only the older generator loses that cord edit. Check current heads before resuming because newer checkpoints exist. The Art013 workflows extend the same verified binary-save method.

This file is durable project memory, not a claim of guaranteed account-wide memory or autonomous background work.

## Current art decisions (supersede older literal-silhouette requirements)
The old mannequin body was rejected. The replacement derives from Blender's CC0 realistic female anatomical base. Preserve believable adult anatomy, then fit the fantasy identity; do not distort shoulders or hips merely to counterbalance breast size. Latest explicit user corrections override older instructions to copy the original silhouette exactly.

The character is tall and muscular, with large but naturally hanging breasts and substantial glutes. Separation must not become a broad channel or lateral displacement. Build unsupported body form first; loose clothing must not lift, squeeze or center the breasts. Only the waist cord is tight. Upper panels run over the upper trapezius, not directly into a throat collar. Neck/trapezius/clavicle/deltoid forms need natural slope and curvature, not a horizontal shelf. Two upper rows of abs should read, with the upper row partly obscured by breast mass and the lower row partly by the outfit. Strong muscle definition without arbitrary lumps. Original illustration, turnaround and subsequently approved image guide identity, colors, outfit, hair/horns/face; coherent 3D anatomy governs construction. The character is not named Astra by user approval.

Finish the actual visual asset, not another testing mannequin. Inspect front/side/back/quarter/portrait renders. Do not label artistic quality complete on the strength of code compilation or numerical tests.

## Architecture and permissions
C# is strongly preferred. Godot .NET is the initial host; Blender authors editable assets; the tissue core is portable C#. User authorizes work in andro951/YokaiDominion and andro951/YokaiDominionTesting. Develop character and tissue data together, but current priority is visual likeness. Keep useful runtime infrastructure; don't let old rigs or coarse tissue cages dictate the new body. Testing repo pins production revisions rather than copying the solver.

## Recovery and validation
Read current checkpoint notes, inspect the saved .blend and source at exact revisions, and preserve user changes. Full-resolution references remain conversation attachments; verify roles and hashes. Existing milestone-002 rig/physics results apply to the old asset only, not automatically to a rebuilt art master. Do not claim rigging, game-ready topology, material baking, garment coupling, calibrated flesh response, full contact or target-GPU performance unless separately implemented and tested.

Local runtime capabilities vary. Blender was recovered from a verified tool archive and used locally in Cord007, Art011 and Art013; GitHub Actions also ran Blender and ordinary Git. Test current capabilities instead of repeating earlier environment assumptions. Avoid concurrent Blender processes in a 4 GB container. No work continues after a response unless an explicitly created automation or submitted external job is identified as such.
