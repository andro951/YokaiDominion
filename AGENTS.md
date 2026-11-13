# Development handoff

## Current character checkpoint — read first
The retained actual character is **Art014**, documented in `docs/CHARACTER_ART014.md` and `docs/ART014_VISUAL_REVIEW.md`. It corrects the jaw and cheeks of Art013 while preserving its body and clothing. It is a modeler-reviewed revision, not user approval or full-character final acceptance.

Current master on `art-checkpoints`: immutable binary commit `1e3649e9c8683a51ece6dfdaf3639a3198a8f118`, file `art/checkpoints/face014/006503bbc6a8/Character01_Art014.blend`, SHA-256 `347c10d42c2b73eae6ffee8e5d7d79fe0b5cc169b11a417c6bfdda07865bac0a`.

Current textured Blender/GLB: immutable binary commit `530c5a59b2318c7a3fc95581395cb6f61c2b5113`, directory `art/checkpoints/portable014/f4caa2b25ed0/`. Check current heads for later work before editing. These remain static high-detail visual assets, not newly rigged or physics-integrated characters.

The body/garment foundation is Art013 (`docs/CHARACTER_ART013.md`). Art011 was rejected for excessive separation, low attachment and horizontal projection. Do not restore it as the current model. Art014 preserves the Art013 body and garment; do not remake those during a face-only task.

## Actual model versus concept images
When the user requests an edit to the actual 3D model, modify and deliver the Blender/GLB geometry. **Do not respond with image generation instead.** This error occurred twice and the user explicitly objected. A generated picture can only be a separately identified concept/reference when that is what the user requests; it never proves mesh changes.

No paid AI generation without new authorization; the user rejected paying for fal. The character is not named Astra by user approval.

## Mandatory visual review
The user requires actual screenshots from multiple angles while editing and comparison: does this look better than before? `tools/art/review014.py` adds fixed face-front/quarter/side views to `review013.py`. The review fixes cameras, lighting, background, color management, render seed and framing and records hashes. `review013.py` retains front/quarter/side/shoulder/full/back and cropped body-only views for body work.

Compare the same angles/settings; inspect the actual images; reject regressions. Art014 narrowing-only and over-recessed-chin variants were rejected before retaining pass 4. Do not declare artistic completion because code or export checks pass. Review the reimported GLB as well as the master.

## Mandatory checkpoint method — proven by Cord007 and subsequent revisions
During active work, save unfinished changes to GitHub every 5–10 minutes, targeting five. Save before long renders. Do not wait for a milestone or final quality.

1. Small UTF-8 source files: use connected GitHub create_file/update_file actions, obtain current blob SHA before updating and read committed content back. Do not construct blobs/trees/refs for routine small updates.
2. Actual .blend, .glb, textures and previews: use ordinary Git on the GitHub Actions runner. Restore the pinned editable asset, execute the committed edit script, pack dependencies and save. Commit actual binary bytes to existing `art-checkpoints`, at unique paths. Save/push the model BEFORE rendering; commit previews separately afterward.
3. Verify the asset commit exists. Download files at that immutable commit, compare SHA-256 and byte counts against the pre-upload manifest, then reopen the downloaded Blender file. A source-only commit, local file, Git object or expiring Actions artifact alone is not a backed-up editable model.
4. Record source commit, asset commit, path/hash, known failures and next step. No force pushes. Use fetch/rebase/retry and unique paths for concurrent saves. Confirm success rather than assuming a queued workflow completed. Avoid allowing a long render to hold up the next editable-model save.

Proven initial implementation: `.github/workflows/cord007-upload.yml` and `tools/art/cord_checkpoint007.py`; evidence `docs/checkpoints/cord007-upload-result.md`, successful run `43149344061`. Current implementations: `art014-checkpoint.yml` and `portable014.yml`. This is durable project documentation, not a claim of guaranteed account-wide memory or asynchronous modeling.

## Art direction retained from the user's corrections
Anatomy first, fantasy identity second. The old mannequin was rejected. The replacement derives from Blender's CC0 realistic female base. Latest explicit user corrections supersede older literal-silhouette instructions. Do not widen shoulders/hips to counterbalance breast size.

Keep the intended large breast size, reduce excessive lateral displacement, blend the upper attachment without lifting the whole mass, and let lower fullness hang rather than project horizontally. Separation must not become a broad channel. Shape unsupported body form first. Loose clothes must not lift, squeeze or center it. Only the waist cord is cinched.

The top passes naturally over the upper trapezius, with only the inner edge beside the neck. No throat band, horseshoe collar or bra-like cups/support. Neck/trapezius/clavicle/deltoid transitions need slope and curvature, not a shelf. Two upper abdominal rows remain readable. Preserve strong musculature without arbitrary lumps. Original illustration, turnaround and approved later reference guide identity/palette/details, not a forced impossible silhouette.

For the face, preserve adult identity and a strong but smoother lower-face structure. Do not simply narrow the jaw until it is pinched, hollow the cheeks, or remove chin projection. Preserve unrelated geometry and use fixed front/quarter/profile comparisons.

## Architecture, provenance and verification
C# is strongly preferred. Godot .NET is the initial host; Blender authors editable assets; the tissue core is portable C#. User authorizes work in `andro951/YokaiDominion` and `andro951/YokaiDominionTesting`. The testing repository pins production revisions rather than duplicating the solver. Keep useful runtime infrastructure but do not let old rigs/tissue cages dictate new anatomy.

Read exact checkpoint notes and source before editing; preserve user changes. The original image and turnaround are references, not renders of the final mesh. Existing milestone002 rig/physics results apply only to that older asset. Do not claim new rigging, game-ready topology, animation, realistic tissue response, garment contact or target-GPU performance without separately implementing and testing it. Preserve upstream CC0 provenance and license in packages.

`tools/art/audit014.py` independently verifies protected body positions and other mesh objects, topology/UV/color/material assignments after loading the saved files. Geometry integrity is not artistic acceptance.

Local capabilities vary. A checksum-verified Blender archive has successfully run in the chat container; GitHub Actions supplies ordinary Git and Blender. Test capabilities rather than repeating earlier assumptions. Avoid concurrent heavy Blender processes in a 4 GB container. No work continues after a response except explicitly identified submitted external jobs or authorized automations.
