# Progress — Art008 visual asset handoff

## Current asset and scope

The active replacement character is the Art008 static visual master, source `9c869a359e9b0ac9fa91f984b5fd97e38f44984a`, derived from the official Blender CC0 realistic female base. The earlier milestone002 mannequin and its rig are not the active art foundation. The user's anatomy-first corrections supersede old literal-silhouette instructions.

Work now covers the actual body/neck/shoulder surface, muscle definition, face/eyes/brows/teeth, separated unsupported chest form, continuous loose neck-directed halter, front/back cloth, braided cord, long wavy hair and fibre detail, horns, ears, tail opening, markings, nails and material variation. Source changes and actual .blend bytes were checkpointed repeatedly. The old Cord007 cord edits survive in the replacement.

This handoff is a complete static visual revision, not a claim of user-approved final likeness, a production MOBA LOD, or a newly rigged/physically simulated character. The current exported GLB has zero skins and zero animation clips. Full art/game acceptance must not be inferred from structural export success.

## Resume from these exact files

All binary files below are normal Git commits on `art-checkpoints`, not merely expiring Actions artifacts.

Editable master:
- Commit: `980b464ba9ade3f4d72e279c981f38729e68490b`.
- File: `art/checkpoints/finish008/9c869a359e9b/Character01_Finish008.blend`.
- SHA-256: `3344fd9706024a8ee5f903472de93333191d78a8ec32c5759dc53467cf3a07e3`.
- Size: 17,358,317 bytes.
- Successful authoring/save/readback/render run: `43159974137`.

Portable PBR files:
- Source: `e8a6f76486e9222b30e158823aee7f80da30b6a9`.
- Asset commit: `4bec672d1e7836dec2d0db141ff6236e3c722395`.
- Directory: `art/checkpoints/portable008/e8a6f76486e9/`.
- GLB: `Character01_Visual008.glb`, SHA-256 `bf422fa4e363f9eb4a04fbc2bb9cb306469fdcbba60123bccdd365203e0856f9`, 40,972,612 bytes.
- Baked Blender copy: `Character01_PBR008.blend`, SHA-256 `08239fda16dcc8ae3b82523ba28e806b3b3bd3535140e96dc0e3047cab8a1fd5`, 44,944,349 bytes.
- Successful export/readback/reimport/render run: `43160875654`.

Full measured evidence and known limitations: `CHARACTER_ART008.md`. Source modules are under `tools/art/`. The authoring driver `finish008.py` applies the committed visual changes to the pinned complete Cord007 asset. Do not accidentally start from the older `art/current` file and lose later work.

## Observed verification

- Actual master saved, committed before rendering, downloaded at immutable commit, hash/size matched and reopened in Blender.
- Six view renders downloaded and inspected: front, side, back, three-quarter, portrait, torso.
- Actual GLB, PBR .blend and all texture files committed, downloaded back and hash/size checked.
- GLB reimported and rendered; the current export retains slate skin color and separate markings rather than the black patches or smeared colors of rejected intermediate exports.
- Independent binary audit: finite positions/normals/UVs, all mesh indices in bounds, all normals within 1% of unit length, embedded images/buffer without external URIs, alpha-masked strand material.
- High-resolution master body: 169,362 vertices. Portable body: 67,746 vertices / 135,488 triangles. Complete export: 511,676 triangles, 14 materials, 289 meshes, 16 embedded images. This remains a high-detail presentation asset, not a measured production runtime budget.
- The final atlas is within 0–1. Source summed UV triangle area 0.605854, portable 0.599258. Color-coverage test samples 135,488 faces with zero unbaked black samples under the defined threshold. This is not a likeness score.

## Rejected intermediate work

The ccb035f720d2 contour model had a rear garment spike caused by selecting a distal tail crossing. The final code uses the first root-side crossing, bounds displacement and adds a rounded hem.

The first single-image export failed visually because the source body uses UDIMs. Repacking resolved black regions, but a subsequent UNSUBDIV reduction corrupted UVs: summed UV area reached 16.63 in one tile. That output was also rejected despite passing a simplistic nonblack-coverage check. The final exporter uses UV/seam/material-preserving collapse, verifies UV area, has a full-resolution fallback, and transfers all maps from the intact sculpt. Do not deliver those earlier portable directories as current.

Earlier hair/brow revisions were also superseded. The latest model has continuous long rooted back waves rather than the old flat filler/stepped fringe; ivory brows retain a low-profile undercoat plus individual hairs, rather than disappearing when the old raised strips were hidden.

## Remaining separate game/physics work

The replacement needs its own deformation rig, skin weights, pose corrections, motion set, tissue region fitting, supported rest-state calibration, garment/body contact, hair/cloth runtime behavior and performance/LOD work. These are not silently completed by importing the visual GLB.

The existing engine-independent C# solver and Godot laboratory remain. Historical milestone002 results are retained in `docs/evidence/milestone-002.json` and `docs/MILESTONE_002.md`: 27 numerical checks passed on Windows/Linux; the old character's controlled jump had approximately 4.19% breast-cage and 2.51% glute-cage local volume change with zero inversions. Those fixture results are not anatomical realism and do not validate this rebuilt mesh. Historical shoulder stretching, contact failures, empty corrective placeholders and lack of production performance remain documented there.

## Saving protocol and recovery

Root `AGENTS.md` now permanently records the proven project workflow: small text via direct Contents API with current SHA/readback; actual binaries via normal Git in Actions; save model BEFORE rendering; verify immutable remote bytes and reopen. Checkpoint unfinished active work every 5–10 minutes, targeting five. Unique paths and fetch/rebase/retry protect concurrent asset saves without force pushes.

The user's latest instructions and asset/license provenance are in `AGENTS.md`, `CHARACTER_REBUILD_003.md`, `CHARACTER_ART008.md` and `THIRD_PARTY_ASSETS.md`. The original art sheet's Astra label is not an approved character name. Never claim account-wide permanent memory or ongoing background modeling merely because these project instructions are saved.
