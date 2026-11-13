# New MakeHuman oni — first-stage study

## User-requested stopping point

A separate new MakeHuman character was created for initial review. It is NOT an edit of Art014 and does not replace that retained option without user approval. The stage covers native adult female anatomy, large breasts, increased muscularity, fuller thighs/glutes, light-purple skin and long ivory hair. Stop here and show the user before further artistic changes. No finished outfit, horns/tail/fangs, rig, animation, tissue physics or game optimization was added.

The cream pieces are removable temporary coverage in collection `TEMPORARY_REVIEW_COVERAGE`. They are not the final costume. Their construction and cleanup leave the underlying body unchanged.

## Actual MakeHuman implementation

Official MakeHuman Project MPFB 2.0.18 in Blender 4.5.3 LTS, upstream commit `d0a32e57a7f915cb2f2b95410e2117648c7bbb7e`. The body was created in a fresh scene from the native MakeHuman hm08 base with native macro/detail targets. No previous character mesh was imported and no custom body/face sculpt was performed. This is genuine MakeHuman data and controls through its official Blender integration, not the standalone MakeHuman GUI.

Native parameters: female; age 0.56; muscle 0.95; weight 0.52; proportions 0.60; height 0.72; breast-size control 1.0 and firmness 0.35. Additional native controls: buttocks volume 0.55; stomach tone 0.35; latissimus 0.15; bilateral thigh width/depth 0.25; upper-arm muscle 0.30; shoulder/lower-arm muscle 0.18. Full parameter values are preserved in the manifest and presets. The result retains ordinary human anatomical relationships rather than the old exaggerated sculpt.

Light-lavender skin is a recolored native skin texture, with sRGB palette [0.76,0.70,0.82], roughness and modest subsurface/micro-bump shading. Long native hair was fitted through MPFB and recolored ivory-silver. The face remains the native anatomical result. This is a foundation study, not a claim of finished photorealism or exact likeness to the old drawing.

## Durable model and presets

Repository: `andro951/YokaiDominion`; branch: `art-checkpoints`.
Source: `dc401ccb83159a695c6ace0b5dcad332ba176d95`.
Immutable actual-model commit: `42ca53e8f7528203878a5b1114853ae4995b8281`.
Directory: `art/checkpoints/makehuman-stage01/dc401ccb8315/`.

- `MakeHuman_Oni_Stage01.blend`: 9,524,103 bytes; SHA-256 `ce32dc0483c65538d3db15561812884eea197c7ddbe851ae7403f201ac335b11`.
- `MakeHuman_Oni_Body.mhm`: 1,290 bytes; SHA-256 `a535578048483c09efccc02e839464d4f220ba5063bafc6d49a0fc6154fea5e4`.
- `MakeHuman_Oni_Stage01.json`: 3,366 bytes; SHA-256 `ef3ffac28993296a2d756cc3a77ff32e6c70966497f635a4904469af86438f89`.
- `LavenderSkin.png`: 3,195,728 bytes; SHA-256 `1b1c30ae9efbd5af29466fdc78688de2153f2a85c90625dddcddf8de758f921e`.

Run: `43362930625`; artifact `14008912255`, `makehuman-stage01-model-verified`. ZIP SHA-256 `121c1a7dad906f4fbb83946fbcfd7e6df141fcbd01fbc2b264d5dde99c33611d`. Actual model files are ordinary Git commits, not only expiring artifacts. The earlier initial study checkpoint at `2f62317f14485d1c3f06ea3226af8d8aa8cf8c05` has rougher temporary coverage and is superseded for presentation.

## What each file reproduces

The packed .blend is authoritative for the entire current visual study, including native shape keys, hair, skin, temporary coverage, camera and lights. It can be viewed/rendered without MPFB; MPFB supplies its anatomical UI.

The .mhm is a **body-only** native parameter file, not a complete hair/skin preset. The MPFB JSON includes body and native-part references, but the custom lavender shader and ivory recoloring are added afterward by the builder. Do not claim either preset alone reproduces every Blender material. Selected original native assets and attribution are included in the downloadable package for preset rebuilding.

## Review and verification

`tools/makehuman_stage01/review.py` renders fixed front, side, back, three-quarter and portrait views with fixed lights, world, framing, color management and seed. The actual saved-file renders were inspected. No image-generation output was used as evidence.

The binary and presets were committed before rendering, downloaded at the immutable commit, compared by size/SHA-256, then reopened. The remote artifact and all manifest files were independently hash-checked in the chat container. The remote .blend reopened locally with 37 native shape-key entries, 19,158 cage vertices (including masked helper geometry), finite evaluated coordinates and no missing file-backed images.

A separate native .mhm body round-trip through MPFB reproduced the evaluated coordinates with maximum difference 0.0000002384185791015625 metres. This validates the body parameters, not artistic quality or standalone-GUI compatibility beyond MPFB's MakeHuman-file loader.

No claim of rigging, runtime physics or final game readiness is made. Further work should wait for the user's review of this first stage.

## Provenance and attribution

Native MakeHuman base/targets and system eyes, eyebrow006, eyelashes01, and young_lightskinned_female_diffuse2 skin are CC0 assets. Original headers and the upstream CC0 text are preserved in the package.

**Hair: elvs_hazel_hair, by Elvaerwyn, supplied under CC-BY in the official MakeHuman hair02 pack.** Changes: fitted to this body and recolored ivory/silver. Preserve that credit with redistribution of the hair or this model containing it. The supplied header states CC-BY but does not specify a version; do not invent one. No endorsement is implied.

Sources:
- https://github.com/makehumancommunity/mpfb2/tree/v2.0.18
- https://static.makehumancommunity.org/assets/assetpacks/hair02.html
- https://files.makehumancommunity.org/asset_packs/hair02/hair02_ccby.zip
- https://files.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip

The MPFB application software license is separate from these asset licenses. The downloadable character package does not redistribute the addon/application or Blender binaries. Exact upstream pack hashes and inventories are recorded in the checkpoint. This is a newly configured MakeHuman character, not an entirely original topology authored from nothing.
