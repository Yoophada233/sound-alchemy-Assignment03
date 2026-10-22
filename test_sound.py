# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = []
# ///
"""Check real audio samples and exported files without an audio device."""

import json
import math
import time
import unittest
import wave
from pathlib import Path

from sound import (HEADROOM, Mix, PRESETS, SAMPLE_RATE, SECONDS, make_bass,
                   pcm_bytes, render_mix, save_mix)

HERE = Path(__file__).resolve().parent


class SoundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.default = render_mix(Mix())
        cls.folder = HERE / "out" / "checks" / str(time.time_ns())

    def test_duration_and_reproducible_seed(self):
        self.assertEqual(len(self.default), SAMPLE_RATE * SECONDS)
        self.assertEqual(self.default, render_mix(Mix()))
        self.assertGreater(max(map(abs, self.default)), 0.01)

    def test_silent_controls_really_make_silence(self):
        for kind in ("enabled", "levels", "master"):
            mix = Mix()
            if kind == "enabled":
                mix.enabled = [False, False, False]
            elif kind == "levels":
                mix.levels = [0, 0, 0]
            else:
                mix.master = 0
            self.assertFalse(mix.audible())
            self.assertTrue(all(value == 0 for value in render_mix(mix)))

    def test_level_changes_audio_not_just_the_label(self):
        mix = Mix()
        mix.enabled = [False, True, False]
        mix.levels[1] = 0.2
        low = render_mix(mix)
        mix.levels[1] = 0.4
        high = render_mix(mix)
        for a, b in zip(low[::137], high[::137]):
            self.assertAlmostEqual(b, a * 2, places=10)

    def test_higher_pitch_produces_more_cycles(self):
        low, high = make_bass(0), make_bass(1)
        def crossings(samples):
            return sum(a <= 0 < b for a, b in zip(samples[:-1], samples[1:]))
        self.assertAlmostEqual(crossings(high) / crossings(low), 2, delta=0.03)

    def test_full_controls_stay_finite_with_headroom(self):
        mix = Mix()
        mix.levels = [1, 1, 1]
        mix.character = [1, 1, 1]
        mix.master = 1
        samples = render_mix(mix)
        self.assertTrue(all(math.isfinite(v) for v in samples))
        self.assertLessEqual(max(map(abs, samples)), 3 * HEADROOM)
        self.assertEqual((samples[0], samples[-1]), (0, 0))
        self.assertEqual(len(pcm_bytes(samples)), len(samples) * 2)

    def test_each_preset_changes_the_actual_sound(self):
        fingerprints = []
        for name in PRESETS:
            mix = Mix()
            mix.preset(name)
            fingerprints.append(pcm_bytes(render_mix(mix)))
        self.assertEqual(len(set(fingerprints)), len(PRESETS))

    def test_snapshot_does_not_change_when_controls_move(self):
        mix = Mix()
        snapshot = mix.copy()
        mix.levels[0] = 0
        mix.character[1] = 1
        mix.enabled[2] = False
        self.assertEqual(snapshot.levels[0], 0.78)
        self.assertEqual(snapshot.character[1], 0)
        self.assertTrue(snapshot.enabled[2])

    def test_invalid_values_are_rejected_before_generating(self):
        for value in (-0.1, 1.1, float("nan"), float("inf")):
            mix = Mix()
            mix.character[0] = value
            with self.assertRaises(ValueError):
                render_mix(mix)
        for values in ([], [float("nan")], [1.01]):
            with self.assertRaises(ValueError):
                pcm_bytes(values)

    def test_export_matches_playback_and_preserves_earlier_files(self):
        mix = Mix()
        first = save_mix(self.folder, mix, self.default)
        original = first.read_bytes()
        second = save_mix(self.folder, mix, self.default)
        self.assertNotEqual(first, second)
        self.assertEqual(first.read_bytes(), original)
        with wave.open(str(first), "rb") as audio:
            self.assertEqual(audio.getnchannels(), 1)
            self.assertEqual(audio.getsampwidth(), 2)
            self.assertEqual(audio.getframerate(), SAMPLE_RATE)
            self.assertEqual(audio.getnframes(), SAMPLE_RATE * SECONDS * 2)
            self.assertEqual(audio.readframes(audio.getnframes()), pcm_bytes(self.default) * 2)
        settings = json.loads(first.with_suffix(".json").read_text(encoding="utf-8"))
        self.assertEqual(settings["levels"], mix.levels)
        self.assertEqual(settings["export_seconds"], 8)


if __name__ == "__main__":
    unittest.main(verbosity=2)

