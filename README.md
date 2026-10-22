# Sound Alchemy / 声音炼金台

**Grow a little world with sound.**

A small Python experience for someone who wants to play with sound without
learning a music editor. Rain nourishes moss, Bass wakes roots and Bells open
flowers and firefly lights. Explore freely, discover landscapes, name and keep
your favourite gardens, or follow an optional visitor invitation.

![Sound Alchemy desktop interface](docs/screenshot.png)

[Watch the garden loop](docs/garden-loop.gif) (silent, scripted demonstration
using the actual application renderer; not a recording of a user trial).

## The interaction

1. Move a slider and watch the garden respond immediately. Press **Play your mix**
   when you want to hear it. A stopped speaker still allows a visual preview.
2. Explore four landscape discoveries. Click an unfound discovery card for a
   clear recipe hint; there is no timer, score or wilting penalty.
3. Choose **Keep garden**, give it a name and press Enter. In **Kept gardens**,
   click a card to restore its exact sound controls and landscape, then press Play.
4. For a little direction, **Open invitation** on a visitor note. Its hint gives
   generous ranges. **Share this garden** checks them and awards a thank-you stamp.
   **Next note** lets you leave it and try another. Free exploration always works.
5. **Reset** restores the initial sound controls and stops playback. It preserves
   discoveries, cards and stamps. **Save 8-second WAV** exports sound and a recipe;
   **Open exports** opens the folder.

The short loop is **adjust > see/hear > discover > keep > try another garden**.
The three optional wishes provide gentle goals. They accept multiple recipes;
there is no exact sound-matching test. The garden responds directly to control
state, rather than analysing speaker output. Lowering MASTER leaves it intact.

All sounds and graphics are generated locally. Nothing plays on startup, and
switching windows stops playback. No accounts, microphone or services are needed.

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

## Controls and feedback

| Action | Response and feedback |
| --- | --- |
| Click a preset | Loads a different combination; the selected button is highlighted. |
| Click an ingredient's ON/OFF button | Adds/removes that ingredient; the card and label change. |
| Drag LEVEL | Changes the running sound volume and the corresponding rain, roots or flowers. The phrase keeps its position. |
| Drag DROPS / PITCH / SPARKLE | Changes the pattern; Sparse/Dense, Lower/Higher and Fewer/More notes explain the direction. Counts show overlapping soft rain textures / bell notes per four-second loop; Rain is a continuous curtain rather than separate audible taps. |
| Drag MASTER | Changes all running layers immediately, including the recipe used for export. |
| Play your mix / Stop listening / Space | The single main button starts or stops playback; repeated presses do not stack copies. Stopping keeps the recipe. |
| Escape | Stops immediately; later background work cannot restart it. |
| Reset / R | Stops and restores the initial Rainy window controls; keeps discoveries and saved cards. |
| Save / S | Writes a new 8-second WAV and recipe under `out/mixes/`. |
| Open exports | Becomes available after a successful WAV save and opens the export folder. |
| Keep garden | Names and stores a complete recipe, including all switches and MASTER. Enter confirms; Esc or Back cancels. |
| Discoveries / Kept gardens | Shows four discovery hints or restorable cards. Arrow buttons page through larger collections. |
| Open invitation / Share this garden | Accepts an optional wish, then checks its broad conditions. A mismatch offers another hint. |
| Next note | Leaves the current invitation without a penalty; keeps previous stamps. |
| Switch to another window | Stops playback; press Play after returning. |

The waveform comes from the actual source layers mixed with the current recipe.
The living garden maps ingredient controls to procedural geometry. Its animation
is a visual metaphor; it does not claim to measure sound samples or speaker output.
Levels, MASTER and individual ON/OFF switches rebalance existing running layers,
preserving the phrase position. Making everything silent stops playback.
Changing DROPS, PITCH, SPARKLE or a preset prepares a new pattern (`UPDATING`),
usually in under a second on the development computer, then restarts the
four-second phrase with a short transition. Rapid mouse moves are combined so
the interface follows the latest slider position.

## Mistakes and interruptions

- **Everything is off / all levels are zero:** Play explains how to make the
  mix audible. Saving a silent recipe gives a message rather than a misleading file.
