"""Install the generated character from a GitHub Actions artifact without extracting arbitrary paths."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import zipfile


def install(archive: Path, destination: Path, force: bool = False) -> dict:
    wanted = ['character-blockout.glb', 'tissue-regions.json', 'character-manifest.json', 'CC0-1.0.txt']
    payloads = {}
    with zipfile.ZipFile(archive) as z:
        for name in wanted:
            key = 'character/' + name
            info = z.getinfo(key)
            if info.file_size > 100 * 1024 * 1024:
                raise ValueError(f'Unexpectedly large character component: {name}')
            payloads[name] = z.read(key)
    data = payloads['character-blockout.glb']
    if len(data) < 20 or struct.unpack_from('<III', data) != (0x46546C67, 2, len(data)):
        raise ValueError('Invalid GLB header')
    regions = json.loads(payloads['tissue-regions.json'])
    manifest = json.loads(payloads['character-manifest.json'])
    if regions.get('schemaVersion') != 1 or len(regions.get('regions', [])) != 4:
        raise ValueError('Unsupported tissue-region asset')
    if not re.fullmatch('[0-9a-f]{40}', manifest.get('sourceCommit', '')):
        raise ValueError('Asset must identify its authoring source revision')
    for name, content in payloads.items():
        path = destination / name
        if path.exists() and path.read_bytes() != content and not force:
            raise FileExistsError(f'{path} differs. Preserve your edits or use --force explicitly.')
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in payloads.items():
        (destination / name).write_bytes(content)
    receipt = {'sourceCommit': manifest['sourceCommit'], 'files': {n: hashlib.sha256(c).hexdigest() for n, c in payloads.items()}}
    (destination / 'install-receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifact', type=Path)
    parser.add_argument('--destination', type=Path, default=Path(__file__).resolve().parents[1] / 'game/Assets/Character01')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    print(json.dumps(install(args.artifact, args.destination, args.force), indent=2))
