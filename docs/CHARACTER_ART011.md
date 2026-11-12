# Character01 Art011 — breast and upper-garment revision

## Scope and current design authority

This is an actual Blender geometry revision, not an image-generated substitute. The user rejected paid AI 3D generation and requested completion of the breast and clothing corrections on the existing model. No paid generator was used.

The approved generated full-body picture guides the fuller breast size, but its horseshoe throat collar is explicitly rejected. The top must travel over the upper trapezius, with only its inner edge beside the neck. The throat remains open. Keep breasts separated, hanging and somewhat outward, with fuller lower poles; do not widen shoulders or hips. Shape the body independently before fitting the loose garment. Only the waist cord is cinched. These latest instructions override earlier instructions to run the top directly toward the throat.

## Actual changes

Resumed the already-saved Art010 pass11 master, not the smaller Art008 asset. Added localized lower/forward breast fullness and a mild downward/outward adjustment, with restricted fairing of the inner attachment. The master edit changes 3,036 body vertices and preserves all 159,606 protected vertices exactly. Maximum additional forward projection relative to Art010 is 0.0246166 m and maximum lowering is 0.010252 m. These are local geometric displacements, not a claim that breast volume changed by a particular percentage.

The independent front-to-back garment strips follow that body shape, widen slightly toward their inner chest edges, and use the continuous over-trapezius shoulder arc. No transverse collar is added. The two upper abdominal rows remain visible. Face, neck, shoulders, arms, hips, legs, back, hair and other accessories were not reshaped by this pass.

Rejected local passes tried projecting the upper strip downward onto the body. At the inner edge this struck the neck and made narrow upright cloth spikes. The final revision removes that projection, preserves the existing continuous trap arc, settles it slightly and fairs its joins. Do not deliver the first Art011 workflow output as final; use revision `011-fullness-drape-3` below.

## Durable editable master

Repository: `andro951/YokaiDominion`, branch `art-checkpoints`.

- Source: `4cb4818d7029e5bce84a56359623de373b899139`.
- Immutable asset commit: `f1c9cc7a621ea1d70f0725f7a1ab1fc2ed599de0`.
- File: `art/checkpoints/art011/4cb4818d7029/Character01_Art011.blend`.
- SHA-256: `54ab5f8d2cc71160c12522d046c396db19604b6ef7c2c1bc130ebba18032b948`.
- Size: 21,501,856 bytes.
- Successful save/readback/reopen/render run: `43180170130`.
- Review artifact: `13926396337`, `art011-editable-verified`.
- Artifact ZIP SHA-256: `3eaa4d70b67cde08d0e982bd6035fe613894c8f896217cbd6a2d7d52b5d1671c`.

The binary was committed before rendering. It was downloaded at the immutable asset commit, checked against its size/hash, reopened in Blender, and rendered. The entire archive was independently downloaded into the chat environment, its digest checked, and the master reopened and audited there again. The archive is a convenience; the model bytes are also normal Git files and do not depend on artifact retention.

## Durable textured Blender and GLB

- Export source: `3ab39eb9ce8ec7248e405f383ba9f51a1605adc4`.
- Immutable asset commit: `ccf9f3e9795365567b4973ed9e9537c9f156f9b2`.
- Directory: `art/checkpoints/portable011/3ab39eb9ce8e/`.
- `Character01_PBR011.blend`: 45,455,411 bytes; SHA-256 `29928d6ec1c3aa7eb6a7f6da2ed4ab25fcc223fec98f4e1673426065e270e106`.
- `Character01_Visual011.glb`: 48,996,928 bytes; SHA-256 `aebcb80037e45b35aff70af1526c0a45addbbeddd15000aca1fc0e4a16fa9dbb`.
- Successful export/readback/reopen/reimport/render run: `43180740392`.
- Artifact: `13925544106`, `art011-portable-verified`.
- Artifact ZIP SHA-256: `96b6376af4ab2cedb15ab75771b4d400350bb93470c3e7fd5562efd066ebb0e2`.

The breast delta was transferred from the high-resolution master to the existing textured body using triangle barycentric interpolation. UV coordinates were preserved byte-for-byte. The high-resolution sculpt and new cloth strips are retained in the packed PBR Blender copy. The generated GLB includes its textures and was reimported and rendered, rather than accepted solely because an export command succeeded. Remote-downloaded PBR bytes were also reopened locally.

## Verification and limits

The static independent audit reports finite geometry, unchanged protected anatomy, and no sampled garment points more than 0.5 mm inside the nearby body surface. It samples every fourth evaluated cloth vertex within a 3 cm nearest-surface window: 14,854 left and 14,827 right near-surface samples. It is not a proof against all triangle intersections or future animation collisions. See `tools/art/audit011.py` and `docs/evidence/art011-surface-audit.json`.

The portable body has 67,746 vertices. The complete high-detail visual export has 720,548 triangles, including subdivided cloth and hair, zero skins, and no animation clips. This is not a measured production game budget. No rig, cloth simulation, C# tissue integration or performance acceptance is added by this visual revision.

The requested breast/top corrections have been applied and visually reviewed in actual torso, three-quarter, side and shoulder renders. This is not a claim of exact identity with the generated picture, user approval, or completion of the whole character/game package. The broader face/hair/material quality is outside this localized revision.

## Reproduce / continue

Use `tools/art/refine011.py` on the pinned Art010 master from `9d2ebe2f3532d5fd84762caa601cc412f424f250`, path `art/checkpoints/art010/121d100576f5/Character01_Art010.blend`. The script refuses applying its changes twice. To continue new edits, open the saved Art011 master above rather than reapplying the same script to it.

`tools/art/export011.py` transfers the delta to the pinned PBR010 baseline. Both workflows preserve hashes and exact sources in their checkpoint directories. Keep the existing rule: save unfinished actual editable files every 5–10 minutes during active work; push before long renders; verify remote bytes and reopening. No asynchronous modeling is implied.
