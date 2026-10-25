# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["pygame==2.6.1"]
# ///
"""Check that visible flowers follow the unchanged, audible bell pattern."""

import hashlib
import math
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from garden_view import WIDTH, HEIGHT, bell_envelope, draw_garden, place_stage, rhythm_levels
from sound import Mix, SAMPLE_RATE, SECONDS, bass_pulse, bell_pattern, make_bells, pcm_bytes


# Captured from the pre-notebook synthesis: these are complete 16-bit bell loops,
# including the original edge fade and tails wrapped back across the loop seam.
BELL_PCM_SHA256 = {
    (0, 0): "f7929566992bd3234ec9d86fd12383c25aa82006c2b3b292dbf9c48976e4be01",
    (0, 0.5): "2c3faded8059bf8276dd747804b5ba6e03e127d37c3a9dcdce693a3b60a4bd1d",
    (0, 1): "6ccd9128b605eb4ff054a6da4b692413291ca189cdff526c195de1cf86757dc0",
    (0.18, 0): "3dde986c75fe6c828b281ced45535df8ad369fd76a261ab1611b272f703a6698",
    (0.18, 0.5): "fb080247981fd836d32e5856a801a3d2e50b1f1a363e7db59e657c987dcbe2b6",
    (0.18, 1): "49f1b503cad0aa2c0ce5c42b7fe59e8e0304604b33c979c7aefa390f3e33130f",
    (0.5, 0): "c00cfdc6ab53cffa68d484a1b4b4c5116cec0e1603790e5f902e3b1878c238ed",
    (0.5, 0.5): "eba02b556d69f49ba990c6729652f27d909b1956d142a33b82abfaa50620568c",
    (0.5, 1): "f250eee9065aa438bc68f85f42703eae77fe13113d8e88612d7fc600fc43c0a2",
    (1, 0): "b1274787e40ff29cca2d54f5cfe2d60eace999cf4cc328ebfcce15fd04933a52",
    (1, 0.5): "0e3e27fb8be45845f5063e12f041bf6bd7d6f50543d831084da8a10afab8612f",
    (1, 1): "3038b43e636ab9f13653ed29878a0a622fe8e4ea345c315dbffc3c5c402f4ceb",
}


