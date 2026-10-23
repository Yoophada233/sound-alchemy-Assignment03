# Verification / 22 October 2026

## Environment

- Windows desktop; display driver reported by Pygame: `windows`.
- Desktop size reported: 1920 x 1080; current garden canvas: 1280 x 900.
  The earlier listening-lab canvas was 1180 x 860.
- Project-local CPython 3.12.14; Pygame 2.6.1.
- Audio format accepted by the local mixer: 22,050 Hz, signed 16-bit, mono.
- Source and generated files remained in the new `sound-alchemy/` folder.
  Dependencies/cache and Python were placed in `.uv-cache/` and `.python/`.
  No Git init, commit, push, public deployment or Canvas submission was performed.

## Executed checks

### Mist greenhouse visual packaging / 23 October 2026

- All 38 existing interaction checks passed. No gameplay/model tests were added
  for a cosmetic change. The application uses the same controls and hitboxes.
- Default, muted, rejected-share, unlock and naming captures were rendered and
  visually inspected. Text, disabled instructions, orange rejection feedback,
  unlock banner and modal controls remain readable. Botanical line art stays
  mostly near margins and uses low contrast.
- New `backdrop.py` produces a deterministic opaque surface without display
  initialization, file access or random-state mutation. The drawing agent checked
  1x1, 35x21, 600x900, 1280x900 and 1920x1080 sizes; the 1280x900 render took about
  0.023 seconds locally. The app caches it once, along with panel-shadow surfaces.
- Main screenshot, muted-control example, wrong-recipe example and unlock
  example were refreshed. The feedback GIFs were regenerated with the current
  palette. Other state captures are under ignored `out/mist-theme/`.
- The offline Windows launcher successfully generated `out/mist-launcher.png`.
- Snapshot: `.backups/before-mist-theme-20261023-011948/`. Changed UI palette,
  decorative drawing/shadows, documentation and examples. The sound generator,
  scene rules and garden renderer remain unchanged. This checks rendering and
  behavior; aesthetic preference and a real user trial still need human feedback.

### Discovery rewards and eight landscapes / 23 October 2026

- `test_ui.py`: all 38 checks passed. New coverage verifies visible named reward
  text and NEW! cards without autoplay, no repeated reward for an existing
  discovery, ordered rapid unlocks, first unlocks from keeping/sharing, page-2
  hints and navigation, pausing while naming, normal expiry and bounded/finished
  celebration pixels. Restart coverage also checks cleared notification state.
- `test_garden.py`: all 25 checks passed. All eight scenes are reachable and
  discovered once; original IDs/order/recipes stay stable. New checks exercise
  required enabled ingredients, inclusive boundaries, character requirements,
  master independence and new-card restore/explicit-archive round trips.
- A drawing comparison by the assistant reviewer found the original four
  scenes pixel-identical to the pre-change renderer at the same parameters/time.
  Its most complex new scene plus celebration averaged about 13 ms/frame in
  the local Pygame environment. This is a local render measurement, not a
  guarantee for other hardware.
- New-scenery gallery, full unlock view and guide page 2 were rendered and
  visually inspected. Current main screenshot shows 0/8. Shareable examples are
  `docs/discovery-unlocked.png` and `docs/discovery-unlock.gif` (40 scripted
  frames, five seconds, silent). Other captures remain in ignored
  `out/discovery-rewards/`. These are implementation captures, not user trials.
- Native Windows smoke check rendered Starlit canopy and its unlock on guide
  page 2, confirmed no autoplay, then started/stopped playback. Closing/reopening
  reset progress, guide page and notification queue. The offline Windows launcher
  also completed a fresh screenshot invocation. These are API/runtime checks,
  not a human judgment of reward prominence or listening quality.
- The eight pre-existing collection/export files still match the earlier
  SHA-256 manifest; `sound.py` remains identical to its pre-revision source.
