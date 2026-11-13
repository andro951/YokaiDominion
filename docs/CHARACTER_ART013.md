# Character01 Art013 — reviewed breast and upper-garment correction

## Scope and visual decision

This revision addresses the user's rejection of Art011: excessive central separation, too-low/abrupt attachment, forward projection without a convincing hanging lower mass, and stiff cloth. The interrupted session's Art012 reconstruction and drape were recovered from committed binaries, not lost or replaced by the old mannequin. Art013 refines that recovered body and garment. No paid model generator or generated-image substitute was used.

The retained revision is `013-contour-drape-2`. Compared with the rejected Art011, the upper chest connection starts higher and runs into a longer upper slope, the center gap is reduced, and the lower fullness hangs below the attachment rather than projecting as a horizontal bulb. The current pass redistributes the recovered contour locally, with a maximum displacement of 6.22 mm; the major reconstruction is inherited from Art012, not falsely attributed to that small displacement. The body remains large rather than being shrunk to hide the problem.

The independently editable top follows the corrected body and crosses the upper trapezius, leaving the throat open. It has no horseshoe collar, cups or lifting band. Fairing removes the relaxed cloth's sharp scalloped ripples; broad longitudinal folds replace the too-smooth first Art013 pass. Only the waist cord is cinched. Shoulders and hips were not widened to accommodate the breasts.

Actual front, quarter, side, shoulder and full views were inspected. The retained result is a modeler-reviewed localized correction, not user approval or a claim that the whole character is finished. See `ART013_VISUAL_REVIEW.md` for the rejected/retained pass decisions.

## Standard screenshot script

`tools/art/review013.py` opens a saved Blender file, replaces inherited lights with a fixed area-light setup, hides studio background meshes, fixes world, exposure, color transform and render seed, and renders named camera views. Front/quarter/side/shoulder/full/back are available; tightly cropped body-only views allow anatomy inspection before cloth.

Example:

    blender -b -t 4 --python-exit-code 1 --python tools/art/review013.py -- --source Character01_Art013.blend --out review --shots front,quarter,side,shoulder,full --width 800 --samples 32

It does not overwrite the source model. Its `review-manifest.json` records the input model hash, exact camera/light settings, resolution, sample count and output-image hashes. Before/after comparisons must use the same script/settings, not different flattering angles or image generation.

## Recover the exact editable master

Repository: `andro951/YokaiDominion`; branch: `art-checkpoints`.

- Source revision: `705063316f9f3ec4b1b20fae3020a5748483a62b`.
- Immutable binary-save commit: `25dcf94c1c583894ea6868d61cc976100f5a9004`.
- File: `art/checkpoints/art013/705063316f9f/Character01_Art013.blend`.
- Bytes: 79,416,422.
- SHA-256: `b3b17ad6fd91a210d231058fe7229e3308e5539d76bc1a58b7e9e4ccbab6aa66`.
- Successful save/download/reopen/review run: `43339640520`.
- Convenience artifact: `13999406073`, `art013-master-and-review`.
- ZIP SHA-256: `42072cff445978f75b8eb8a4c1a61d737f3f1fa278c544771b1c92c02846d693`.

The master contains 825,304 body vertices. Art013 changed 76,768; all 680,787 protected vertices were preserved exactly. The high count is inherited from the Art012 reconstruction and is not an optimized game budget. The final source script refuses applying the same pass twice.

## Recover the actual portable export

- Export source: `98ac3d6ed90a413e3bf4eef75deb2083e9033133`.
- Immutable binary-save commit: `38edb00f0bb1e0c228c89b5af3a5d9f26e105f56`.
- Directory: `art/checkpoints/portable013/98ac3d6ed90a/`.
- `Character01_PBR013.blend`: 28,887,520 bytes; SHA-256 `39cee47abe223f4b9368e846d9ee36573fe30746ebd0ecd7052aa9e579a3f5bf`.
- `Character01_Visual013.glb`: 66,956,844 bytes; SHA-256 `a6bc11acbb2e558304903cecd89e39f9e5659c570f416b464556d68c78a63d5c`.
- Successful export/download/reopen/reimport/render run: `43340070848`.
- Artifact: `13998534683`, `art013-portable-verified`.
- ZIP SHA-256: `4ba867662ab83730356e79328a59a1bb4cc84cb624cba42df8f836afb7b3f453`.

The portable body has 181,565 vertices; the complete model has 948,194 triangles. The existing baked vertex albedo was preserved byte-for-byte, and the actual corrected garment meshes were imported from the master. The GLB embeds its image data. The master is the detailed editing authority; portable markings are softer than the procedural master because the portable asset inherits baked vertex colors.

## Observed verification

Both workflows saved actual binaries before rendering. They downloaded each file at its immutable asset commit, compared SHA-256 and size, reopened the Blender files, and rendered the saved geometry. The portable workflow reimported and rendered the actual remotely downloaded GLB. Front/quarter/side export views were inspected for retained shape and materials.

Both artifact ZIP hashes and every master/PBR/GLB file hash were independently checked in the chat container. The remotely saved master and PBR file reopened locally in Blender 4.5.3 LTS. Body positions were finite; expected Art013 garment objects and revision tags were present; no file-backed image dependencies were missing. The protected master positions were independently compared with `art013_previous_position` and were unchanged.

Numerical integrity and export checks do not establish likeness or realistic dynamic tissue behavior. Visual decisions are based on the actual matched renders, not on those checks alone.

## What is not part of this pass

This is a static visual asset. There is no new rig, skin weighting, animation set, dynamic cloth, refitted C# tissue simulation, validated collision system or production LOD. The previous mannequin's rig/physics tests do not validate this rebuilt mesh. No full-character artistic acceptance is implied for the existing face, hair, hands or other unrelated features.

## Saving and continuing

Resume from the exact Art013 master above, not Art008/011. Preserve the proven method in `AGENTS.md`: small text through Contents create/update; actual model binaries through ordinary Git in Actions; unique checkpoint paths; save before long renders; verify remote bytes and reopening; no force pushes. During active editing, checkpoint unfinished work every 5–10 minutes. A source-only commit or expiring workflow artifact is not a substitute for the committed editable model.
