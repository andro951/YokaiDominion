# Direct GitHub checkpoint protocol

This file tests the connected GitHub Contents API. It is not a new character-art revision and does not claim that an editable model has been uploaded.

## Round-trip evidence

- Repository head observed before this test: `ae306363c0c4f80fdbc82916a0f2e54d3bea0611`.
- Initial direct create succeeded at commit `6d7738d3df3ecb427e7d771c0b3df7d52fdce1e5`.
- Fetching the file at that exact commit returned the expected complete text and probe token.
- This revision uses update_file with the fetched blob SHA `007b60f9af08c71329257a7c3bc5e05d43d3eaaa`; verify this revision by reading the resulting commit as well.

## Saving during active development

- Checkpoint unfinished changes approximately every five minutes, never intentionally exceeding ten minutes of unsaved active work. Also checkpoint before long renders or risky operations.
- For small text changes, use direct create_file/update_file calls. For updates, fetch the current file SHA and supply it; do not force-update branch history or overwrite unrelated work.
- Confirm each successful write with the returned commit SHA and fetch the committed file to verify its content. A local save, prepared API payload, or uncommitted Git object is not a remote checkpoint.
- Preserve editable Blender assets separately with a verified binary-capable upload route. Do not claim that saving scripts or preview images alone preserves unsaved mesh edits.
- Record the exact saved source revision, editable-asset location/hash when available, and any work that remains local or unverified.

No periodic background task is implied. This cadence applies while an assistant is actively working with tools in a conversation.

Probe token: yokai-art006-direct-contents-roundtrip-v2