- Snapshot: `.backups/before-discovery-rewards-20261023-005223/`. Changes cover
  scene rules/drawing, UI reward queue and guide pagination, related tests,
  instructions and examples. No sound-source, launcher, dependency or normal
  visit-persistence changes were required.

Earlier four-scene counts below are historical. Current normal launch starts
with eight undiscovered entries, three unfinished wishes and an empty collection.

### Fresh visits / 23 October 2026

- `test_ui.py`: all 31 checks passed. Updated collection tests distinguish
  same-visit restoration from persistence. New restart coverage places a fully
  completed legacy archive beside the app's test output, then verifies a new
  window has no discoveries, stamps or cards and leaves that file byte-identical.
  Other coverage verifies normal gameplay never calls progress persistence.
- `test_garden.py`: all 20 checks passed. A default Garden is memory-only;
  collecting/restoring/completing works without filesystem reads or writes, and
  a new Garden is empty. Existing explicit-folder archive checks still pass for
  preservation of earlier files; normal application startup does not use them.
- A native Windows window completed all four discoveries and three wishes and
  kept one garden, then closed. Reopening through the default Lab constructor
  showed 0/4 discoveries, 0/3 stamps and no cards, with initial sound controls,
  first note selected and no autoplay. Before/after captures are under isolated
  ignored `out/fresh-visit-check/`.
- An offline fresh-process screenshot invocation regenerated
  `docs/screenshot.png` with empty progress and the visit-lifetime notice.
- SHA-256 checks against the pre-change manifest confirmed all 8 pre-existing
  collection/export files were still present and byte-identical. No progress
  files or WAV exports were deleted. Sound synthesis and launcher are unchanged.
- Snapshot: `.backups/before-fresh-visits-20261023-002215/`. Changed application
  startup/progress calls, the default Garden lifetime, corresponding tests,
  instructions/process notes and the main screenshot.

This supersedes earlier notes about automatic collection restoration and
collection disk-save errors. Exported WAV/recipe files still persist. Native
checks establish runtime state changes, not a person-observed usability trial.

### Rejected Share feedback / 23 October 2026

- `test_ui.py`: all 30 checks passed. New cases exercise rejected sharing through
  the button handler, inline visitor-card text, repeated attempts after the pulse
  settles, unchanged recipe/rewards, clearing after edits or switching notes,
  successful resubmission and a rapid second click on a completed note.
- `test_garden.py`: all 19 checks passed. New coverage checks direction/range
  instructions, disabled ingredients and exact acceptance boundaries. Existing
  discovery and collection checks continue to pass. The acceptance ranges and
  error messages share `WISH_LIMITS`; the numerical conditions are unchanged.
- Rejected, ingredient-OFF and successful visitor-card views were rendered and
  visually inspected. Captures are in isolated ignored `out/wish-feedback/`;
  `docs/wish-feedback.png` and `docs/wish-feedback.gif` show the rejected state.
  The animation captures changed border pixels at different elapsed times.
- The short border animation ends while inline guidance remains. Editing the
  recipe or changing notes clears the stale guidance. No sound effect is added.
- Snapshot: `.backups/before-wish-feedback-20261023-000852/`. Changed application,
  wish-feedback logic, related tests, instructions and demonstration assets.
  Sound synthesis, dependency setup and saved-data format are unchanged.
- The checks use scripted input and silent SDL rendering. This is implementation
  evidence; no physical mouse, speaker or other-person acceptance is claimed.

### Muted parameter controls

- The complete `test_ui.py` suite passed: 28 checks. Two new scenarios cover all
  three ingredients: LEVEL zero rejects clicks/drags without changing parameter
  state or scheduling new sound work, and OFF retains the parameter while still
  allowing volume edits. Raising LEVEL or switching back ON restores editing
  with the original parameter value intact.
- Enabled, LEVEL-zero and OFF states were rendered. The three-card muted view
  in `docs/controls-muted.png` and the mixed ON/OFF view under ignored
  `out/control-hints/` were visually inspected for readable recovery hints and
  layout. The main screenshot was refreshed with VOLUME / LEVEL labels.
