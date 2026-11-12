# Development handoff

## Mandatory checkpoint method (user requirement; proven by Cord007)
During active work, save unfinished changes to GitHub every 5–10 minutes, targeting five minutes. Save before long renders. Do not wait for a milestone or final quality.

1. For small UTF-8 source files, use the connected GitHub create_file/update_file actions. Fetch the current blob SHA before an update and read the committed content back. Do not construct blobs/trees/refs for routine small updates.
2. For actual .blend, .glb, textures and previews, use ordinary Git on the GitHub Actions runner. Restore a pinned editable asset, execute the committed edit script, pack dependencies and save the .blend. Commit the real binary bytes to the existing art-checkpoints branch. Save the model BEFORE rendering; push that model immediately, then commit previews separately when ready.
3. Verify the asset branch commit exists. Download files at that immutable commit, compare SHA-256 and byte counts with the pre-upload manifest, then reopen the downloaded .blend in Blender. A saved script, local file, Git object or expiring Actions artifact alone does NOT count as a backed-up editable model.
4. Record source commit, asset commit, asset path/hash, known failures and next step. No force pushes. Use a unique checkpoint path so other work is not overwritten. Confirm success rather than assuming a queued workflow completed.

Proven implementation: .github/workflows/cord007-upload.yml and tools/art/cord_checkpoint007.py. Evidence: docs/checkpoints/cord007-upload-result.md. Cord007 source workflow commit 579a33ba410567bd5ffac651e590b8d4247a0120; successful run 43149344061. Actual editable model is at art/checkpoints/cord007/Character01_Cord007.blend on art-checkpoints, immutable asset commit 1f2e230192c93b3a9084ba759e023b34faa0476c, SHA-256 a10153251e3296d6055849bbdfc77db6cabe818a485ed19aabc84a5ddc155b3b. This is a post-processing edit of Art006; rebuilding only the older generator loses that cord edit. Check current heads before resuming, because newer checkpoints may exist.

This file is durable project memory, not a claim of guaranteed account-wide memory or autonomous background work.

## Current art decisions (supersede older literal-silhouette requirements)
The old mannequin body was rejected. The replacement uses Blender's CC0 realistic female anatomical base. Preserve believable adult anatomy, then fit the fantasy identity; do not distort shoulders or hips merely to counterbalance breast size. Latest explicit user corrections override older instructions to copy the original silhouette exactly.

The character is tall and muscular, with large but naturally hanging, separated and outward-oriented breasts and substantial glutes. Build unsupported body form first; loose clothing must not lift, squeeze or center the breasts. Only the waist cord is tight. Upper cloth panels converge diagonally from each breast toward the neck, not vertically over the shoulders. Neck/trapezius/clavicle/deltoid forms need natural slope and curvature, not a horizontal shelf. Two upper rows of abs should read, with the upper row partly obscured by breast mass and the lower row partly by the outfit. Strong muscle definition without arbitrary lumps. Original illustration and turnaround guide identity, colors, outfit, hair/horns/face; coherent 3D anatomy governs construction. The character is not named Astra by user approval.

Finish the actual visual asset, not another testing mannequin. Inspect front/side/back/three-quarter/portrait renders. Do not label artistic quality complete on the strength of code compilation or numerical tests.

## Architecture and permissions
C# is strongly preferred. Godot .NET is the initial host; Blender authors editable assets; the tissue core is portable C#. User authorizes work in andro951/YokaiDominion and andro951/YokaiDominionTesting. Develop character and tissue data together, but current priority is visual likeness. Keep useful runtime infrastructure; don't let old rigs or coarse tissue cages dictate the new body. Testing repo pins production revisions rather than copying the solver.

## Recovery and validation
Read current checkpoint notes, inspect the saved .blend and source at exact revisions, and preserve user changes. Full-resolution references remain conversation attachments; verify their roles and hashes. Existing milestone-002 rig/physics results apply to that old asset only, not automatically to a rebuilt art master. Do not claim rigging, game-ready topology, material baking, garment coupling, calibrated flesh response, full contact or target-GPU performance unless separately implemented and tested.

Local runtime capabilities vary. Blender was successfully recovered from a previously verified tool archive and used locally in Cord007; GitHub Actions also ran Blender and ordinary Git. Test current capabilities instead of repeating earlier environment assumptions. No work continues after a response unless an explicitly created automation or submitted external job is identified as such.
