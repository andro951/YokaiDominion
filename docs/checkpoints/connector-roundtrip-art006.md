# Direct GitHub checkpoint protocol

This file is a small write/read-back probe of the connected GitHub Contents API. It is not a new character-art revision and does not claim that an editable model has been uploaded.

Repository head observed before this probe: `ae306363c0c4f80fdbc82916a0f2e54d3bea0611`.

## Saving during active development

- Checkpoint unfinished changes approximately every five minutes, never intentionally exceeding ten minutes of unsaved active work. Also checkpoint before long renders or risky operations.
- For small text changes, use direct create_file/update_file calls. For updates, fetch the current file SHA and supply it; do not force-update branch history or overwrite unrelated work.
- Confirm each successful write with the returned commit SHA and fetch the committed file to verify its content. A local save, prepared API payload, or uncommitted Git object is not a remote checkpoint.
- Preserve editable Blender assets separately with a verified binary-capable upload route. Do not claim that saving scripts or preview images alone preserves unsaved mesh edits.
- Record the exact saved source revision, editable-asset location/hash when available, and any work that remains local or unverified.

No periodic background task is implied. This cadence applies while an assistant is actively working with tools in a conversation.

Probe token: yokai-art006-direct-contents-roundtrip-v1
