# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = []
# ///
"""Check the actual repeating signal, including the PCM join in a saved WAV."""

import math
import statistics
import sys
import time
import unittest
import wave
from array import array
from pathlib import Path

from sound import (LOOP_MODEL, Mix, PITCHES, SAMPLE_RATE, SECONDS,
                   make_bass, make_rain, render_mix, save_mix)


def rms(samples):
    return math.sqrt(sum(value * value for value in samples) / len(samples))


def seam_ratio(samples, milliseconds=4):
    """Compare a window centred on the join with ordinary windows in the loop."""
    width = round(milliseconds * SAMPLE_RATE / 1000)
    seam = samples[-width:] + samples[:width]
    windows = [rms(samples[i:i + 2 * width])
               for i in range(2 * width, len(samples) - 2 * width, 2 * width)]
    return rms(seam) / statistics.median(windows)


class LoopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rain = [make_rain(density) for density in (0, 0.62, 1)]
        cls.bass = [make_bass(index / (len(PITCHES) - 1))
                    for index in range(len(PITCHES))]

    def test_rain_has_no_repeated_volume_hole(self):
        for density, samples in zip((0, 0.62, 1), self.rain):
            for width in (2, 4, 8):
                with self.subTest(density=density, half_window_ms=width):
                    # The old edge fade put the join about 11 dB below normal.
                    self.assertGreater(seam_ratio(samples, width), 0.5)
                    self.assertLess(seam_ratio(samples, width), 1.8)

    def test_rain_join_has_no_abnormal_jump_or_corner(self):
        for samples in self.rain:
            differences = [b - a for a, b in zip(samples, samples[1:])]
            join = samples[0] - samples[-1]
            self.assertLess(abs(join), 4 * rms(differences))
            corners = [b - a for a, b in zip(differences, differences[1:])]
            self.assertLess(abs(join - differences[-1]), 4 * rms(corners))
            self.assertLess(abs(differences[0] - join), 4 * rms(corners))

    def test_all_bass_notes_continue_the_waveform_across_zero(self):
        for note, samples in zip(PITCHES, self.bass):
            with self.subTest(note=note):
                # Both sine partials are odd around zero; the breathing envelope
                # is even. The previous lap must supply that negative-time half.
                for offset in range(1, round(0.012 * SAMPLE_RATE)):
                    self.assertAlmostEqual(samples[-offset], -samples[offset], places=10)
                # A taper can hide a phase jump while creating a volume hole.
                self.assertGreater(seam_ratio(samples), 0.5)

    def test_bass_keeps_each_named_pitch_within_one_cent(self):
        for note, samples in zip(PITCHES, self.bass):
            with self.subTest(note=note):
                crossings = []
                for index, (a, b) in enumerate(zip(samples, samples[1:])):
                    if a <= 0 < b:
                        crossings.append(index - a / (b - a))
                frequency = ((len(crossings) - 1) * SAMPLE_RATE
                             / (crossings[-1] - crossings[0]))
                self.assertLess(abs(1200 * math.log2(frequency / note)), 1)

    def test_export_keeps_continuous_rain_and_bass_at_the_four_second_join(self):
        folder = Path(__file__).resolve().parent / "out" / "loop-checks" / str(time.time_ns())
        for layer in (0, 1):
            mix = Mix()
            mix.enabled = [index == layer for index in range(3)]
            mix.levels = [1, 1, 0]
            mix.character = [1, 1, 0]
            mix.master = 0.7
            self.assertEqual(mix.settings()["loop_model"], LOOP_MODEL)
            path = save_mix(folder, mix, render_mix(mix))
            with wave.open(str(path), "rb") as audio:
                self.assertEqual(audio.getnframes(), 2 * SAMPLE_RATE * SECONDS)
                samples = array("h", audio.readframes(audio.getnframes()))
            if sys.byteorder != "little":
                samples.byteswap()
            count = SAMPLE_RATE * SECONDS
            self.assertEqual(samples[:count], samples[count:])
            self.assertGreater(seam_ratio(samples[:count]), 0.5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
