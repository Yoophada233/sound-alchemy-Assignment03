# Glass garden artwork

Created for Sound Garden on 30 October 2026 using the built-in OpenAI ImageGen tool in Codex. The student selected the glass music-box direction, asked for the botanical scene depth of the second concept, then requested softer natural textures. These production assets follow that approved direction.

The runtime loads these local PNGs through `artwork.py`. No image service, account, API key, Pillow or network is used when running the app. The PNGs contain no interface text or controls. Text, hit areas, rain, rhythm lights, roots, letters and feedback are drawn separately in Python/Pygame.

- `landscape.png`: opaque panoramic background (1942 x 809), with no baked-in rain or musical flowers. The atmosphere is intentionally softly painted.
- `flowers.png`: transparent open flower and closed bud. Their actual split is at 64% of the sheet width; the runtime trims transparent padding and scales each head independently.
- `specimens.png`: eight transparent collectible objects, in four columns and two rows. Runtime tinting marks undiscovered specimens; numbers and names stay native text.
- `accents.png`: transparent crystals, amber reeds, canopy branch and fern. These replace the earlier flat scenery motifs. Their quadrants are trimmed at runtime, without modifying the original PNG.
- `foliage.png`: 1254 x 1254 RGBA atlas of ivy, a hanging branch, a fern/moss corner and a foreground leafy branch. The left column's split is at 54% of the height, inside the transparent gap; the right column splits at 50%. The original asset is preserved. `foliage.py` composes these into shaded page edges and wide-window margins. Leaves are static, so they do not compete with the four musical flowers or restart any sound.

The painted scenery stays quiet; live controls still govern precipitation, additional fern growth, root pulses, flower choices, fireflies and scene-specific motifs. If an image is absent or unreadable, code-drawn geometry remains available.

The concept mockup is visual direction, not a screenshot of the finished app. `../../docs/screenshot.png` is captured from the actual application. No generated concept is presented as a runtime or user-trial result.

## Generation prompts

The later page-border asset has its own [exact foliage prompt](foliage-prompt.md).

### landscape.png

Use case: stylized-concept.
Asset type: a production background plate for the existing Sound Garden Python application, NOT a UI mockup.
Reference image: the approved dark glass music-box design. Extract its softened nocturnal landscape art direction into a clean panoramic backdrop for use behind separately coded interactive flowers and controls.
Create ONE ultra-wide landscape image, approximately 3072 x 1280 pixels, aspect ratio 2.4:1. No framing or margins. The entire image is scenery.
Composition: a calm deep midnight-blue sky occupying the upper third; three layers of blue mountains receding through soft atmospheric mist; a smaller middle-distance evergreen forest shoreline around y=48%; a broad moonlit blue lake in the middle from y=50% to 78%; four subtle low moss-and-stone near-shore islands centered near x=19%,39%,60%,80%, with ground at y=85%. A dark near-soil band occupies the lowest 12%, with natural moss edges and a few graceful ferns only at the far left and right. Leave clear open water behind the future flower positions around y=65%. Empty quiet dark sky in the upper left and upper right must accept text overlays.
Style: carefully authored softly painted 2.5D miniature ecosystem, midnight teal/navy, satin smooth surfaces, botanical silhouettes, subdued green moss. Smooth coherent forms, soft mountain edges and calm horizontal lake reflections. NO grain, noise, crunchy sharpening, tiny glitter, photographic HDR or overly dense vegetation. Medium-scale material detail, not a blurry image. Quiet ambient moonlight from above-right, with a restrained reflection in the lake.
CRITICAL exclusions: NO interface, NO text, NO letters, NO numbers, NO logos, NO labels, NO buttons, NO border, NO brass frame, NO musical flowers, NO glowing flower stems, NO glass buds, NO foreground flower blossoms, NO specimen shelf, NO moon itself, NO stars, NO rain streaks, NO fireflies. These are separate live elements added by code. Do not copy any controls from the reference. Do not depict a whole terrarium or display case. Deliver only the fully painted seamless landscape plate.

### flowers.png

