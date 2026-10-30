# sound-alchemy-Assignment03

**Grow a little world with sound.**

A small Python experience for someone who wants to play with sound without
learning a music editor. Rain nourishes moss, Bass wakes roots and Bells open
flowers and firefly lights. Click four flowers to write a tiny repeating melody,
discover landscapes, name and keep your favourite gardens, or follow an optional
visitor invitation. No music theory is needed.

![Sound Alchemy desktop interface](docs/screenshot.png)

The interface is a moonlit glass music box. Soft mountain layers and a quiet
lake sit behind four playable glass flowers; a dark sound workbench sits below.
Eight botanical miniatures form a specimen shelf. Visitor letters open only
when wanted, and kept gardens carry pictures of their actual recipes.
Five local PNG assets supply the painted scenery and transparent plants.
Satin green leaves, climbing ivy and fern corners surround the instrument;
soft shadows separate them from the dark background. Wider windows extend the
plants into the side margins. This decoration is cached at the window size,
with the controls and text drawn clearly above it.
Pygame draws the text, controls, rain, root pulses and musical lights separately.
The [artwork notes](assets/glass/README.md) credit ImageGen and include the prompts.
The [wide-window screenshot](docs/foliage-wide.png) shows the surrounding plants
in the additional side space. Older interaction GIFs predate this edge decoration.

[See the eight specimens](docs/field-notes.png),
[kept recipe pictures](docs/kept-gardens.png), or
[watch a specimen being filed](docs/discovery-unlock.gif).
The silent GIF is a scripted demonstration using the actual app renderer,
not a recording of a user trial.

[Watch the four-flower melody](docs/flower-melody.gif) and
[hear an example](docs/flower-melody.wav). The GIF is silent; the separate WAV
demonstrates a prepared recipe. These are scripted examples, not a user trial.

## The interaction

1. Press the gold **Play your garden** button beside the garden. A short, dismissible
   introduction moves from listening to making a phrase, then following a clue.
   Nothing plays automatically; you can also explore a silent visual preview.
2. Click the four numbered flowers, or press **1-4**, to make each one ring or rest. Flowers 1-4
   occupy seconds 0, 1, 2 and 3 of the repeating four-second loop. Flowers 1 and 3
   start lit. During playback a firefly visits the beats and each sounding flower
   lights up. Try leaving one quiet beat, then adding it back.
3. Explore eight landscape discoveries, shown together in **Specimens**. Choose
   **Explore this** to pin a listening clue above the flowers. **A gentle nudge**
   gives one direction based on your current controls; **Show exact recipe**
   reveals the numbers only when you ask. A new discovery shows its name,
   a short garden celebration and a leaf flying into the notebook. Its specimen
   gains colour and a NEW marker. Use **View specimen** to find it;
   there is no gameplay timer, score or wilting penalty. A collected specimen's
   note offers a small composing experiment, such as comparing neighbouring
   flowers with separated ones. These experiments are optional, without a score.
4. Choose **Keep garden**, give it a name and press Enter. In **Kept gardens**,
   click a card to restore its sound controls, four-flower melody and landscape,
   then press Play. Its thumbnail comes from that saved recipe.
5. For a little direction, click **Letters**, then **Open invitation** on a visitor
   letter. It starts with a short descriptive clue; **Need recipe numbers?**
   reveals its generous ranges. **Share this garden** checks them and
   awards a thank-you stamp. **Next note** lets you try another; the x closes the
   letter so you can see the whole garden again. Free exploration always works.
6. **Reset** restores the initial sound controls and the starter melody, and stops playback. It preserves
   this visit's discoveries, cards and stamps. Closing and reopening starts a
   fresh visit with no progress. Under **Tools & export**, **Save 8-second WAV**
   exports sound and a recipe; **Open exports** opens the folder.

While listening, **hold Q / W / E**, or hold the corresponding Rain / Bass / Bells
button below Play, to hear one layer on its own. Release to hear the full mix
again. You can hold a key while moving a slider: try W with Pitch, or E with
Sparkle. This temporary listening focus preserves your recipe, loop position,
discoveries and exported mix. It never starts sound by itself. Stopping, leaving
the app, opening the naming dialog or muting the focused layer clears it.

The short loop is **listen > change a beat > follow a clue > discover > try a variation > keep**.
The three optional wishes provide gentle goals. They accept multiple recipes;
there is no exact sound-matching test. The garden responds directly to control
state, rather than analysing speaker output. Lowering MASTER leaves it intact.

Audio is synthesized locally and the included artwork renders offline. Nothing plays on startup, and
switching windows stops playback. No accounts, microphone or services are needed.

