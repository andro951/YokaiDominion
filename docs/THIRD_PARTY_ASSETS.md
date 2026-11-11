# Character asset provenance

## CC0 anatomical base data under evaluation

The hand-built voxel body exposed significant anatomy and skin-weight limitations. A clean humanoid base with established facial and finger topology is a better foundation for the requested quality than polishing fused primitives indefinitely.

Selected upstream: `makehumancommunity/makehuman`, immutable revision `a8bc2d54ff0ac92e78ff71431b1023eda42bf482`.

The upstream LICENSE.md explicitly distinguishes application source code (AGPL) from graphical assets: base meshes, targets, rigs, textures and other graphical data are CC0 1.0 Universal. Only graphical data is selected for the character pipeline; no upstream application logic is being copied into the C# runtime or project authoring code. Preserve LICENSE.ASSETS.md with vendored/exported data and record exact hashes when individual files are selected.

Primary license sources:
- https://www.makehumancommunity.org/about/license.html
- https://github.com/makehumancommunity/makehuman/blob/a8bc2d54ff0ac92e78ff71431b1023eda42bf482/LICENSE.md
- https://github.com/makehumancommunity/makehuman/blob/a8bc2d54ff0ac92e78ff71431b1023eda42bf482/LICENSE.ASSETS.md

The base topology is third-party CC0 data, not an original topology sculpt by this project. Reference-specific reshaping, costume, fantasy details, integration and tissue runtime are developed here. Do not describe the complete resulting asset as made entirely from scratch.

This checkpoint only obtains and evaluates the base data. It does not yet replace the current generated character or assert quality acceptance.
