# Character01 — Art008 visual revision

## What this deliverable is

A complete static visual-asset revision of the replacement character: an editable Blender art master plus a baked PBR Blender copy, an embedded-texture GLB, texture images, authoring sources and actual rendered reviews. It is not the old milestone002 mannequin, and it does not inherit that older model's rig or physics acceptance.

Visual work addressed the body/neck/shoulder surface, muscle definition, unsupported separated chest form, face/eyes/brows/teeth, long hair, horns, ears, tail, markings, nails, loose neck-directed garment and waist cord. Garment construction does not move the body into a supported bra shape. The latest halter is a continuous independently editable neck-to-waist surface. The old disjoint cloth pieces and rejected hair filler remain hidden in the archive collection for editing history.

Artistic likeness is not proven by numerical checks. The six views and closeups are actual renders of the saved model. They should be judged directly against the user's latest anatomical direction and visual quality goal, not against old literal-silhouette rules.

## Exact editable master

- Repository / branch: andro951/YokaiDominion / art-checkpoints.
- Source revision: 9c869a359e9b0ac9fa91f984b5fd97e38f44984a.
- Immutable model commit: 980b464ba9ade3f4d72e279c981f38729e68490b.
- Path: art/checkpoints/finish008/9c869a359e9b/Character01_Finish008.blend.
- SHA-256: 3344fd9706024a8ee5f903472de93333191d78a8ec32c5759dc53467cf3a07e3.
- Bytes: 17,358,317.
- Workflow run: 43159974137.
- Archive artifact: 13916879601, art008-editable-and-review.
- Archive digest: d45d4197d1642bfef05a4f808f21af823e8b0ad726dce5d4d972c20cf06d78e2.

The model was committed before renders, downloaded at its immutable commit, hash/size checked and reopened in Blender. The artifact was independently downloaded into the chat container and checked again. All six Art007 cord-rounding edits remain present. Its individual source modules are included with the checkpoint; the base input is the pinned Cord007 file recorded in AGENTS.md.

## Exact portable textured asset

- Export source revision: e8a6f76486e9222b30e158823aee7f80da30b6a9.
- Immutable asset commit: 4bec672d1e7836dec2d0db141ff6236e3c722395.
- Directory: art/checkpoints/portable008/e8a6f76486e9/.
- Character01_PBR008.blend: 44,944,349 bytes; SHA-256 08239fda16dcc8ae3b82523ba28e806b3b3bd3535140e96dc0e3047cab8a1fd5.
- Character01_Visual008.glb: 40,972,612 bytes; SHA-256 bf422fa4e363f9eb4a04fbc2bb9cb306469fdcbba60123bccdd365203e0856f9.
- Workflow run: 43160875654, completed successfully.
- Archive artifact: 13917749813, art008-portable-files.
- Archive digest: 395aad2de1633c30857739531415f521e57199e9e991bdb943abcd951c71f5d2.

The GLB contains its textures; there are no external image or buffer URIs. It has 16 embedded images, 14 materials, 289 mesh objects and 511,676 triangles in total. The portable body has 67,746 vertices / 135,488 triangles; the high-resolution master body has 169,362 vertices. This is a high-detail visual asset, not an optimized MOBA LOD. A measured runtime budget and final production topology remain separate tasks.

All committed model and texture files were downloaded back from GitHub and checked against their byte counts and SHA-256 hashes. The GLB was reimported into Blender, rendered, downloaded and visually inspected. The final reimport retains the slate color and separate markings; earlier black-patch/streaked exports were rejected rather than treated as accepted deliverables.

Independent GLB audit: 300,250 vertices including attribute seams; finite positions/normals/UVs; all indices in bounds; zero normals outside a 1% unit-length tolerance; alpha-masked double-sided hair material; zero skins and zero animation clips. Body-bake coverage sampled 135,488 faces and found zero unbaked black samples under the defined test. This is a texture-integrity measurement, not a visual-quality score.

## Export problems found and corrected

1. The source anatomy has UVs across multiple UDIM tiles. Baking to a single PNG without repacking left black patches. The final exporter packs a single 0–1 atlas, then bakes 4K base color, normals and roughness.
2. UNSUBDIV damaged the low-resolution UV layout. The rejected mesh's summed UV triangle area was 16.63 in one tile, versus approximately 0.636 for the source. The final path uses UV/seam/material-delimited collapse with an area-preservation gate and full-resolution fallback if required. The actual final atlas area was 0.605854 for the source and 0.599258 for the portable body; all coordinates remain in the atlas.
3. All body maps are transferred from the intact high-resolution sculpt to the portable mesh. Generic attribute interpolation on a damaged reduced mesh is not accepted as a substitute.
4. Hair alpha is preserved explicitly and exported as MASK with cutoff 0.30. Procedural Blender-only shader detail is baked where needed.
5. A rear cloth opening initially selected a distal tail crossing and created a lateral spike. The final geometry uses the first root-side crossing, a bounded displacement and a rounded hem.

## Scope still not delivered by these new assets

- No replacement armature, skin weights, animation set, pose correctives, ragdoll or IK controller.
- No fitted tissue-region data or working soft-body/garment simulation on this replacement mesh.
- No target-PC GPU performance result or production LOD/draw-call budget.
- No claim that all engines will display every material identically.
- No claim of user-approved final likeness or a biological/anatomical simulation calibration.

The existing C# core remains in the repository, but the old milestone002 results belong to its old test asset. Do not erase that distinction.

## Recovering and continuing

Use the exact model and export paths above. Do not resume from the old art/current baseline or a rejected intermediate export. Read AGENTS.md for the mandatory 5–10-minute unfinished-work checkpoint procedure. Source is saved with direct text-file writes; actual binary assets are saved using ordinary Git in Actions and verified by download/readback. Models are pushed before preview renders.

Blender 4.5.3 LTS was used for authoring and validation. The art-master collections separate body, face, hair, garments, horns/tail, studio and archived components. Preserve the procedural master when making game-specific topology or rigging changes. Provenance is in THIRD_PARTY_ASSETS.md.
