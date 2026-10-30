# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = []
# ///
"""Check the four flower steps using the samples a listener actually hears."""

import itertools
import unittest
from unittest.mock import patch

from sound import (FLOWER_NOTES, Mix, SAMPLE_RATE, SECONDS, bell_pattern,
                   make_bells, render_layers,
                   render_mix, validate)


class MelodyTests(unittest.TestCase):
    def test_copy_and_recipe_keep_an_independent_four_flower_pattern(self):
        mix = Mix()
        self.assertEqual(mix.flower_steps, [True, False, True, False])
        snapshot = mix.copy()
        recipe = mix.settings()
        mix.flower_steps[1] = True
        recipe["flower_steps"][0] = False
        self.assertEqual(snapshot.flower_steps, [True, False, True, False])
        self.assertTrue(mix.flower_steps[0])
        mix.preset("Glass garden")
        self.assertEqual(mix.flower_steps, [True, True, True, False])

    def test_invalid_patterns_are_rejected_before_rendering(self):
        invalid = (None, [], [True] * 3, [True] * 5, [1, 0, 1, 0],
                   [True, False, True, "off"], "1010")
        for steps in invalid:
            with self.subTest(steps=steps):
                mix = Mix()
                mix.flower_steps = steps
                with self.assertRaises(ValueError):
                    render_layers(mix)
                if steps is not None:  # None deliberately selects the old helper API.
                    with self.assertRaises(ValueError):
                        bell_pattern(0.5, steps)
        mix = Mix()
        mix.flower_steps = (True, False, False, True)
        validate(mix)

    def test_all_sixteen_patterns_keep_their_slots_at_every_sparkle(self):
        for steps in itertools.product((False, True), repeat=4):
            expected = tuple((index * SAMPLE_RATE, FLOWER_NOTES[index])
                             for index, on in enumerate(steps) if on)
            for sparkle in (0, 0.18, 0.5, 1):
                self.assertEqual(bell_pattern(sparkle, steps), expected)
        self.assertEqual(bell_pattern(1, [False, False, False, True]),
                         ((3 * SAMPLE_RATE, 4),))

    def test_a_flower_changes_only_its_one_second_slot(self):
        solos = []
        for slot in range(4):
            steps = [index == slot for index in range(4)]
            samples = make_bells(0.6, 0.5, steps)
            onsets = [index for index, value in enumerate(samples) if abs(value) > 1e-12]
            self.assertGreater(min(onsets), slot * SAMPLE_RATE)
            self.assertLess(max(onsets), slot * SAMPLE_RATE + round(0.70 * SAMPLE_RATE))
            solos.append(samples)
        together = make_bells(0.6, 0.5, [True] * 4)
        self.assertEqual(together, [sum(values) for values in zip(*solos)])

    def test_sparkle_adds_a_longer_ring_without_changing_the_beat(self):
        steps = [False, True, False, False]
        short = make_bells(0, 0, steps)
        long = make_bells(1, 0, steps)
        start, end = round(1.35 * SAMPLE_RATE), round(1.65 * SAMPLE_RATE)
        short_tail = sum(value * value for value in short[start:end])
        long_tail = sum(value * value for value in long[start:end])
        self.assertGreater(long_tail, short_tail * 2)
        self.assertEqual(bell_pattern(0, steps), bell_pattern(1, steps))

    def test_four_closed_flowers_are_silent_but_other_ingredients_still_play(self):
        steps = [False] * 4
        self.assertEqual(make_bells(1, 1, steps), [0.0] * (SAMPLE_RATE * SECONDS))
        mix = Mix()
        mix.flower_steps = steps
        mix.enabled = [False, False, True]
        self.assertFalse(mix.audible())
        self.assertEqual(render_mix(mix), [0.0] * (SAMPLE_RATE * SECONDS))
        mix.enabled[0] = True
        self.assertTrue(mix.audible())
        self.assertGreater(max(map(abs, render_mix(mix))), 0)

    def test_live_layers_and_export_render_use_the_same_flower_pattern(self):
        mix = Mix()
        mix.flower_steps = [False, True, False, True]
        mix.enabled = [False, False, True]
        mix.levels[2] = mix.master = 1
        layers = render_layers(mix)
        bells = make_bells(mix.character[2], mix.character[1], mix.flower_steps)
        self.assertEqual(layers[2], bells)
        self.assertEqual(render_mix(mix), [value * 0.25 for value in bells])

    def test_editing_only_flowers_reuses_the_existing_rain_and_bass_samples(self):
        mix = Mix()
        original = render_layers(mix)
        character = mix.character.copy()
        mix.flower_steps = [False, True, False, True]
        with patch("sound.make_rain", side_effect=AssertionError("Rain restarted")), \
                patch("sound.make_bass", side_effect=AssertionError("Bass restarted")):
            changed = render_layers(mix, original, character)
        self.assertIs(changed[0], original[0])
        self.assertIs(changed[1], original[1])
        self.assertNotEqual(changed[2], original[2])
        mix.character[0] = 0.8
        regenerated = render_layers(mix, original, character)
        self.assertIsNot(regenerated[0], original[0])

    def test_flower_patterns_do_not_change_fresh_rain_or_bass_audio(self):
        mix = Mix()
        before = render_layers(mix)
        mix.flower_steps = [False, True, False, True]
        after = render_layers(mix)
        self.assertEqual(before[:2], after[:2])
        self.assertNotEqual(before[2], after[2])


if __name__ == "__main__":
    unittest.main(verbosity=2)
