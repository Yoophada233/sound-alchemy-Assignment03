# Verification

## Environment

- Windows desktop; display driver reported by Pygame: `windows`.
- Desktop size reported: 1920 x 1080; logical notebook layout: 1280 x 960.
  The current content canvas follows the window's native viewport pixels.
  The earlier garden canvas was 1280 x 900; the listening lab was 1180 x 860.
- Project-local CPython 3.12.14; Pygame 2.6.1.
- Audio format accepted by the local mixer: 22,050 Hz, signed 16-bit, mono.
- Earlier revisions used the `sound-alchemy/` source folder; the current
  29 October revisions use the `Assignment-3-sound-alchemy/` Git checkout.
  Dependencies/cache and Python are local to `.uv-cache/` and `.python/`.
  Individual historical sections describe their own modification boundaries;
  this record is not evidence of a Canvas submission or a live website.

## Executed checks

### Dimensional edge foliage / 30 October 2026

- Added four original ImageGen plant sprites in `assets/glass/foliage.png`:
  ivy, hanging leaves, fern/moss and a broad-leaf branch. The supplied current
  screenshot and earlier concept were style/layout references. The delivered
  atlas is 1254 x 1254 RGBA; the original file is preserved. Its left-row split
  uses the actual transparent gap at 54%, avoiding a cropped vine or stray leaf.
- `foliage.py` fits the shaded plants at native destination density and adds soft
  shadows. `backdrop.py` anchors the mist colour field to the page so wider window
  margins blend with it. Decorations sit behind text and controls; hit areas and
  the four playable flowers retain their coordinates. The plants are static 2D
  artwork suggesting depth, not real-time 3D geometry or newly interactive objects.
- The page and surrounding plants are built on initialization/resize and cached.
  **92 related checks passed**: artwork, resolution, UI and exploration tests.
  The asset-failure check was expanded and rerun with its four-test module; missing
  foliage leaves a working backdrop and surrounding window instead of preventing
  startup. Resolution tests exercise real handlers at 2560 x 1440 and 3840 x 2160.
- Actual SDL-rendered screenshots were inspected at 1280 x 960, 1920 x 1080 and
  3840 x 2160; a 2560 x 1440 capture was also produced. At 2K/4K the content canvas
  is 1920 x 1440 / 2880 x 2160 respectively, with text rendered at that density.
  Warm frame medians over 12 draws were 11.49 / 16.00 / 19.10 / 35.08 ms for those
  four window sizes. A guard confirmed no background/border rebuild during these
  draws. These are local silent SDL checks, not monitor testing on another PC.
- Updated `docs/screenshot.png`; added `docs/foliage-wide.png`. Both are actual
  application renders. Full-resolution review images and timing results are in
  ignored `out/foliage-review/`. Earlier interaction GIFs retain the former edges.
- Recovery copy and hashes: `.backups/before-foliage-border-20261030-183409/`.
  The sound synthesis, personal PROCESS, launcher and dependencies were not edited.
  No Git commit/push or real-person usability trial is claimed for this revision.

### Continuous Rain and Bass loops / 30 October 2026

- The student reported an audible interruption every four seconds. Both source
  buffers applied an 8 ms fade at each end, leaving a repeated dip. Several Bass
  pitches also ended partway through an oscillator cycle. Live playback already
  used SDL's repeating buffers; no timer-driven restart was needed or changed.
- Rain now warms the existing reference-profile filters with a discarded lap of
  the same seeded noise, preserving their state through the join. Its circular
  density envelopes and reference coefficients are unchanged. Bass closes whole
  cycles in four seconds without the edge fade. The maximum tuning difference is
  0.972 cents; A2/A3 are unchanged. The one-second pulse and Bells synthesis remain.
- At the reported settings (both levels 100%, Drops 92, Bass A3), an 8 ms window
  centred on the seam measured **-11.03 to -1.06 dB for Rain** and
  **-12.11 to -1.92 dB for Bass**, relative to the median ordinary window.
  The remaining variation reflects the rain texture and Bass breathing envelope.
  Excluding the first/last 50 ms, Rain's relative RMS sample difference from the
  backup was below 0.0005% at all three tested densities. This supports preserving
  the established timbre; it is not a listening acceptance claim.
