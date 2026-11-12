# Cord007: actual model-file upload test — passed

This is a small cord/knot geometry and material refinement, not a finished character or new rig/physics milestone.

## Saved assets

- Repository: andro951/YokaiDominion
- Asset branch: art-checkpoints
- Immutable asset commit: 1f2e230192c93b3a9084ba759e023b34faa0476c
- Directory: art/checkpoints/cord007/
- Editable model: Character01_Cord007.blend
- Model size: 13,386,076 bytes
- Model SHA-256: a10153251e3296d6055849bbdfc77db6cabe818a485ed19aabc84a5ddc155b3b
- Matched before/after previews: cord-before.png and cord-after.png
- Full-body preview: three-quarter.png
- Manifest: manifest.json

These are ordinary committed binary files on the asset branch, not Git LFS pointers and not only expiring Actions artifacts. The older art/current baseline was preserved rather than overwritten.

## Source and execution

- Baseline asset commit: 0c14f54535bc0897f6b29b7c27e92ed191ce6759
- Baseline art/current/source.ref: ae306363c0c4f80fdbc82916a0f2e54d3bea0611 (Art006)
- Edit script commit: 0cad21a398e51cccad01bb83a3f0fb348450ee1c
- Workflow source commit: 579a33ba410567bd5ffac651e590b8d4247a0120
- Workflow: .github/workflows/cord007-upload.yml
- Successful run: 43149344061
- Run artifact: 13912444957, cord007-binary-roundtrip

The workflow opened the already-saved full character .blend, applied tools/art/cord_checkpoint007.py, packed dependencies and saved a complete editable model. It committed and pushed the actual .blend and PNG bytes using ordinary Git on the GitHub Actions runner. The chat connector was used to save the small source/workflow files, not to send binary bytes as text.

## Observed verification

1. All six cord, braid, knot and hanging-end objects have an editable rounding modifier and refined fibre/roughness material. Body vertex coordinates are byte-for-byte unchanged.
2. The newly saved .blend was reopened in Blender 4.5.3 before upload and the saved modifiers were checked.
3. After pushing, all four committed binary files were downloaded from GitHub at the immutable asset commit. SHA-256 and byte counts matched the pre-upload manifest.
4. That remotely downloaded .blend reopened in Blender and retained the edit.
5. The archive was independently downloaded into the chat container. Its ZIP SHA-256 matched the Actions artifact digest, and every model/preview SHA-256 matched the manifest again.
6. The downloaded model opened locally in Blender 4.5.3, restoring Body plus all six named Art007 cord modifiers.
7. Matched cord-before and cord-after renders were visually inspected. This is modest rounding/surface refinement, not a full likeness pass.

## Resume without losing the edit

Use art/checkpoints/cord007/Character01_Cord007.blend at the asset commit above for this version. The generator's older art/current file does not contain this post-processing edit. The small standalone post-processing script is saved on main and can reproduce the edit on the pinned baseline.

During active development, checkpoint unfinished work every 5–10 minutes. A successful source commit is not sufficient evidence of a saved model: confirm the corresponding binary asset commit and hash. No background modeling or periodic task is implied by this document.