[See a listening clue](docs/listening-guide.png),
[see a single layer in focus](docs/listening-focus.png), or
[watch the listening-and-discovery tour](docs/listening-tour.gif).
The tour is a silent scripted demonstration of the app, not a user trial.

## Run on Windows

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) on your PATH.
On the development computer it is already available. The first setup needs
internet; subsequent launches work offline once the local runtime and package
are cached.

**Double-click `start.cmd`.** It finds or prepares Python 3.12 inside this folder,
installs the declared Pygame dependency into the project cache, then opens the
app. It does not install global Python commands or edit the Windows registry.
Keep the launcher terminal open while using the app. Close the app window to exit.

The same setup can be reproduced from a fresh PowerShell terminal in this folder:

```powershell
$env:UV_CACHE_DIR = "$PWD\.uv-cache"
$env:UV_PYTHON_INSTALL_DIR = "$PWD\.python"
$env:PYTHONDONTWRITEBYTECODE = "1"
uv python install 3.12 --no-bin --no-registry
uv run --no-project --managed-python --python 3.12 app.py
```

`app.py` declares `pygame==2.6.1` in its `# /// script` header. No global pip
installation, manual virtual-environment activation or course Week 4 environment
is needed. Python 3.12.14 and Pygame 2.6.1 were used for local verification.

If you already have a suitable Python and prefer your normal uv setup:

```text
uv run --no-project --python 3.12 app.py
```

This shorter command uses your normal uv cache/settings. The Windows launcher
and full PowerShell instructions above keep the runtime and cache in this project.