- **169 regression checks passed** in the project-local Python environment.
  Five new signal/export tests cover seam energy at three Rain densities, boundary
  jumps/corners, all seven Bass phases and pitches, and the actual 8-second WAV.
  The two main seam checks were also run against the backup and correctly failed.
  Historical Rain/Bass PCM digests were replaced with the relevant independent
  flower-pattern check; twelve unchanged Bells PCM digests still pass.
- A new UI check verifies no restart at simulated loop boundaries. A separate
  **12.2-second real-time run with silent SDL devices** kept both original Sound
  buffers and the playback clock at 4.2, 8.2 and 12.2 seconds. No extra Play call
  occurred; Stop ended playback. This checks actual loop scheduling, not speakers.
- `docs/rain-bass-seamless.wav` contains four exact PCM repeats (16 seconds), with
  both levels 100%, Drops 92, A3, Master 70%, Bells off. Before/after isolated Rain,
  Bass and combined files plus numerical results are in ignored
  `out/seamless-loop-checks/1793355668675998100/`. The comparison uses equal gains.
  Every WAV was reopened and its duration and repeated bytes verified.
- New sidecar recipes identify `loop_model: periodic-rain-bass-v1`; `rain_model`
  remains `minecraft-reference-v4`. Previous demo WAVs are historical examples.
  Backup: `.backups/before-seamless-loops-20261030-181055/`, with file hashes.
  No UI, gameplay, launcher, dependency or personal PROCESS change was required.
  No physical-output recording or human listening trial was performed for this fix.

### Moonlit glass artwork / 30 October 2026

- Implemented the student's selected glass music-box direction with the deeper
  lake/mountain composition and softened natural textures. The live application
  uses four included PNGs plus separate native-resolution controls and effects;
  it does not use a flattened concept screenshot as its interface.
- Open/rest glass flowers retain their four separate beat positions, generous
  hit areas and synchronized lights. Rain, extra fern growth, root pulses,
  fireflies and scene accents still respond to the sound controls. Eight
  miniature specimens distinguish dim unobserved entries from lit discoveries.
- The dark palette covers the workbench, field notes, visitor error/success
  panels, collection, naming dialog and export menu. A full-width painting now
  fills the wide stage; the old repeated-column edge extension is not used for
  painted scenery. Fallback procedural rendering remains available if a PNG
  is absent or damaged.
- **163 regression checks passed**, including four asset checks for true alpha,
  usable sprite regions, missing/damaged files, procedural fallback and the
  wide-scene edge regression. Log: `out/art-review/tests-final.log`. The printed
  read-only-export and missing-viewer errors are intentional test cases.
  After the final static-console cache change, **87 UI, resolution and
  exploration checks passed again** (`out/art-review/ui-cache-final.log`).
- Inspected actual application captures at 1280 x 960, 2560 x 1440 and
  3840 x 2160. Their content canvases are respectively 1280 x 960,
  1920 x 1440 and 2880 x 2160. Text and controls stay native; the deliberately
  soft landscape uses a 1942 x 809 painting. Larger desktops retain the
  existing centered 4:3 composition.
- Cached the three static instrument cases in the native background. Warm
  preview samples after this change (20 frames each, silent SDL driver) had
  median times of approximately 11 ms, 18 ms and 33 ms at those window sizes.
  The earlier 4K pass took about 46 ms. These are local preview timings, not
  a universal FPS guarantee; live lights, recipe changes and larger windows
  can cost more. Records: `out/art-review/render-timing-final.json`;
  captures and resolution records: `review.json` and `native-*.png` there.
- A hidden **native Windows** window accepted posted flower, Play and held
  listening-focus keys, resized to 1600 x 900, and stopped on focus loss.
  This check used a silent audio driver; it is not a new speaker audition or
  a physical 4K-monitor acceptance test. Record: `out/art-review/native-smoke.json`.