- **No audio device:** the interface and WAV export remain available. Check the
  selected output device and press Play again to retry the connection.
- **Repeated clicks:** Play toggles one playback state. Save has a short cooldown;
  each completed export gets a unique name and never replaces an earlier export.
- **Stop while the sound is updating:** playback remains stopped after the update.
- **Folder cannot be written:** a save error appears; the app remains usable.
- **Export folder cannot be opened:** the saved files remain intact and a
  message explains their location. If the saved file was moved, save again.

If you hear nothing, check the ON/OFF buttons, levels, MASTER and device volume.
If setup cannot download a dependency, keep the launcher message and retry when
the connection is available. No service credentials are needed.

## Your local collection

Discoveries, kept garden recipes and visitor stamps survive a restart under
`out/gardens/`. Each completed save writes a **new** numbered JSON snapshot;
previous snapshots are preserved. The newest valid snapshot loads on startup.
If a newer file is damaged, the app reports recovery from an earlier snapshot.
If disk saving fails, the app explicitly says progress is available this session
only. Try keeping the garden again after fixing folder permissions.

Names can contain 1-28 characters, including Chinese on Windows. Empty names
receive an inline message. A completely empty garden cannot be kept; muting
MASTER is allowed because it only controls listening volume. Local names and
collections are ignored by Git. There is no delete button in this small version.

## Files

```text
app.py            window, naming, visitor/collection controls and audio playback
garden.py         discoveries, wishes, validated cards and recoverable snapshots
garden_view.py    procedural landscape drawn from the current Mix
sound.py          Mix state, synthesis and WAV/recipe export
start.cmd         Windows launcher with a project-local runtime/cache
test_sound.py     signal and export checks; Python standard library only
test_ui.py        event-handler checks using silent SDL test devices
test_garden.py    discovery, wish, collection round-trip and recovery checks
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
uv run --no-project --managed-python --python 3.12 test_ui.py
uv run --no-project --managed-python --python 3.12 test_garden.py
```

The sound checks compare real sample changes, pitch, silence, headroom,
repeatability and exported bytes. UI checks exercise the real handlers with
silent test devices; they do not prove speaker output or replace a human trial.
Check outputs remain under `out/`.

See [verification notes](docs/VERIFICATION.md) for the checks actually performed.
An [8-second default scene](docs/rainy-window-v4.wav) and a
[rain-only preview](docs/rain-only-v4.wav) are available when someone
cannot run the app. It illustrates the sound; the screenshot and controls table
explain the interaction. The silent scripted GIF above shows visual changes,
naming and collections. A sound-enabled screencast and live website have not
been produced.

## What one piece of the code does

In `Lab.move_slider()` a user's drag changes `mix.levels[index]`. `changed()`
updates the volumes of the existing Sound objects, so the phrase keeps moving.
`draw_garden()` uses that same Mix to change rain, moss, root movement and flowers;
`Garden.discover()` checks whether a new landscape has appeared. Naming a card
saves the recipe; restoring it supplies a new Mix without changing the saved one.
`mix_layers()` combines the cached ingredients with that same recipe for the
waveform and WAV. Character controls ask the worker to make new ingredients;
volume-only changes reuse them. This is the connection between **input,
program response and feedback**.

## Limits and submission status

This is a deliberately small sound garden: four landscape discoveries and three
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
Patterns are fixed four-second loops; recipes
can be restored through kept garden cards. Arbitrary exported JSON files cannot
yet be imported through the interface. Slider controls need a pointer. Headroom
prevents digital sample clipping; it cannot determine an appropriate device volume.
Live playback uses Pygame's 16-bit mixer and quantized gain controls; the exported
WAV is mixed from the same source layers and exact recipe values, so tiny rounding
differences from live output are possible. The waveform is a source-mix preview,
not a microphone or speaker recording.

The code and local checks are ready for a first trial. **A real user trial,
personal review of the AI-assisted work, Git development commits, public GitHub
publication and the Canvas submission are still pending.** Do not present the
automatic checks as another person's trial. See `PROCESS.md` and `CREDITS.md`.