Use case: stylized-concept.
Asset type: a transparent game sprite atlas containing TWO flower-head states for the Sound Garden instrument.
Reference: match the delicate translucent botanical glass and warm light in the supplied approved concept.
Output one landscape 2:1 RGBA image with a genuinely transparent background. Divide the image into two equal square cells with no visible dividing line, with one centered sprite in each cell. Keep generous completely transparent padding, no overlap. Exact same visual scale across the two cells.
LEFT CELL: a single open glass lily flower HEAD ONLY, seen from the front slightly above, delicate broad translucent clear glass petals curving upward around a softly glowing warm amber center with a few fine gold stamens. Elegant small asymmetries in petals, smooth satin glass, warm rim highlights and a subtle muted lilac tint in shadows. Fill about 72% of the square's width and 65% of its height, centered at cell center.
RIGHT CELL: the same flower HEAD as a fully closed, unlit glass bud. Narrow tear-shaped folded glass petals, gently translucent smoky jade with faint lilac and warm brass rims, no internal bright glow. About 30% of cell width and 65% of cell height, exactly centered at the same vertical position as the open head.
No stalks, no leaves, no soil, no scenery, no rocks, no detached sparkles, no display plinths, no cast shadows, no lettering or numbers, no UI, no background gradients, no checkerboard. Both flower heads need clean transparent edges and controlled highlights. Softly rendered dimensional illustration, NOT oversharpened photography. The two sprites will be cropped by equal cell boundaries and placed on separately drawn stems. Preserve true alpha transparency.

### specimens.png

Use case: stylized-concept.
Asset type: one transparent sprite sheet of eight collectible botanical miniatures for Sound Garden.
Reference image establishes materials: translucent glass and living moss on small brushed dark-brass circular plinths, soft warm light, elegant miniature forms, smooth softly painted 2.5D finish. Not gritty, not oversharpened, not photorealistic HDR.
Deliver one landscape 2:1 RGBA image, with EIGHT independent objects in an EXACTLY regular FOUR COLUMN by TWO ROW grid. Every cell has identical dimensions, its object centered and fully contained, generous transparent spacing, matching base size and visual scale. Bottoms of bases align within each row. No contact or overlap between cells. Genuine transparent background, NO checkerboard or painted backdrop.
Read left to right across the top row, then across the bottom row:
1. Rainy moss: a delicate clear glass water droplet dome containing a tiny green moss garden.
2. Moonlit roots: a pale crescent moon above fine visible curling bronze roots, a quiet midnight glass botanical sculpture.
3. Firefly grove: an airy small clover plant with three or four tiny amber firefly lights among translucent green leaves.
4. Dawn chorus: a small cluster of open pale glass flowers, warm peach centers, thin elegant stems.
5. Storm roots: a smoky blue-gray small glass rain cloud with three slim raindrops above an exposed curled root system.
6. Crystal rain: three faceted transparent blue-white quartz crystals rising beside a tiny reflective pool.
7. Starlit canopy: an arched delicate branch with five translucent leaves and a subtle small constellation of points between the twigs.
8. Amber reeds: a group of three slender golden reed stems, warm amber seed heads, translucent narrow leaves.
All eight stand on their own identical low round dark-brass plinth. NO text, NO specimen names, NO numbers, NO labels, NO dividers, NO UI, NO large halo, NO table, NO surrounding scenery, NO scene outside the objects. Small controlled highlights and natural silhouettes, each clearly different at icon size. Keep ALL objects fully visible inside their own equally spaced grid cell.

### accents.png

Use case: stylized-concept.
Create one TRANSPARENT RGBA environment sprite atlas for the Sound Garden miniature lake scene. Match the softened glass ecosystem in reference 1 and the botanical materials of reference 2, but these are NATURAL SCENERY OBJECTS with NO display plinths.
Exactly FOUR separate objects in a regular TWO COLUMN by TWO ROW square grid, centered inside equal square cells, generous transparent margins and no overlap.
Top-left: a small elegant cluster of three translucent smoky blue quartz crystals of different heights, one tall center crystal and two shorter ones, softly rounded highlights, a few tiny dark moss leaves at their base. No pedestal or pot.
Top-right: an airy clump of five slender amber reeds, long fine bronze-green stems, translucent golden narrow leaves, soft warm oat seed heads. Natural botanical asymmetry. No pedestal or pot.
Bottom-left: a graceful arched botanical branch, growing from bottom-left up and across toward the upper right; eight widely spaced jade glass leaves, slender dark wood stem, a few delicate pale star points. Fine silhouette, mostly empty transparent space. No base.
Bottom-right: one small graceful green fern plant with several curved fronds, softly rendered jade foliage with restrained pale rim light, darkest greens at the base. Natural plant, not a glass ornament, no base.
Art style: dimensional softly painted miniature scene props, clean smooth surfaces, low microcontrast, subdued cool night ambient light, delicate warm highlights. Refined coherent forms, not grainy photography or flat geometric icons. Do not add a glow cloud, large shadow or decorative fragments outside the objects.
No text, no numbers, no UI, no background, no table, no display stands, no disks, no frames, no enclosing glass. True alpha transparency throughout all empty space. Keep every object fully inside its equal quadrant, separated by clear transparent gutters.