- SHA-256 comparisons against the pre-change backup confirmed that `sound.py`,
  `garden.py`, `fieldguide.py`, `raster.py`, `PROCESS.md` and `start.cmd` were
  unchanged by this artwork pass. Existing uncommitted work was retained.
  The backup is `.backups/before-glass-garden-20261030-010149/`.
- Runtime PNGs and the short silent GIF demonstrations were regenerated from
  the app. They are scripted visual evidence, not a real user trial. Artwork
  credits and generation prompts are in `assets/glass/README.md` and `CREDITS.md`.
  No dependency, global setting, Git commit or remote was changed in this pass.

### Listening instrument and progressive field notes / 29 October 2026

- The single gold Play/Stop control sits above the flowers and stays accessible
  when a letter is open. A dismissible introduction responds to actual playback
  and flower edits. Larger seed-number buttons, RING/REST labels, hover feedback
  and keys 1-4 make the four-beat instrument explicit. The discovery notice now
  sits in the upper frame instead of covering the flowers.
- All eight specimens have a persistent listening clue, an optional contextual
  nudge and an explicitly requested numeric recipe. The clue stays selected
  during edits. After collecting, it offers a composing experiment. Visitors
  also start with descriptive clues and offer recipe numbers on request;
  rejected sharing retains its specific recovery feedback.
- Holding a Rain/Bass/Bells button or Q/W/E isolates that running layer through
  mixer gain only. Release restores the latest full mix without replacing its
  buffers or resetting its clock. Keyboard focus permits simultaneous slider
  editing. Mouse release outside the button, pointer departure, focus loss,
  Stop, Reset, naming and muting the focused ingredient are covered. The
  listening focus never changes the recipe, exported samples or discovery
  conditions. Sound-driven root/bell lights respect the focused layer.
- **159 regression checks passed**: the previous 137 plus 22 exploration checks.
  After the last letter-layout adjustment, **87 UI, resolution and exploration
  checks passed again**. Logs: `out/exploration-checks/regression.log` and
  `out/exploration-checks/final-ui-tests.log`. The printed read-only-folder and
  missing-folder-viewer errors are intentional test cases.
- Checks cover all eight reachable nudge routes, muted ingredients and resting
  flowers, help-text fit, held-key releases, newly generated audio while a focus
  key is held, naming input, and 2K/4K hit positions for the new controls.
  Letter paper blocks covered controls; hidden listening/Keep controls cannot
  receive clicks through it.
- A hidden native Windows window accepted posted number-key and focus-key
  events, resized to 1600 x 900 (1200 x 900 content), and stopped all mixer
  channels on focus loss. The real local mixer accepted 22,050 Hz / signed
  16-bit / mono. The probe used a gain that quantizes to zero, so it was silent;
  it verifies native APIs, not speaker quality or a person's understanding.
  Details: `out/exploration-checks/native-probe.json`.
- `start.cmd --screenshot out/exploration-checks/launcher-final.png` completed
  successfully through the documented launcher. No dependency was added.
- Current screenshots and silent GIF demonstrations were refreshed from the app
  renderer. The new `docs/listening-tour.gif`, `docs/listening-guide.png` and
  `docs/listening-focus.png` illustrate the changed experience. These use
  prepared inputs, not a user trial. Native-size 2560 x 1440 and 3840 x 2160
  offscreen frames are retained in `out/exploration-checks/`.
- Recovery snapshot, including the preceding uncommitted high-resolution work:
  `.backups/before-listening-exploration-20261029-011725/`. Its 15 originals were
  SHA-256 checked before editing. Only this checkout was changed. `PROCESS.md`,
  the synthesis implementation and the discovery rules were preserved. No Git
  staging, commit or push was performed. Physical 2K/4K displays, listening
  preference and a separate-person trial remain unverified for this revision.

### Native-resolution rendering and Windows DPI

- The earlier renderer enlarged a 1280 x 960 UI bitmap and a 748 x 310 garden.
  The new renderer uses those dimensions as logical coordinates, rasterizes
  typography and geometry at the destination density, and blits the finished
  frame at 1:1 pixels. The continuous backdrop colour field remains interpolated;
  its botanical line art is drawn at the current resolution.
