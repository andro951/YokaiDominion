# Art013 visual review decisions

## Scope
Complete the requested breast spacing, attachment, hanging contour and loose over-trapezius garment corrections. Do not claim the whole character is production-ready. No paid generation and no image-generated substitutes were used.

## Standard screenshots
`tools/art/review013.py` renders the actual supplied Blender file through fixed front, quarter, side, shoulder, full-body and back cameras. Optional cropped body-only views inspect the anatomy before garment fitting. The script replaces inherited lights, hides inherited studio meshes, fixes world/color-management settings and Cycles seed, and writes camera coordinates, file hashes and source hash to `review-manifest.json`. It never saves over the source model.

## Comparisons actually inspected

**Rejected Art011 vs recovered Art012:** The Art011 front has excessive spacing and a large flat upper-chest gap. Its side view projects nearly horizontally with a straight lower fabric bridge. The recovered Art012 master has a higher continuous attachment, lower fullness and a more vertical hanging silhouette. Preserve that recovery rather than reverting to Art008 or rerunning the Art011 enlargement.

**Art013 contour/drape pass 1 vs recovered Art012:** A small localized redistribution (maximum about 6.2 mm) softens the upper slope and adds weight to the lower contour. Other anatomy remains protected. Fairing the previously physically relaxed cloth removes the sharp scalloped ripples. The front and side look cleaner, but the cloth became too smooth; retain the contour and refine the fabric rather than enlarge the breasts again.

**Art013 contour/drape pass 2 vs pass 1:** Restore broad low-amplitude longitudinal folds using the garment's surface normal, with zero edge displacement. Keep the over-trapezius route and waist endpoints. The folds do not reshape the body. The quarter view reads more as fabric than the flat pass 1, without bringing back the jagged wrinkles. This is the retained candidate.

**Art013 vs rejected Art011, identically framed:** Front, quarter and side comparisons were rendered using the same script, camera coordinates, world, lighting, resolution and sample count. The side view shows the longer upper slope and lower hanging mass rather than the earlier projecting bulb. The front no longer has the excessive central separation. The shoulder view keeps the throat open, with cloth over the upper trapezius rather than a horseshoe throat collar. The current local front/quarter/side/shoulder/full views were inspected directly, not evaluated only by successful export.

## Acceptance boundary
This is the modeler's visual acceptance of this localized correction pass, not user approval, a likeness score or certification of perfect anatomy. The separate face/hair finish, runtime rig, tissue simulation, dynamic garment collisions and production LOD remain outside this pass. The earlier erroneous claim that a successful export proves art completion must not recur.

## Save method
Text/source via the connected Contents create/update actions; actual .blend and GLB bytes via ordinary Git on GitHub Actions. Save the binary before rendering, then download at an immutable commit, compare hashes/size and reopen. New checkpoint paths preserve rejected passes. Do not overwrite or force-reset user work.
