# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["pygame==2.6.1"]
# ///
"""Four playable flowers stay reachable and follow the audible melody."""

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from garden_view import (FLOWER_HEADS, WIDTH, HEIGHT, bell_envelope, draw_garden,
                         firefly_position, flower_targets, melody_flowers, place_stage)
from sound import Mix


class FlowerViewTests(unittest.TestCase):
    def test_targets_are_four_separate_controls_inside_every_stage_shape(self):
        for rect in ((28, 88, 1224, 448), (13, 17, 748, 310),
                     (9, 20, 374, 310), (0, 0, 224, 93)):
            with self.subTest(rect=rect):
                area = pygame.Rect(rect)
                targets = flower_targets(area, Mix())
                self.assertEqual(len(targets), 4)
                self.assertTrue(all(area.contains(target) for target in targets))
                self.assertEqual(list(targets), sorted(targets, key=lambda target: target.x))
                self.assertTrue(all(not first.colliderect(second)
                                    for first, second in zip(targets, targets[1:])))

    def test_hit_areas_cover_the_actually_placed_heads_in_wide_and_tall_windows(self):
        colors = ((249, 23, 61, 255), (3, 242, 38, 255),
                  (41, 29, 245, 255), (245, 232, 12, 255))
        world = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for point, color in zip(FLOWER_HEADS, colors):
            pygame.draw.circle(world, color, point, 3)
        for rect in ((28, 88, 1224, 448), (13, 17, 748, 310), (9, 20, 374, 620)):
            area = pygame.Rect(rect)
            surface = pygame.Surface((area.right + 10, area.bottom + 10), pygame.SRCALPHA)
            place_stage(surface, area, world, frame=False)
            for target, color in zip(flower_targets(area, Mix()), colors):
                bounds = pygame.mask.from_threshold(surface, color, (8, 8, 8, 8)).get_bounding_rects()
                self.assertEqual(len(bounds), 1)
                self.assertTrue(target.contains(bounds[0]))

    def test_controls_do_not_move_with_recipe_time_or_mute_state(self):
        mix = Mix()
        area = (28, 88, 1224, 448)
        original = flower_targets(area, mix)
        for value in (0, 0.3, 1):
            mix.levels = [value] * 3
            mix.character = [value] * 3
            mix.flower_steps = [value > 0] * 4
            mix.enabled = [False, True, False]
            self.assertEqual(flower_targets(area, mix, value * 91), original)
        self.assertEqual(flower_targets((0, 0, 0, 40), mix), ())

    def test_rests_keep_their_numbered_flower_instead_of_shifting_notes(self):
        steps = [False, True, False, True]
        for slot in range(4):
            for flower in range(4):
                light = bell_envelope(slot + 0.006, 0.5, flower, 4, flower_steps=steps)
                if steps[slot] and flower == slot:
                    self.assertGreater(light, 0.95)
                else:
                    self.assertEqual(light, 0)

    def test_bloom_decays_before_the_next_beat_and_repeats_with_audio(self):
        steps = [True] * 4
        for slot in range(4):
            self.assertEqual(bell_envelope(slot + 0.71, 0.7, slot, 4, flower_steps=steps), 0)
            first = bell_envelope(slot + 0.03, 0.7, slot, 4, flower_steps=steps)
            repeat = bell_envelope(slot + 4.03, 0.7, slot, 4, flower_steps=steps)
            self.assertAlmostEqual(first, repeat)
        self.assertEqual(bell_envelope(0.006, 1, 0, 4, flower_steps=[False] * 4), 0)

    def test_pending_choice_previews_petals_but_uses_audible_slots_for_attacks(self):
        visible = Mix()
        visible.flower_steps = [False, True, False, True]
        audible = visible.copy()
        audible.flower_steps = [True, False, True, False]
        audible.character[2] = 0
        visible.character[2] = 1
        surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        lights = surface.copy()
        with patch("garden_view.bell_envelope", wraps=bell_envelope) as attacks, \
                patch("garden_view.flower") as flowers:
            melody_flowers(surface, lights, visible, audible, 0.006, True, None)
        self.assertEqual([call.args[2] for call in attacks.call_args_list], list(range(4)))
        self.assertTrue(all(call.kwargs["flower_steps"] == audible.flower_steps
                            and call.args[1] == 0 for call in attacks.call_args_list))
        self.assertEqual([call.args[2] for call in flowers.call_args_list],
                         [FLOWER_HEADS[1][0], FLOWER_HEADS[3][0]])

    def test_stopped_off_zero_and_master_mute_disable_sound_led_bloom(self):
        for state in ("stopped", "off", "zero", "master"):
            mix = Mix()
            if state == "off":
                mix.enabled[2] = False
            elif state == "zero":
                mix.levels[2] = 0
            elif state == "master":
                mix.master = 0
            surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            with patch("garden_view.flower") as flowers:
                melody_flowers(surface, surface.copy(), mix, mix, 0.006,
                               state != "stopped", None)
            self.assertEqual(len(flowers.call_args_list), 2)
            self.assertTrue(all(call.args[-1] == 0 for call in flowers.call_args_list))

    def test_firefly_arrives_at_each_actual_onset_and_wraps_without_a_jump(self):
        for slot, (x, y) in enumerate(FLOWER_HEADS):
            self.assertEqual(firefly_position(slot), (x, y - 20))
        for phase in (0, 0.15, 1.5, 2.91, 3.999):
            for actual, repeat in zip(firefly_position(phase), firefly_position(phase + 4)):
                self.assertAlmostEqual(actual, repeat)
        before = firefly_position(4 - 0.000001)
        after = firefly_position(4 + 0.000001)
        self.assertLess(abs(before[0] - after[0]), 0.001)
        self.assertLess(abs(before[1] - after[1]), 0.001)

    def test_all_rest_recipe_still_renders_four_visible_controls_and_hover(self):
        mix = Mix()
        mix.flower_steps = [False] * 4
        mix.levels = [0, 0, 0]
        mix.enabled = [False] * 3
        plain = pygame.Surface((850, 340), pygame.SRCALPHA)
        hovered = plain.copy()
        draw_garden(plain, plain.get_rect(), mix, 0, flower_hover=None)
        draw_garden(hovered, hovered.get_rect(), mix, 0, flower_hover=2)
        self.assertNotEqual(pygame.image.tobytes(plain, "RGBA"),
                            pygame.image.tobytes(hovered, "RGBA"))
        self.assertEqual(len(flower_targets(plain.get_rect(), mix)), 4)

    def test_master_mute_keeps_the_same_static_garden_and_four_flower_choices(self):
        mix = Mix()
        muted = mix.copy()
        muted.master = 0
        original = pygame.Surface((850, 340), pygame.SRCALPHA)
        silent = original.copy()
        draw_garden(original, original.get_rect(), mix, 0.23, playing=False)
        draw_garden(silent, silent.get_rect(), muted, 0.23, playing=False)
        self.assertEqual(pygame.image.tobytes(original, "RGBA"),
                         pygame.image.tobytes(silent, "RGBA"))
        self.assertEqual(flower_targets(original.get_rect(), mix),
                         flower_targets(silent.get_rect(), muted))


if __name__ == "__main__":
    unittest.main()
