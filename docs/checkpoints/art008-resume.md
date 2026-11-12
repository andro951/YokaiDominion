# Art008 recovery and visual-asset work

## Durable checkpoint policy
The proven saving method and the user's five-to-ten-minute cadence are in root AGENTS.md. Small sources use direct Contents API updates with current blob SHAs. Actual model/texture/preview bytes use normal Git in Actions, on art-checkpoints. Model bytes are pushed before preview rendering, then downloaded at the immutable asset commit, hash-checked and reopened in Blender. Source-only commits do not count as a backed-up editable model.

## Verified complete editable source (before the newer fibre refinement)
- Source: b2af9b1add70e8a9657cb599d866cc39a5af764f.
- Workflow run: 43155434870, completed successfully.
- Asset commit: 3e295fdd736a2ad70f812e894c984d227e323936.
- Asset branch path: art/checkpoints/finish008/b2af9b1add70/Character01_Finish008.blend.
- SHA-256: 235c3e4d408f4d56c1b36105a8bdd7faaeff9f0ce07375bd4f5ac24217a4e71b.
- Size: 15,896,929 bytes.
- Artifact: 13916390075, art008-editable-and-review. Archive digest cd869fd430331cf589cd8d907f7ee2c0167279c093b57c04effe314185991362.

The model was independently downloaded and its hash checked in the chat container. The front, side, back, three-quarter, torso and portrait renders are actual Blender renders. The new master preserves Cord007 cord edits. It has new face, local muscle definition, skin variation, an independently constructed continuous loose halter, repaired rear cloth/tail opening, layered hair, pointed markings, materials and organized editable collections.

## Newer saved or running revisions
The hair-fibre source is tools/art/hair008.py. The 008-hair-9 master is already committed under art/checkpoints/finish008/860b56fcf2d4/ with SHA-256 bccc85ed6b12985d0046baef8956f2be2c9d2ab2d3ea868c77546ad71d4700ca (16,367,380 bytes); its final visual review is not recorded here yet.
The next driver source is 43885097653792668cb1dd3cab82519510d54d60, adding tools/art/face009.py for fitted individual eyebrow hairs and softer continuous facial planes. Confirm its workflow and corresponding asset manifest before calling that revision verified.

## Rejected intermediate output
The ccb035f720d2 contour pass had an incorrect tail opening: a nearest-Y search chose the distal tail loop, stretching the rear cloth sideways. The corrected implementation uses the first root-side crossing and limits displacement. Do not deliver the rejected geometry.
The first PBR export at source 8598fb47f763067f2f4eee573e6ff36ee5881089 completed structurally but had black patches because the body uses multiple UDIM tiles and only one image was baked. Its successful workflow was NOT visual acceptance. The replacement repacks the UV islands into tile1001, transfers sculpt normals, checks baked surface coverage, and must be reimported and visually reviewed. A stale UV RNA reference after edit mode was fixed by reacquiring the UV layer. Fast bounded AABB island packing was separately checked locally. Do not label the portable export ready until the final output passes review.

## Scope boundary
These new files are a static visual art master and a static portable PBR export. They do not yet contain the finished replacement rig, animation set, tissue region refit, clothing physics or ragdoll. Old milestone002 numerical/rig results belong to the old model and are not acceptance for this rebuilt master. Keep the original reference identity and the user's later natural unsupported anatomy corrections; do not restore the rejected oversized centered breast or shelf-shoulder geometry.

## Next recovery action
Read the latest source head, finish008 driver/module list, the matching asset manifest and remote-readback record. Review the actual current model images. Finish the latest fibre/portrait review and corrected portable export. Update this note with final exact hashes rather than relying on temporary local paths. No asynchronous modeling is implied.