- Recovery snapshot: `.backups/before-control-hints-20261022-235603/`.
  Changes cover `app.py`, `test_ui.py`, instructions/process notes and screenshots.
  Sound synthesis, dependencies, stored recipes and the launcher are unchanged.
- These checks use silent SDL devices and scripted input. Physical mouse and
  speaker acceptance of this particular UI revision remain for the next trial.

### Sound garden revision

- `test_sound.py`: 12 checks passed. SHA-256 confirms `sound.py` is identical
  to the pre-garden snapshot: Rain v4, Bass and Bells synthesis are unchanged.
- `test_garden.py`: 18 checks passed, including all four discoveries, all three
  wishes, overlapping scene/wish conditions, independent restored recipes,
  duplicate names, invalid names/data, snapshot preservation and corrupt-file
  fallback. MASTER does not affect creative matching.
- `test_ui.py`: 26 checks passed, including the original audio/export checks
  and discovery without autoplay, naming without shortcut leakage, IME
  composition state, collection paging/restoration, optional wishes, reset
  preservation and recoverable disk-save failure.
- `docs/screenshot.png`, Chinese-name entry and a four-card completed collection
  were rendered and visually inspected. Chinese names use the installed Windows
  Microsoft YaHei font rather than missing-glyph boxes. A scripted IME test does
  not establish behavior of every physical keyboard or input method.
- `docs/garden-loop.gif`: 64 frames, eight seconds, generated by scripted actions
  through the real application renderer. It is silent and does not represent an
  observed person or a user trial. Demonstration cards live in an isolated folder
  under ignored `out/garden-demo/`; they do not populate the user's collection.
- Native Windows display and audio initialized at `(22050, -16, 1)`. A newly
  created app played, stopped, saved a garden, closed, reopened, and restored the
  card while remaining stopped. This confirms API/runtime behavior, not enjoyment
  or speaker quality. The smoke-test collection is isolated under `out/native-garden/`.
- `start.cmd --screenshot out/garden-launcher.png` completed with offline uv,
  using the existing project runtime and dependency cache.
- Recovery source snapshot: `.backups/before-garden-20261022-230822/`.
  New modules are `garden.py`, `garden_view.py` and `test_garden.py`; application,
  interaction tests, documentation and screenshot were updated. No dependency,
  launcher or sound-source change was required. The separate
  `Assignment-3-sound-alchemy` copy and its Git repository were not modified.

The student asked for more play after reporting boredom with the mixer. Whether
the garden extends engagement remains a human trial question; no retention result
or other-person observation is claimed.

### Earlier audio and mixer checks

