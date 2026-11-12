# YokaiDominion

C#-first character/game project: Godot .NET, Blender authoring, and an engine-independent C# volumetric tissue core.

## Latest character: Art008 visual master

The replacement character now has an editable visual master and a verified textured portable export. These are actual committed binary assets on **`art-checkpoints`**, not only scripts or expiring Actions artifacts.

- **Editable art master:** `art/checkpoints/finish008/9c869a359e9b/Character01_Finish008.blend`
- **Portable baked-material Blender copy:** `art/checkpoints/portable008/e8a6f76486e9/Character01_PBR008.blend`
- **Embedded-texture GLB:** `art/checkpoints/portable008/e8a6f76486e9/Character01_Visual008.glb`
- **Textures:** the `textures/` directory beside that GLB.

Switch GitHub's branch selector from `main` to **`art-checkpoints`** to see those files. Source scripts remain on `main`. Exact immutable asset commits, hashes, sizes, validation runs and limitations are in [CHARACTER_ART008.md](docs/CHARACTER_ART008.md).

The visual pass includes anatomical surface refinement, face/eyes/brows/teeth, sloping muscular neck/shoulder transitions, defined musculature, independently draped continuous halter fabric, the preserved braided cord, layered long wavy hair with strand-opacity detail, horns, ears, tail, markings and material finish. It follows the user's later anatomy-first directions rather than reproducing the rejected mannequin's exaggerated proportions.

**This replacement is a static visual asset. It does not yet have its replacement animation rig, skin weights, tissue-region refit or physics integration.** The GLB has zero skins and zero animations. The older milestone002 rig/physics results below must not be attributed to this new model. Artistic likeness should be judged from the actual saved model and views; successful export checks are not proof of final user-approved art quality.

## Verified visual-asset delivery

The editable master is 17.4 MB; its source revision is `9c869a359e9b0ac9fa91f984b5fd97e38f44984a` and its immutable binary commit is `980b464ba9ade3f4d72e279c981f38729e68490b`.

The portable files were produced by source `e8a6f76486e9222b30e158823aee7f80da30b6a9`, successful run `43160875654`, and committed at `4bec672d1e7836dec2d0db141ff6236e3c722395`. Every committed model/texture file was downloaded back and hash/size verified. The GLB was reimported, rendered and visually inspected. It contains its textures, including the 4K body maps, without external image or buffer URIs.

This is a high-detail visual asset: 511,676 total triangles, 14 materials, 289 mesh objects and 16 embedded images. The portable body is 135,488 triangles. Production LODs, draw-call consolidation and target-machine performance remain separate work, not implied by the word portable.

## Current reference and anatomy direction

The user's latest corrections take precedence over the earlier literal-silhouette contract. Build believable adult anatomy first. Keep naturally hanging, separated, outward-oriented breasts, a strong muscular body and substantial glutes; do not widen the skeleton merely to counterbalance breast volume. Only the waist cord is tight. The loose upper fabric angles toward the neck and does not lift or squeeze the body. Shoulders slope from muscular neck/trapezius into rounded deltoids; two upper abdominal rows remain readable.

The original illustration and turnaround guide identity, colors, fantasy details and outfit. The current model is not an approved replacement reference. The sheet's Astra label is not a user-approved character name; use Character01 internally.

## Existing C# runtime and historical milestone002

`src/Yokai.Tissue/` is portable C# without Godot dependencies. `game/` contains the earlier numerical laboratory and morph/skin/tissue reference integration. These remain usable engineering work, but their character mesh was superseded artistically.

Historical runtime instructions are in [RUN_CHARACTER.md](docs/RUN_CHARACTER.md), with evidence in [milestone-002.json](docs/evidence/milestone-002.json). That earlier asset had 176 exported joints, eight diagnostic poses and four tissue cages. Its 27 general numerical checks passed on Windows/Linux at `409ae5f`, run `42973868017`; its measured jump behavior was not anatomically calibrated flesh. Shoulder stretching, contact and locomotion limitations are recorded in the historical reports. Do not treat the old diagnostic animations as a complete motion set for the replacement.

The existing runtime baseline uses Godot 4.7.2 .NET / .NET 10. Art008 authoring and import checks used Blender 4.5.3 LTS. The companion YokaiDominionTesting repository pins exact production revisions rather than copying the solver.

## Provenance

The active rebuilt body derives from Blender's official CC0 Human Base Meshes v1.4.1 realistic female asset, not from the old MakeHuman prototype. Fantasy details, garment/groom shaping, textures and integration work are project additions. Original topology/sculpt provenance and the older model's separate license history are documented in [THIRD_PARTY_ASSETS.md](docs/THIRD_PARTY_ASSETS.md).

## Mandatory saving policy

Read [AGENTS.md](AGENTS.md) before working. During active editing, checkpoint unfinished changes every **5–10 minutes**, targeting five, and before long renders. Small text changes use direct Contents API create/update with the current file SHA and readback. Actual binary assets use ordinary Git in Actions, are pushed **before rendering**, then downloaded at immutable commits, hash-checked and reopened. A local save or source-only commit is not a saved model.

Keep unique checkpoint paths, preserve user work, avoid force pushes, and record failures as failures. Do not commit credentials or toolchain/font files. No autonomous modeling continues after a response ends.
