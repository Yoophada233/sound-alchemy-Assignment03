# Credits

## Course inspiration

[SD5913 / PFAD, 2026 course examples](https://github.com/sd5913/pfad/tree/2026):

- `week05`: short uv scripts, Pillow/array examples and the distinction between
  data and its visible rendering.
- `week06/sound/tone.py` and `wav_support.py`: sine synthesis, sample rate,
  short edge fades and standard-library WAV concepts.
- `week06/browser/harmonics.js`: understandable sound controls and interruption
  handling.
- `week07/ball.py` and `ball_pygame.py`: explicit object state, separated model
  and view, and a readable event loop.

Synthesis implementation, interface and tests here were written
for this project with AI assistance.

## Software and documentation

- [Python standard library](https://docs.python.org/3.12/): `math`, `random`,
  `wave`, `array`, `pathlib`, JSON, worker and test support.
- [Pygame 2.6.1](https://www.pygame.org/): window, drawing, events and audio playback.
  Pygame is distributed under LGPL 2.1; it is installed as a dependency, not vendored.
  [Mixer reference](https://www.pygame.org/docs/ref/mixer.html) was consulted for
  mixer format, channels, loop playback and fades.
- [uv](https://docs.astral.sh/uv/): Python/dependency setup and inline script metadata.
- [W3C Audio EQ Cookbook](https://www.w3.org/TR/audio-eq-cookbook/): mathematical
  filter-coefficient conventions used for reference-guided noise shaping.
- Rain design background: Andy Farnell's
  [Practical 15: Rain](https://mitp-content-server.mit.edu/books/content/sectbyfn/books_pres_0/8375/designing_sound.zip/practical15.html)
  and Miklavcic, Zita and Arvidsson's
  [Computational Real-Time Sound Synthesis of Rain](https://huelights.com/docs/P_169.pdf)
  (DAFx 2004). These informed the impact/texture distinction; this project's
  lightweight Python rain models are newly written and do not reproduce
  their patches or claim a full physical simulation.
- Existing Windows Segoe UI and Georgia fonts are read from the local OS when
  available; their files are not included. Other systems use Pygame's bundled
  default font.

## Media and AI

All audio is synthesized by `sound.py`; there are no borrowed field recordings
or third-party music tracks. Interface controls and live effects are drawn in code,
with locally included artwork described below. The screenshot
comes from the app's own renderer. `docs/rainy-window.wav` is an intentional sample
made by the original synthesis code. `docs/rainy-window-v2.wav` and
`docs/rain-only-v2.wav` use the rejected impact-based revision. The current
`docs/rainy-window-v3.wav` and `docs/rain-only-v3.wav` use a continuous filtered
noise curtain with unpitched soft textures. Earlier samples are development
references, not examples claimed to have passed listening acceptance.

## User-supplied Minecraft reference / v4

[【Minecraft】一小时纯雨声](https://www.bilibili.com/video/BV1Pe411x7JY/), uploaded
by 隔壁老晨MrLchen, was supplied by the student as a concrete listening reference.
Agent Reach's `bili` backend retrieved it; a 60–90 second window was measured
locally. Minecraft/game audio and the uploaded recording are not claimed as
project-owned assets and are not redistributed in this repository.

`docs/rain-reference-profile.json` contains numerical measurements and fitted
filter coefficients, not an encoded waveform. `docs/rain-only-v4.wav` and
`docs/rainy-window-v4.wav` are newly synthesized using that profile. Earlier
audio versions remain development references. NumPy was used only in the
existing analysis environment; it is not a new app dependency.

The 30 October loop repair keeps these fitted Rain filters and uses the previous
lap to settle their state. Bass closes whole oscillator cycles in four seconds;
Rain and Bass no longer use the bell phrase's edge fade. The new
`docs/rain-bass-seamless.wav` is a 16-second synthetic demonstration of this
repair. No recording or new sound library was introduced; older WAVs remain
historical examples. Codex assisted with the repair and regression checks.

Codex assisted with ideas, code, documentation and verification. See `PROCESS.md`
for the current division of work and pending student/user-trial reflection.


## Moonlit glass garden / 30 October 2026

The student selected the glass ecosystem music-box concept, combined it with the
layered landscape of the botanical-notebook concept, then asked for softer
natural textures. Codex used the built-in OpenAI ImageGen tool to create four
original production PNGs in `assets/glass/`: a night landscape, two glass
flower states, eight specimen miniatures and four botanical scenery accents.
The [asset notes](assets/glass/README.md) retain the generation prompts and
describe how the image sheets are used.

These are AI-generated artwork, not photographs, purchased sprite packs or
manually painted student illustrations. The app includes the files and needs
no image service at runtime. Codex wrote the asset integration and dark UI.
Pygame draws text, controls, rain, rhythm lights, roots and feedback at the
current display density. The original procedural geometry remains as a
fallback when an image cannot be read.

Screenshots and silent demos are captured from the working app, not from the
concept generator. Chinese garden names use the existing Windows Microsoft
YaHei font when available.

The later edge-foliage revision adds a fifth original PNG atlas, `foliage.png`,
generated with the built-in ImageGen tool from the student's current screenshot
and approved concept as visual references. Its four plants are natural ivy,
hanging leaves, a fern/moss corner and a broad-leaf branch. These are shaded
2D sprites that suggest depth, not real-time 3D models. Pygame fits the plants,
casts soft shadows and caches the composition at each window size. The exact
prompt and atlas boundaries are recorded in the asset notes.