class RhythmTests(unittest.TestCase):
    def test_bell_loop_audio_is_unchanged_at_all_character_examples(self):
        for (sparkle, pitch), expected in BELL_PCM_SHA256.items():
            with self.subTest(sparkle=sparkle, pitch=pitch):
                digest = hashlib.sha256(pcm_bytes(make_bells(sparkle, pitch))).hexdigest()
                self.assertEqual(digest, expected)

    def test_pattern_has_even_sample_onsets_inside_one_loop(self):
        for sparkle in (0, 0.18, 0.5, 1):
            pattern = bell_pattern(sparkle)
            self.assertIsInstance(pattern, tuple)
            self.assertEqual(len(pattern), 2 + round(sparkle * 6))
            self.assertEqual(pattern[0], (0, 0))
            starts = [sample for sample, _ in pattern] + [SAMPLE_RATE * SECONDS]
            gaps = [second - first for first, second in zip(starts, starts[1:])]
            self.assertLessEqual(max(gaps) - min(gaps), 1)
            self.assertTrue(all(0 <= sample < SAMPLE_RATE * SECONDS for sample, _ in pattern))
        self.assertEqual(tuple(note for _, note in bell_pattern(1)), (0, 7, 12, 4, 9, 7, 4, 12))

    def test_pattern_rejects_invalid_sparkle(self):
        for sparkle in (-0.1, 1.1, math.nan, math.inf):
            with self.subTest(sparkle=sparkle):
                with self.assertRaises(ValueError):
                    bell_pattern(sparkle)

    def test_each_note_lights_its_assigned_flower_then_decays(self):
        for index, (onset, _) in enumerate(bell_pattern(1)):
            time = onset / SAMPLE_RATE
            self.assertGreater(bell_envelope(time + 0.006, 1, index, 8), 0.95)
            self.assertLess(bell_envelope(time + 0.4, 1, index, 8), 0.14)
            self.assertEqual(bell_envelope(time + 0.71, 1, index, 8), 0)
        self.assertEqual(bell_envelope(0.006, 0, 1, 2), 0)

    def test_last_note_tail_crosses_the_seam_and_pattern_repeats(self):
        self.assertAlmostEqual(bell_envelope(0, 1, 7, 8), math.exp(-0.5 * 5))
        for time in (0, 0.006, 0.53, 2.81, 3.99):
            for index in range(8):
                self.assertAlmostEqual(bell_envelope(time, 1, index, 8),
                                       bell_envelope(time + SECONDS, 1, index, 8))

    def test_muting_stopping_and_master_zero_disable_audio_gestures(self):
        mix = Mix()
        self.assertEqual(rhythm_levels(mix, False), (0, 0))
        self.assertEqual(bell_envelope(0.006, 1, 0, 8, active=False), 0)
        self.assertEqual(bell_envelope(0.006, 1, 0, 0), 0)
        mix.enabled[2] = False
        self.assertEqual(rhythm_levels(mix, True)[1], 0)
        mix.enabled[2] = True
        mix.levels[2] = 0
        self.assertEqual(rhythm_levels(mix, True)[1], 0)
        mix.master = 0
        self.assertEqual(rhythm_levels(mix, True), (0, 0))

    def test_bass_and_root_cycle_peak_on_the_same_half_second(self):
        self.assertEqual(bass_pulse(0), 0)
        self.assertEqual(bass_pulse(0.5), 1)
        self.assertAlmostEqual(bass_pulse(1), 0)
        self.assertAlmostEqual(bass_pulse(0.23), bass_pulse(3.23))

    def test_renderer_applies_the_real_bell_envelope_and_silence_gate(self):
        mix = Mix()
        mix.levels = [0, 0, 1]
        mix.character[2] = 0
        surface = pygame.Surface((850, 340), pygame.SRCALPHA)

        def strengths(time, recipe=mix):
            with patch("garden_view.flower") as flowers:
                draw_garden(surface, (0, 0, 850, 340), recipe, time, playing=True)
                return [call.args[-1] for call in flowers.call_args_list]

        self.assertGreater(strengths(0.006)[0], strengths(0.4)[0] + 0.5)
        muted = mix.copy()
        muted.master = 0
        self.assertTrue(all(value == 0 for value in strengths(0.006, muted)))

    def test_pending_controls_preview_growth_but_follow_the_audible_character(self):
        visible = Mix()
        visible.levels[2] = 1
        visible.character[2] = 1
        audible = visible.copy()
        audible.character[2] = 0
        surface = pygame.Surface((850, 340), pygame.SRCALPHA)
        with patch("garden_view.bell_envelope", wraps=bell_envelope) as envelopes:
            draw_garden(surface, (0, 0, 850, 340), visible, 0.006,
                        playing=True, rhythm_mix=audible)
            self.assertTrue(envelopes.called)
            self.assertTrue(all(call.args[1] == 0 for call in envelopes.call_args_list))

    def test_wide_stage_keeps_a_round_flower_round(self):
        world = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        marker = (249, 175, 29, 255)
        pygame.draw.circle(world, marker, (WIDTH // 2, HEIGHT // 2), 20)
        stage = pygame.Surface((1224, 448), pygame.SRCALPHA)
        place_stage(stage, stage.get_rect(), world, frame=False)
        bounds = pygame.mask.from_threshold(stage, marker, (2, 2, 2, 2)).get_bounding_rects()
        self.assertEqual(len(bounds), 1)
        self.assertLessEqual(abs(bounds[0].width - bounds[0].height), 1)


if __name__ == "__main__":
    unittest.main()