- Rendering and input checks include 2560 x 1440 and 3840 x 2160 windows. Their
  content frames are respectively 1920 x 1440 and 2880 x 2160. Tests check native
  glyph pixels, garden working resolution, flower/slider hit positions,
  letterbox/popup interception, IME placement after resize, crisp thumbnails,
  saved-recipe preservation and return to a smaller window.
- Rendered before/after crops in ignored `out/resolution-checks/` were inspected
  at their original pixel sizes. They cover the title, small labels and garden.
  Only this `Assignment-3-sound-alchemy` checkout was changed; `PROCESS.md`,
  audio synthesis and the other working copy were left intact.
- A native Windows check confirmed `permonitorv2` awareness on the running app
  window at 96 DPI. Maximizing produced a 1920 x 1017 client surface and a
  1356 x 1017 native content frame. Actual 2K/4K hardware and moving between
  monitors at different Windows scale factors were not physically tested.
- Resolution-specific text/specimen images and two-entry garden/stage buffer
  caches avoid repeatedly allocating large surfaces. A regression exposed zero
  alpha copied from an alpha-disabled RGBA sky; a true RGB sky fixes it. The
  checks verify both an opaque sky and clean buffers without earlier glows.
- Recovery snapshot: `.backups/before-native-resolution-20261029-000101/`.
- Final regression: **137 tests passed** (54 UI, 31 garden, 12 sound, 10 rhythm,
  9 melody, 10 flower-view and 11 native-resolution checks). Output is retained
  under ignored `out/resolution-checks/regression-final.log`.
- Fifteen warm software-rendered frames averaged 21.55 ms at 2560 x 1440 and
  33.66 ms at 3840 x 2160 on this computer. These are local rendering measurements,
  not a guarantee for other monitors or computers. No render-resolution cap or
  quality reduction was applied to obtain them.
- `start.cmd --screenshot out/resolution-checks/launcher-final.png` succeeded.
  This revision does not add packages, modify global DPI settings, commit or
  push to GitHub, or count as a separate-person usability trial.

### Four flowers, one melody / 25 October 2026

The four numbered foreground flowers now select bells at seconds 0, 1, 2 and 3
of each loop. The default sounds flowers 1 and 3. Sparkle changes the existing
bell decay and garden glow without replacing the chosen beat pattern. Presets
retain the melody; Reset restores it. This supersedes the automatic bell-count
behaviour described in earlier entries below.

- **126 checks passed:** 54 UI/event tests, 31 garden-model tests, 12 sound tests,
  10 earlier rhythm tests, 9 four-beat audio tests and 10 flower-view tests.
  UI checks use silent SDL devices; they are not evidence of another person's
  experience. Mocked export/folder errors intentionally print their messages.
- Audio checks cover all 16 flower combinations, exact one-second sample starts,
  silent rests, independent Sparkle decay, saved recipe copies and the same
  pattern in live/export rendering. Rain(.62) and Bass(0) retain their previous
  PCM digests. Legacy helper calls also retain twelve original bell-loop digests;
  the new app intentionally uses the four editable beats instead.
- Live-edit checks confirm that only the Bells buffer is replaced, rotated to
  the current loop sample. Rain/Bass buffers and their channels are reused,
  and the original playback clock remains unchanged. The latest rapid edit wins;
  stopping during generation stays stopped. Pending visuals follow the audible
  steps while showing the newly selected petals.
- Four stable hit areas use the same proportional stage geometry as the drawing.
  Wide/tall/small stages, rests without renumbering, muted/paused gestures,
  Master-independent preview and the four-second firefly wrap are checked.
  Letter and naming overlays prevent edits to covered flowers.
- Cards and exported JSON include four copied booleans. Missing fields in old
  recipes migrate to the new default; malformed fields are rejected. All four
  resting flowers count as absent Bells for wishes/discoveries. Recovery text
  asks for a lit flower. Master zero still permits composing and keeping a card.
- A native Windows/mixer check started playback, clicked flower 2 through the
  real event handler, accepted the updated melody and retained Rain/Bass Sound
  objects and playback origin. Stop then left no active playback. A 65-frame
  measurement averaged 36.16 ms during concurrent automated checks; this is not
  a performance guarantee or subjective listening assessment.
