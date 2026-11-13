# Character01 Art014 — actual jaw and cheek mesh correction

## Scope and retained visual decision

The user's current request was to fix the actual 3D face, especially the jaw and cheeks. The preceding image-generator response did not edit the model and must not be represented as a model update. This revision uses Blender mesh edits and real rendered comparisons only. No image generator or paid 3D generator was used.

Retained revision: `014-face-4`, based on the existing Art013 body and garment. It tapers the broad lower face, rounds the square chin/jaw corners, softens the abrupt diagonal cheek transition, and redistributes cheek fullness. The first narrowing-only pass was rejected because it pinched the face; an intermediate smoother pass was rejected because the profile lost too much chin projection. The retained pass restores projection while keeping the rounded contour. See `ART014_VISUAL_REVIEW.md`.

This is a localized modeler-reviewed correction, not user approval, an exact copy of a generated portrait, or a claim that the entire character is artistically finished. The body, breasts, outfit, hair, horns, separate eyes and accessories were not rebuilt. No new rig, animation, physics or game-performance acceptance is added.

## Standard actual-model portrait review

`tools/art/review014.py` adds fixed close-up face-front, face-quarter, face-side and opposite-quarter cameras to `review013.py`. Both before and after are rendered at the same camera/light/world/color settings, with 800-pixel width and 32 Cycles samples for delivery. The script never saves over the source model. Each review manifest records the source model hash, camera/light settings and output hashes.

    blender -b -t 4 --python-exit-code 1 --python tools/art/review014.py -- --source Character01_Art014.blend --out review --shots face-front,face-quarter,face-side --width 800 --samples 32

The export is separately reimported and rendered. A generated image is never evidence that the 3D asset changed.

## Verified editable master

Repository: `andro951/YokaiDominion`, branch `art-checkpoints`.

- Source revision: `006503bbc6a8a5a5a2dc73a9ab957a00b2a6078d`.
- Immutable binary commit: `1e3649e9c8683a51ece6dfdaf3639a3198a8f118`.
- Path: `art/checkpoints/face014/006503bbc6a8/Character01_Art014.blend`.
- Size: 88,381,563 bytes.
- SHA-256: `347c10d42c2b73eae6ffee8e5d7d79fe0b5cc169b11a417c6bfdda07865bac0a`.
- Save/readback/reopen/render run: `43358308317`.
- Convenience artifact: `14007596420`, `art014-master-verified`.
- Artifact ZIP SHA-256: `32f1ce8c4677cbc004faf569102748fc6b9ce4a8f46e540c8d657e63f324e772`.

The runner pushed actual editable bytes before rendering. It downloaded those bytes at the immutable commit, compared SHA-256 and size, reopened Blender and rendered portraits. The archive and model hash were independently checked after downloading into the chat container, and the remotely saved model reopened there for an independent scope audit.

## Verified textured Blender and GLB

- Export source: `f4caa2b25ed00489dfde8e362db6dba311bc4d32`.
- Immutable binary commit: `530c5a59b2318c7a3fc95581395cb6f61c2b5113`.
- Directory: `art/checkpoints/portable014/f4caa2b25ed0/`.
- `Character01_PBR014.blend`: 28,888,652 bytes; SHA-256 `03e6eb524d6b55eea064e0b0f353326596937316f59708e66fd8f5d969f5c9fb`.
- `Character01_Visual014.glb`: 66,956,864 bytes; SHA-256 `d16b32f18eadcad15635a409f18d60cb705e065876354290d3ed405c86df7b78`.
- Export/readback/reopen/audit/reimport run: `43358962660`.
- Convenience artifact: `14007556413`, `art014-portable-verified`.
- Artifact ZIP SHA-256: `3255cc654befabce395ecbc83a365a39d704a603a4bc5d5f7e6e8553adcfe1b4`.

The export transfers the actual final displacement field, including the cheek fairing, to the existing PBR013 topology using barycentric interpolation on the prior high-resolution facial surface. Maximum nearest-surface mapping distance was approximately 0.254 mm. Existing baked skin colors were preserved exactly. Other meshes were not regenerated. The GLB remains a static high-detail visual asset with embedded images and no skins or animation clips; its triangle count remains 948,194.

## Independent saved-file audit

`tools/art/audit014.py` compares the actual loaded before/after files. The remote master audit found 22,664 changed vertices after float32 storage, with a maximum displacement of approximately 11.06 mm. All 800,727 vertices outside the facial bounding region were exactly unchanged; all 387 other mesh objects matched in vertex positions, topology, UVs, colors, material assignments, transforms and render visibility. The body's topology, UVs, colors and material assignments were unchanged.

The remote portable Blender copy also passed: 10,620 stored vertices changed; all 169,631 vertices outside the facial bounding region and all 290 other mesh objects were unchanged. Both audits confirmed finite positions. These integrity checks do not prove artistic likeness or animation quality.

The working edit report counts 22,721 nonzero float64 changes before Blender's float32 storage; tiny changes can round away. The independent stored-file count above is the delivery count, not a contradiction or additional edit.

## Recovery and next work

Resume from the saved Art014 master, not from the image-generated picture or the older Art013 face. `face014.py` refuses applying its operation twice; new work must be a new revision based on the saved model. Preserve the accepted body and garment unless the user requests changes.

Use the method in `AGENTS.md`: UTF-8 source through direct create/update actions; actual .blend/.glb bytes through ordinary Git in Actions; save before long renders; verify immutable downloaded bytes and reopening. During active work, save unfinished checkpoints every 5–10 minutes. Earlier Art014 pass-1 and pass-3 backups remain unfinished historical checkpoints, not the retained deliverable.