| Check | Observed result |
| --- | --- |
| Python source parse | `app.py` and `sound.py` parsed successfully. |
| Sound tests | 12 passed: original signal/export checks plus procedural-rain repeatability, sparse/dense energy difference, bounded samples/loop ends, invalid density and limits on dominant impact peaks/window-energy bursts. |
| Interaction tests | 16 passed: original interaction checks plus level/master continuity, a burst of mouse moves followed by release/Stop, rejoining a muted layer, latest gains during pattern generation, saved-folder action, folder-viewer error recovery and a moved export. |
| Final runtime | Both test files passed using the installed project-local Python 3.12 environment via uv. |
| Fresh PowerShell setup | README setup commands succeeded; an offline screenshot invocation generated `out/fresh-terminal.png`. |
| Windows launcher | `start.cmd --screenshot out/launcher-check.png` exited successfully. |
| Interface inspection | Full application canvas rendered to `docs/screenshot.png`; inspected for clipped text, overlap and control layout. |
| Native audio connection | Local mixer initialized and played. In the usability revision, the running layer buffers and playback origin were unchanged after level/master edits; Stop then reported no active playback. |
| Native export-folder action | Windows accepted an open-folder request for the real `out/mixes/` directory. The sandbox denied this OS action during the first check; it succeeded in a narrowly escalated directory-only check, without system-setting changes. |
| Demo WAVs | Current `docs/rain-only-v4.wav` and `docs/rainy-window-v4.wav`: 8 seconds, mono, 16-bit PCM, 22,050 samples/s. Earlier files remain available for comparison. |
| Export preservation | A second export used a different name; the first WAV remained byte-identical. |
| Sound preservation | Bass and Bells samples match the pre-rain-revision source at minimum/middle/maximum controls. Preset values remain unchanged; only Rain synthesis changes the new mixed sample. |
| Duplicate Stop removal | The standalone Stop control and its click route were removed. Reset moved next to the main Play/Stop button. The interruption test now stops through that main button. |
| Rain revision | Old and new rain-only renders at identical level/master settings had RMS 0.0103 and 0.0100 respectively. The change is texture/envelopes, not simply an overall volume boost. |
| Native revised-rain playback | The local mixer accepted a rain-only playback request and reported stopped after Stop. This establishes device/API operation, not a human judgment of realism. |
| Soft-rain v3 | No resonant/tonal impact grains remain. Default raw peak/RMS is 4.89 and maximum 50 ms-window RMS / median is 1.31, supporting a more even curtain without dominant knocks. Rain-only sample RMS is 0.01126 at the same level/master used for earlier comparisons. |
| Reference acquisition | Agent Reach `bili video` and `bili audio --no-split` succeeded for BV1Pe411x7JY. The 30,246,861-byte source remains in ignored `out/reference/`. |
| Reference decoding | Windows' default 48 kHz PCM transcoder decoded 60–90 seconds; the analysis used a band-limited conversion to 22.05 kHz mono. No new decoder/package installation was needed. |
| Reference-guided v4 | Absolute band-fraction error over nine bands: v3 0.3028, v4 0.0260. Spectral centroid: reference 2169.94 Hz, v4 2186.42 Hz. 50 ms RMS variation: reference 0.1143, v4 0.1069. Full figures and coefficients are in `rain-reference-profile.json`. |
| Native v4 WAV playback | The local mixer loaded the final rain-only WAV, reported active playback, and reported stopped after Stop. Both final WAVs reopened with the expected mono / 22,050 Hz / 8-second format. |

Tests use the project's own local runtime. Deliberate mocked export and
folder-viewer errors print console messages; those recovery tests pass.
The usability revision preserves a source snapshot under
`.backups/before-usability-20261022-183958/` and keeps prior exports.
The rain revision also preserves sources and the original sample under
`.backups/before-rain-20261022-202242/`. Sidecar recipes now identify
the former v2 model. Before v3, another snapshot was made under
`.backups/before-soft-rain-20261022-204310/`; new recipes identify
`rain_model: soft-rain-v3`.
Before v4, sources were preserved under
`.backups/before-reference-rain-20261022-214522/`. Current sidecars identify
`rain_model: minecraft-reference-v4`. The original recording is not a runtime
asset and remains outside the shareable project materials.

## What this evidence does not establish

- The UI event tests use SDL dummy video/audio drivers. They validate the app's
  event/state behavior, not physical mouse input, speaker quality or a human trial.
- The native audio check confirms the output API accepted and stopped playback;
  no human listening assessment was recorded and system output was not recorded.
- Live sound gains are quantized by Pygame (for example requested 0.24 was
  reported as 0.234375). Export and waveform use the exact source recipe;
  they do not claim byte identity with speaker output.
- The screenshot is from the real application renderer in its silent capture
  mode. It is a static layout check, not a recording of a person using the app.
- Real unplug/reconnect behavior and other computers/operating systems have not
  been manually tested. Unavailable-device handling was exercised in the tests.
- A real user trial and the student's own explanation/reflection are pending.
- The student reported the first rain as too noisy and rejected v2 as sounding
  like plastic knocks. V3 was also rejected. V4 was fitted to their concrete
  Minecraft reference; listening acceptance remains pending. Spectral/statistical
  agreement cannot establish naturalness, pleasantness or exact reproduction.
- Public repository access, Git history and submission requirements remain pending.