- Current screenshots and silent GIFs were generated from the app renderer.
  `flower-melody.gif` illustrates a four-second phrase; `flower-melody.wav` is
  a separate eight-second, mono, 16-bit, 22,050 Hz synthesized example.
- The Windows source launcher generated `out/four-flower-launcher.png`
  successfully. Updated default, muted, letter, unlock and melody canvases were
  visually checked for control labels, numbering and overlay placement.
- Recovery snapshots in both local project folders:
  `.backups/before-four-flower-melody-20261025-133112/`.
  No Git commit/push or human trial is claimed for this revision.

### Night greenhouse and specimen notebook / 25 October 2026

This revision reorganises the app into a 1280 x 960 garden stage, a shared sound
workbench and a shelf of eight distinctive botanical specimens. Visitor letters
and export tools open on demand. Kept cards depict their saved recipes. Bell
onsets/decays and bass strength share timing helpers between sound and visuals;
audio samples remain unchanged in the comparisons below.

- `specimens.py` was rendered with all eight found and unobserved motifs at
  52 x 50 and 116 x 112 and the resulting gallery was visually inspected.
  Distinct silhouettes remain visible before discovery. Drawing restores the
  caller's clip; checks also exercised a restricted clip and the flight's
  inactive/active/finished elapsed times without errors.
- A local 200-iteration drawing measurement averaged about 2.45 ms for all eight
  100 x 90 specimens together. This is an implementation measurement on the
  development computer, not a promise for other devices.
- The gallery remains under ignored `out/specimen-art-review-20261025.png`.
  The new illustrations and leaf flight use Pygame geometry, with no image
  dependency, files read at runtime or persistent particle state.
- All **91 automated checks passed** with the project-local Python 3.12 runtime:
  44 UI/event tests, 25 garden tests, 12 sound tests and 10 rhythm tests.
  The UI suite uses SDL dummy devices. It covers all eight visible specimen
  hints, recipe-derived thumbnails that survive later edits, panel opening and
  closing, letterboxed pointer mapping, and disabled export controls covering
  the collection below. Existing muted controls, wrong-share recovery, naming,
  fresh visits and export-error checks still pass.
- Playback-origin checks confirm that gain changes preserve the running clock;
  pending character changes follow the currently audible pattern until the new
  loop starts. A queued first play or restart shows silent preparation until
  audio actually starts. Stopping clears the audio-started state.
- Direct before/after comparison against the recovery snapshot found all
  **18 raw float64 sample loops byte-identical**: three Rain densities, three
  Bass pitches and twelve Bells sparkle/pitch combinations. The rhythm tests
  also retain twelve complete bell-loop PCM digests. This revision changes
  feedback scheduling, not the sound design.
- Current default, disabled-control, rejected-letter, unlock, full-specimen and
  kept-thumbnail canvases were rendered and visually inspected. Main examples
  are `screenshot.png`, `controls-muted.png`, `wish-feedback.png`,
  `discovery-unlocked.png`, `field-notes.png` and `kept-gardens.png`. The two GIFs
  were regenerated from scripted application frames; they are not human trials.
- `start.cmd --screenshot out/launcher-notebook.png` succeeded. A separate native
  Windows check opened the 1280 x 960 window on a 1920 x 1080 desktop, started
  the 22,050 Hz / signed 16-bit / mono mixer and confirmed active playback, then
  confirmed no active playback after Stop. Forty-two native draw/update frames
  averaged 21.28 ms in that run. This is a device/API check, not a listening
  assessment or a physical-mouse usability trial.
- Recovery snapshot: `.backups/before-specimen-notebook-20261025-122030/`.
  The human trial is still pending. Rendered captures and event tests must not
  be described as a person's aesthetic, listening or usability judgment.

Paged-guide descriptions below are historical iteration evidence. The notebook
now shows all eight specimens at once; the linked screenshots/GIFs were refreshed.

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
- This document does not establish that the latest revision is present remotely,
  that signed-out public access works, or that its URL has been submitted on Canvas.

