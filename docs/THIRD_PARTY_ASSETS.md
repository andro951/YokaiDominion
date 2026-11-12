# Character asset provenance

## Active rebuilt character: Blender Human Base Meshes v1.4.1

The Art003-through-Art008 replacement character derives from the realistic female anatomical mesh and its eye objects in the official Blender Human Base Meshes bundle v1.4.1. The selected object is `GEO-body_female_realistic`. The base topology and original anatomical sculpt are third-party work by Blender Studio and community contributors, not invented from scratch by this project.

Official distribution:
- https://www.blender.org/download/demo-files/
- https://download.blender.org/demo/asset-bundles/human-base-meshes/human-base-meshes-bundle-v1.4.1.zip

The official distribution page labels the bundle CC0. The bundle's README states that all provided assets are public domain under CC0. The README also documents quad topology, sculpt face sets, multiresolution detail, and UV maps including UDIMs. This matters for export: the character's source UVs span multiple tiles and must not be baked into a single PNG without repacking.

Acquisition/inventory evidence is retained in Actions run `43065127516`, artifact `13874429316` (`official-female-anatomy-source`). Its ZIP SHA-256 is `8bfb8fd99b4d1c7c1614a846b9d69dfcfcb8dc92682af465239ed929230da2fb`. That archive contains the extracted female .blend, original bundle hash, inventory, and original text blocks in inspection.json. The artifact was downloaded and its digest checked again for the Art008 handoff.

The bundle also contains a text block named License referring specifically to the Rain Rig under CC-BY 4.0. We have not imported or used the Rain Rig. Preserve that original text with provenance records instead of silently altering it. The selected realistic-female bundle asset is identified as CC0 by both the bundle README and official distribution page. Courtesy credit: Blender Studio / Blender Foundation and community contributors.

Project work includes reference-specific anatomical reshaping, clothing, hair, horns, ears, eyes/brows detail, markings, tail, materials, texture generation, asset conversion and numerical/runtime tooling. The drawings are user-provided design references. No marketplace model or third-party hair/skin image texture was added in Art008.

## Historical milestone002 prototype: MakeHuman graphical data

The earlier rejected body used selected graphical mesh/morph/rig/weight data from `makehumancommunity/makehuman`, immutable revision `a8bc2d54ff0ac92e78ff71431b1023eda42bf482`. That older model remains in historical commits and milestone archives. It is not the base of the current Art008 replacement.

The upstream LICENSE.md distinguishes AGPL application source from CC0 graphical assets. The earlier pipeline selected graphical data only; no MakeHuman application logic was copied into the C# runtime. Preserve LICENSE.ASSETS.md with that historical data.

Historical primary sources:
- https://www.makehumancommunity.org/about/license.html
- https://github.com/makehumancommunity/makehuman/blob/a8bc2d54ff0ac92e78ff71431b1023eda42bf482/LICENSE.md
- https://github.com/makehumancommunity/makehuman/blob/a8bc2d54ff0ac92e78ff71431b1023eda42bf482/LICENSE.ASSETS.md

## Scope

Do not conflate the asset licenses with an unchosen license for all project code. Do not claim the final character topology is wholly original. Do not claim that licensing establishes artistic acceptance, game performance, animation compatibility or realistic tissue behavior.
