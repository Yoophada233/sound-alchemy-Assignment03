# Verification / 22 October 2026

## Environment

- Windows desktop; display driver reported by Pygame: `windows`.
- Desktop size reported: 1920 x 1080; application design canvas: 1180 x 860.
- Project-local CPython 3.12.14; Pygame 2.6.1.
- Audio format accepted by the local mixer: 22,050 Hz, signed 16-bit, mono.
- Source and generated files remained in the new `sound-alchemy/` folder.
  Dependencies/cache and Python were placed in `.uv-cache/` and `.python/`.
  No Git init, commit, push, public deployment or Canvas submission was performed.

## Executed checks

| Check | Observed result |
| --- | --- |
| Python source parse | `app.py` and `sound.py` parsed successfully. |
| Sound tests | 9 passed: duration/repeatability, silence, level scaling, pitch, headroom/fades, distinct presets, state copies, invalid data and export integrity. |
| Interaction tests | 16 passed: original interaction checks plus level/master continuity, a burst of mouse moves followed by release/Stop, rejoining a muted layer, latest gains during pattern generation, saved-folder action, folder-viewer error recovery and a moved export. |
| Final runtime | Both test files passed using the installed project-local Python 3.12 environment via uv. |
| Fresh PowerShell setup | README setup commands succeeded; an offline screenshot invocation generated `out/fresh-terminal.png`. |
| Windows launcher | `start.cmd --screenshot out/launcher-check.png` exited successfully. |
| Interface inspection | Full application canvas rendered to `docs/screenshot.png`; inspected for clipped text, overlap and control layout. |
| Native audio connection | Local mixer initialized and played. In the usability revision, the running layer buffers and playback origin were unchanged after level/master edits; Stop then reported no active playback. |
| Native export-folder action | Windows accepted an open-folder request for the real `out/mixes/` directory. The sandbox denied this OS action during the first check; it succeeded in a narrowly escalated directory-only check, without system-setting changes. |
| Demo WAV | `docs/rainy-window.wav`: 8 seconds, mono, 16-bit PCM, 22,050 samples/s; generated from the default recipe. |
| Export preservation | A second export used a different name; the first WAV remained byte-identical. |
| Sound preservation | The default exported PCM remains byte-identical to the existing demonstration WAV; no ingredient synthesis or preset values changed. |
| Duplicate Stop removal | The standalone Stop control and its click route were removed. Reset moved next to the main Play/Stop button. The interruption test now stops through that main button. |

Tests use the project's own local runtime. Deliberate mocked export and
folder-viewer errors print console messages; those recovery tests pass.
The usability revision preserves a source snapshot under
`.backups/before-usability-20261022-183958/` and keeps prior exports.

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
- Public repository access, Git history and submission requirements remain pending.

