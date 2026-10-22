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

The sound recipes, synthesis implementation, interface and tests here were written
for this project with AI assistance. No course image, music file, font file or
student artwork is redistributed. The mathematical sine/WAV concepts are adapted
into the new three-layer interaction; the course tutorials are not the submission.

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
or third-party music tracks. Interface graphics are drawn in code. The screenshot
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

Codex assisted with ideas, code, documentation and verification. See `PROCESS.md`
for the current division of work and pending student/user-trial reflection.


## Procedural garden

The garden artwork is drawn from Python/Pygame geometry created for this project
with Codex assistance. No external garden images, sprite packs or textures are
used. Chinese garden names use the existing Windows Microsoft YaHei font when
available; font files are not redistributed.