For macOS/Linux with uv and Python 3.12:

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv run --no-project --python 3.12 app.py
```

Only Windows has been checked. On other systems Pygame's bundled font replaces
the Windows fonts; the appearance may differ.

## High-resolution displays

Close any older app window and start the updated app through `start.cmd`.
Maximizing or resizing redraws text, controls, specimens, thumbnails and the
garden at the viewport's actual pixel resolution. The 1280 x 960 layout remains
a coordinate system rather than a bitmap stretched across the monitor. A
2560 x 1440 window draws a 1920 x 1440 content area; at 3840 x 2160 it draws
2880 x 2160, with the same proportions and accurate click positions.

The painted landscape is deliberately soft; it is a 1942 x 809 source image
resampled to the scene area. Interface text, controls, flower numbers and live
effects are drawn at native density, independently of this painting.

Windows uses SDL's
[per-monitor V2 DPI awareness](https://wiki.libsdl.org/SDL2/SDL_HINT_WINDOWS_DPI_AWARENESS)
to avoid operating-system bitmap stretching. This is an app-level setting;
Windows display settings do not need changing. Fonts and illustrations are
cached at their current pixel size, with bounded garden buffers to keep memory
and redraw work under control.

## Controls and feedback

The four newer discoveries add distinct scenery:

| Discovery | Landscape response |
| --- | --- |
| Storm roots | A dark rain cloud and glowing underground roots. |
| Crystal rain | Blue faceted crystals beside reflective rain pools. |
| Starlit canopy | An arch of leaves and linked constellations above the garden. |
| Amber reeds | Tall golden reeds under a warm horizon. |

All eight specimens are visible on one shelf. Unobserved entries keep dim,
coloured silhouettes; observed entries gain warm light and their own colour.
Unlocks work during silent visual preview as well as playback. A named notice,
a garden celebration, a 1.35-second filing animation and the specimen highlight
make the result visible. An already discovered recipe does not repeat the reward.

| Action | Response and feedback |
| --- | --- |
| Click a preset | Loads a different combination while preserving the four flower choices; the selected button is highlighted. |
| Click an ingredient's ON/OFF button | Adds/removes that ingredient; the card and label change. |
| Drag LEVEL | Changes the running sound volume and the corresponding rain, roots or flowers. The phrase keeps its position. |
| Click a numbered flower / keys 1-4 | Toggles the bell at second 0 / 1 / 2 / 3. Bright numbered buttons and RING / REST labels show the choice. Flower light and the travelling firefly connect it to its place in the loop. Rain and Bass continue uninterrupted. |
| Hold Q / W / E, or the Rain / Bass / Bells listening buttons | Temporarily hears one layer during playback. Release to restore the complete mix. Keyboard focus permits simultaneous slider edits; dragging off a held mouse button cancels focus. Muted layers explain how to enable them. |
| Drag DROPS | Changes the density of overlapping soft rain textures; Rain remains a continuous curtain rather than separate audible taps. |
| Drag PITCH | Changes Bass pitch and plant height; the four bell notes follow the Bass root using notes from a pentatonic scale. |
| Drag SPARKLE | Changes bell decay and flower glow. The four beat positions and chosen flowers stay unchanged. |
| LEVEL at zero / ingredient OFF | Its lower parameter is greyed out and marked DISABLED. Clicks and drags are blocked; the hint explains how to enable it. Its previous value is preserved. |
| Bells LEVEL zero / OFF, then click a flower | The melody is preserved and the click explains how to re-enable Bells. MASTER at zero still allows composing; raise it to hear the result. |
| Drag MASTER | Changes all running layers immediately, including the recipe used for export. |
| Play your garden / Stop listening / Space | The single gold button above the flowers starts or stops playback; repeated presses do not stack copies. Stopping keeps the recipe. |
| Escape | Closes the letter/tools and stops immediately; later background work cannot restart it. In the naming dialog it cancels naming. |
| Reset / R | Stops and restores the initial Rainy window controls and flowers 1+3; keeps discoveries and saved cards. |
| Tools & export / Save / S | Opens the export controls; Save or S writes a new 8-second WAV and recipe under `out/mixes/`. |
| Open exports | Becomes available after a successful WAV save and opens the export folder. |
| Keep garden | Names and keeps a complete recipe for this visit, including all switches, MASTER and the four flower steps. Enter confirms; Esc or Back cancels. Closing clears it. |
| Specimens / Kept gardens | Shows all eight illustrated discoveries, or restorable cards with actual recipe thumbnails. Select a specimen to keep its clue visible while adjusting sounds. Kept gardens have arrows when more than four are stored. |
| A gentle nudge / Show exact recipe | Changes the amount of help in the selected field note. Nudges react to the latest controls, including a switched-off ingredient or four resting flowers. No recipe is applied automatically. Close the note to return to the unobstructed garden. |
| New discovery / View specimen | Shows the unlocked name and a short celebration, then sends a leaf into the notebook. View specimen selects that shelf. The x dismisses the notice. Rapid discoveries queue in order, and naming a garden pauses the notice timer. |
| Letters / Open invitation / Share this garden | Opens an optional letter, accepts its wish, then checks broad conditions. Recipe numbers are optional. A mismatch pulses the letter border and shows NOT QUITE YET with a specific unmet LEVEL or ON/OFF requirement. Close the letter with its x or the Letters button. Playback remains accessible above the letter. |
| Next note | Leaves the current invitation without a penalty; keeps previous stamps. |
| Switch to another window | Stops playback; press Play after returning. |

The living garden combines a painted background with live botanical layers. During
playback, each bell onset lights its assigned flower with the note's attack and
decay; the one-second bass pulse moves light through the roots. The audio and
these gestures share `bell_pattern()` and `bass_pulse()` and use the playback
clock, including the newly accepted pattern after an update. This is scheduled
visual feedback, not analysis of the speaker output. Stopping or muting the
relevant sound removes its sound-led gestures; the garden can still be previewed.
Levels, MASTER and individual ON/OFF switches rebalance existing running layers,
preserving the phrase position. Making everything silent stops playback.
Clicking a flower regenerates only the Bells layer. The replacement bell buffer
is rotated to the current loop position, preserving the playback origin and
letting Rain and Bass continue. The flower edit is visible immediately; its
sound starts when the updated buffer is ready. Changing DROPS, PITCH, SPARKLE
or a preset prepares a new pattern (`UPDATING`),
usually in under a second on the development computer, then restarts the
four-second phrase with a short transition. Rapid mouse moves are combined so
the interface follows the latest slider position.

## Mistakes and interruptions

An unsuitable shared recipe shows an orange **NOT QUITE YET** panel beside the
Share button, the number of unmet conditions, and one concrete adjustment to
try next. The border pulses briefly on every rejected click. The explanation
stays after the pulse and clears when controls change or another note opens.
Sharing again checks the latest recipe. Completed notes retain their stamp and
cannot be rejected by a rapid second click. No error sound is played.

[Preview the wrong-recipe feedback](docs/wish-feedback.gif) (scripted capture).

The upper **VOLUME / LEVEL** slider controls whether an ingredient can be heard.
DROPS, PITCH and SPARKLE modify that ingredient; they are not separate sound
sources. At LEVEL zero, raise that upper slider to enable the lower control.
If the ingredient is OFF, switch it on as well. MASTER and playback remain
independent: stopping playback still allows editing an enabled ingredient.

![Disabled parameter controls with instructions](docs/controls-muted.png)

- **Everything is off / all levels are zero:** Play explains how to make the
  mix audible. Saving a silent recipe gives a message rather than a misleading file.
- **All four flowers rest:** Bells is silent even with a positive LEVEL. Click
  one flower to bring a note back. Discovery and visitor checks treat the absent
  Bells as zero, and their feedback can ask for a lit flower. Rain or Bass may
  still play and be kept. A Bells-only garden with four resting flowers cannot
  be kept or exported as a misleading silent result.
- **No audio device:** the interface and WAV export remain available. Check the
  selected output device and press Play again to retry the connection.
- **Repeated clicks:** Play toggles one playback state. Save has a short cooldown;
  each completed export gets a unique name and never replaces an earlier export.
- **Stop while the sound is updating:** playback remains stopped after the update.
- **Folder cannot be written:** a save error appears; the app remains usable.
- **Export folder cannot be opened:** the saved files remain intact and a
  message explains their location. If the saved file was moved, save again.

If you hear nothing, check the ON/OFF buttons, levels, lit flowers, MASTER and device volume.
If setup cannot download a dependency, keep the launcher message and retry when
the connection is available. No service credentials are needed.

## A fresh visit each time

Every launch starts with **0/8 discoveries, 0/3 visitor stamps and no kept
gardens**. Current recipe controls return to their initial values, with flowers
1 and 3 lit. Progress and
cards live only in memory for this window, so the next visitor starts fresh.
Within one visit you can still name, keep, page through and restore garden cards.
The Reset button resets sound controls while retaining that visit's progress;
close and reopen the app for a completely fresh visit.

The app does not read or write progress files during normal use. Older
`out/gardens/` snapshots are left intact and are ignored on startup. Explicitly
exported WAVs and their recipe files under `out/mixes/` remain on disk; use
**Save 8-second WAV** before leaving if you want to keep an audio result.

Names can contain 1-28 characters, including Chinese on Windows. Empty names
receive an inline message. A completely empty garden cannot be kept; muting
MASTER is allowed because it only controls listening volume. The naming dialog
and collection area explain that kept cards last until the window closes.
New recipes include a four-boolean `flower_steps` field; a malformed field is
rejected. Existing explicit archives without that field use the starter melody
when read. Normal startup still ignores those archives.

## Files

```text
app.py            window, naming, visitor/collection controls and audio playback
backdrop.py       cached mist gradient and botanical surround
foliage.py        shaded plant borders and decorative window margins
artwork.py        cached local paintings, transparent sprites and satin materials
assets/glass/    painted scenery, glass sprites, attribution and generation prompts
garden.py         discoveries, wishes and validated cards for the current visit
fieldguide.py     listening clues, contextual nudges and optional composing experiments
garden_view.py    landscape plus flower/root gestures from the shared sound timing
raster.py         native-pixel drawing from the shared logical layout
specimens.py      eight collectible miniatures, procedural fallback and filing animation
sound.py          Mix state, shared note timing, synthesis and WAV/recipe export
start.cmd         Windows launcher with a project-local runtime/cache
test_sound.py     signal and export checks; Python standard library only
test_loops.py     Rain/Bass seam energy, continuous phase, tuning and WAV joins
test_ui.py        event-handler checks using silent SDL test devices
test_garden.py    fresh visits, discovery, wish, card and legacy archive checks
test_rhythm.py    shared note onsets, flower envelopes and muted rhythm gestures
test_melody.py    four-beat audio, Sparkle independence and cached layer checks
test_flower_view.py four-flower geometry, beat lights and muted-preview checks
test_resolution.py native 2K/4K text, geometry, input and resize checks
test_exploration.py onboarding, layered clues, solo listening and keyboard interaction
test_artwork.py   optional asset failures, sprite transparency and wide-scene edges
README.md         idea, controls, run instructions and limitations
PROCESS.md        development decisions, AI use and real user-trial status
CREDITS.md        course inspiration and software/font credits
docs/             interface screenshot, verification notes and sample sound
out/              local exports/check outputs; excluded from version control
```

`.uv-cache/`, `.python/`, `.backups/` and generated `out/` files are ignored.
The screenshot and intentionally prepared demonstration WAV under `docs/` are
shareable project materials. No borrowed recordings are required.

## Check it

After the PowerShell setup above:

```powershell
uv run --no-project --managed-python --python 3.12 test_sound.py
uv run --no-project --managed-python --python 3.12 test_loops.py
uv run --no-project --managed-python --python 3.12 test_ui.py
uv run --no-project --managed-python --python 3.12 test_garden.py
uv run --no-project --managed-python --python 3.12 test_rhythm.py
uv run --no-project --managed-python --python 3.12 test_melody.py
uv run --no-project --managed-python --python 3.12 test_flower_view.py
uv run --no-project --managed-python --python 3.12 test_resolution.py
uv run --no-project --managed-python --python 3.12 test_exploration.py
uv run --no-project --managed-python --python 3.12 test_artwork.py
```

The sound checks compare real sample changes, pitch, silence, headroom,
repeatability and exported bytes. UI checks exercise the real handlers with
silent test devices; they do not prove speaker output or replace a human trial.
Check outputs remain under `out/`.

See [verification notes](docs/VERIFICATION.md) for the checks actually performed.
The current [16-second Rain + Bass loop preview](docs/rain-bass-seamless.wav)
repeats four times, with joins at 4, 8 and 12 seconds (both levels at 100%,
Drops at 92, pitch A3, Master at 70%, Bells off). An earlier
[8-second four-flower example](docs/flower-melody.wav) and
[rain-only reference-profile preview](docs/rain-only-v4.wav) are also available
when someone cannot run the app. They illustrate the sound; the screenshot and controls table
explain the interaction. The [unlock demonstration](docs/discovery-unlock.gif)
shows a named specimen being filed into the notebook; the
[rejected-share demonstration](docs/wish-feedback.gif) shows a visitor's specific
adjustment feedback. Both are silent scripted captures of the current interface.
A sound-enabled screencast and live website have not been produced.

## What one piece of the code does

In `Lab.move_slider()` a user's drag changes `mix.levels[index]`. `changed()`
updates the volumes of the existing Sound objects, so the phrase keeps moving.
`draw_garden()` uses that same Mix to change rain, moss, root movement and flowers;
`Garden.discover()` checks whether a new landscape has appeared. Naming a card
saves the recipe; restoring it supplies a new Mix without changing the saved one.
`mix_layers()` combines the cached ingredients with that same recipe for the
exported WAV. Character controls ask the worker to make new ingredients;
volume-only changes reuse them. `bell_pattern()` supplies the exact note start
samples to both synthesis and flower-light envelopes; `bass_pulse()` supplies
the same strength cycle to sound and roots. This is the connection between
**input, program response and feedback**.

For the new direct interaction, `Lab.toggle_flower()` changes one boolean in
`mix.flower_steps`. `bell_pattern()` translates enabled steps into sample onsets
at 0, 1, 2 and 3 seconds; both the bell generator and flower lights read those
onsets. A cached Rain/Bass pair is reused, and the new bell buffer joins at the
current phrase position. Kept cards and exported JSON copy all four booleans,
so restoring a card or exporting audio uses the same composition.

## Limits and submission status

This is a deliberately small sound garden: eight landscape discoveries and three
visitor notes. It is not an endless simulation. The value comes from exploring
and keeping different sound/visual combinations. Current
Rain uses filters fitted to the measured spectrum of the student's
[Minecraft rain reference](https://www.bilibili.com/video/BV1Pe411x7JY/), with
seeded noise and short strength changes. The
[measurement summary](docs/rain-reference-profile.json) records the reference
window and fitted coefficients. NumPy was used only for local analysis; the app
keeps its existing Python/Pygame setup. No reference audio is needed to run it.

The tonal impact/resonance grains in v2 were removed after listening feedback;
the student also rejected v3 and supplied this concrete reference. The
[first-version scene](docs/rainy-window.wav) and
[v2](docs/rain-only-v2.wav) / [v3](docs/rain-only-v3.wav) rain samples are kept
as iteration references. New recipes identify the current rain model as
`minecraft-reference-v4`. The Bilibili recording is used for local analysis and
is not redistributed; exported WAVs are newly synthesized.
Rain and Bass now repeat without a fade at every four-second boundary. Rain
filters first run through a discarded copy of the noise, so the returned loop
starts with the preceding lap's filter history. Bass uses whole cycles per loop;
the largest tuning adjustment is less than one cent. Its one-second breathing
pulse is retained. Initial Play and deliberate pattern changes still use short
transitions. New recipes also record `loop_model: periodic-rain-bass-v1`;
the older preview WAVs retain their original synthesis for comparison.
Patterns are fixed four-second loops with four editable bell beats; users toggle
notes rather than placing them freely or selecting their pitches. Recipes
can be restored through kept garden cards. Arbitrary exported JSON files cannot
yet be imported through the interface. Slider controls need a pointer. Headroom
prevents digital sample clipping; it cannot determine an appropriate device volume.
Live playback uses Pygame's 16-bit mixer and quantized gain controls; the exported
WAV is mixed from the same source layers and exact recipe values, so tiny rounding
differences from live output are possible. Neither the garden animation nor the
export is a recording of the microphone or speakers.

