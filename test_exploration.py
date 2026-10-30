# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["pygame==2.6.1"]
# ///
"""Check the listening instrument, progressive clues and temporary solo controls."""

import os
import time
import unittest
from unittest.mock import patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame

from app import Lab, GARDEN_RECT, GUIDE_RECT, PLAY_RECT, VISITOR_RECT, FOCUS_KEYS
from fieldguide import FIELD_NOTES, listening_observation, next_nudge
from garden import SCENES, scene_for
from garden_view import flower_targets, melody_flowers
from raster import viewport
from sound import Mix


class ClueTests(unittest.TestCase):
    def test_each_specimen_has_a_non_numeric_clue_and_a_composing_experiment(self):
        self.assertEqual(set(FIELD_NOTES), {scene["id"] for scene in SCENES})
        for note in FIELD_NOTES.values():
            self.assertNotIn("%", note["clue"])
            self.assertTrue(note["listen"])
            self.assertTrue(note["after"])

    def test_each_nudge_route_can_reach_its_landscape_without_changing_other_inputs(self):
        for scene in SCENES:
            with self.subTest(scene=scene["id"]):
                mix = Mix()
                note = FIELD_NOTES[scene["id"]]
                for index, low, high in note["ranges"]:
                    mix.levels[index] = (low + high) / 2
                if "character" in note:
                    index, low = note["character"]
                    mix.character[index] = low
                self.assertEqual(scene_for(mix), scene["id"])
                before = mix.settings()
                self.assertIn("here already", next_nudge(scene["id"], mix))
                self.assertEqual(mix.settings(), before)

    def test_nudge_recovers_disabled_sound_and_resting_flowers_before_asking_for_volume(self):
        mix = Mix()
        mix.enabled[2] = False
        self.assertIn("Switch Bells on", next_nudge("firefly-grove", mix))
        mix.enabled[2] = True
        mix.flower_steps = [False] * 4
        self.assertIn("Wake a numbered flower", next_nudge("firefly-grove", mix))
        mix.flower_steps[0] = True
        self.assertIn("Bring Bells forward", next_nudge("firefly-grove", mix))

    def test_balance_description_handles_empty_and_resting_bells(self):
        mix = Mix()
        mix.levels = [0, 0, 1]
        mix.flower_steps = [False] * 4
        self.assertIn("empty", listening_observation(mix))
        mix.flower_steps[0] = True
        self.assertIn("One bell", listening_observation(mix))
        mix.flower_steps = [True] * 4
        self.assertIn("Every beat", listening_observation(mix))


class ListeningInteractionTests(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        self.addCleanup(self.lab.close)
        self.ready()

    def ready(self):
        deadline = time.monotonic() + 10
        while self.lab.ready_revision != self.lab.revision and time.monotonic() < deadline:
            self.lab.update()
            time.sleep(.005)
        self.assertEqual(self.lab.ready_revision, self.lab.revision)
        self.lab.draw()

    def mouse(self, point, down=True):
        area, ratio = viewport(self.lab.screen.get_size())
        position = (area.x + round(point[0] * ratio), area.y + round(point[1] * ratio))
        self.lab.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN if down else pygame.MOUSEBUTTONUP,
                                          button=1, pos=position))

    def click(self, key):
        self.lab.draw()
        position = self.lab.buttons[key].center
        self.mouse(position)
        self.mouse(position, False)
        self.lab.draw()

    def key(self, key, down=True, repeat=False):
        self.lab.event(pygame.event.Event(pygame.KEYDOWN if down else pygame.KEYUP,
                                          key=key, repeat=repeat))

    def labels(self):
        with patch.object(self.lab, "text", wraps=self.lab.text) as text:
            self.lab.draw()
        return [call.args[0] for call in text.call_args_list]

    def test_one_prominent_transport_and_no_automatic_sound_or_progress(self):
        self.assertEqual([key for key in self.lab.buttons if key[0] == "play"], [("play", 0)])
        self.assertTrue(GARDEN_RECT.contains(PLAY_RECT))
        self.assertLess(PLAY_RECT.bottom, VISITOR_RECT.top)
        self.assertFalse(self.lab.playing)
        self.assertFalse(self.lab.garden.discovered)
        self.assertIn("This garden is an instrument.", self.labels())
        self.click(("play", 0))
        self.assertIn("Make one beat yours.", self.labels())
        self.key(pygame.K_2)
        self.assertIn("What else could grow here?", self.labels())

    def test_number_keys_edit_once_and_do_not_escape_the_naming_dialog(self):
        before = self.lab.mix.flower_steps.copy()
        self.key(pygame.K_2)
        self.key(pygame.K_2, repeat=True)
        self.assertTrue(self.lab.mix.flower_steps[1])
        self.assertFalse(self.lab.playing)
        self.lab.begin_keep()
        self.key(pygame.K_1)
        self.assertEqual(self.lab.mix.flower_steps[0], before[0])

    def test_ring_and_rest_labels_are_inside_the_click_targets(self):
        for index, target in enumerate(flower_targets(GARDEN_RECT, self.lab.mix)):
            before = self.lab.mix.flower_steps[index]
            self.mouse((target.centerx, target.bottom - 12))
            self.mouse((target.centerx, target.bottom - 12), False)
            self.assertIs(self.lab.mix.flower_steps[index], not before)

    def test_clue_stays_selected_while_adjusting_and_numbers_require_a_request(self):
        before = self.lab.mix.settings()
        self.click(("guide", 7))
        self.assertEqual(self.lab.mix.settings(), before)
        self.assertFalse(self.lab.garden.discovered)
        self.assertFalse(self.lab.playing)
        self.assertEqual(self.lab.guide_help, 0)
        self.assertEqual(self.lab.guide_scene, "amber-reeds")
        self.assertNotIn(SCENES[7]["hint"], self.labels())
        self.click(("guide_help", 1))
        track = next(rect for key, rect in self.lab.sliders if key == ("level", 0))
        self.lab.move_slider(("level", 0), track.center)
        self.assertEqual(self.lab.guide_scene, "amber-reeds")
        self.assertEqual(self.lab.guide_help, 1)
        self.click(("guide_recipe", 2))
        self.assertEqual(self.lab.guide_help, 2)
        self.click(("guide_recipe", 0))
        self.assertEqual(self.lab.guide_help, 0)

    def test_discovered_note_offers_a_variation_and_changing_notes_resets_help(self):
        self.lab.choose_preset("Rainy window")
        self.click(("guide", 0))
        self.assertTrue(any("Rest one flower" in text for text in self.labels()))
        self.click(("guide_recipe", 2))
        self.click(("guide", 4))
        self.assertEqual(self.lab.guide_help, 0)
        self.click(("guide_close", 0))
        self.assertIsNone(self.lab.guide_scene)
        self.assertTrue(self.lab.lesson_hidden)
        self.assertIn("rainy-moss", self.lab.garden.discovered)

    def test_keyboard_focus_only_changes_running_gains_not_recipe_samples_or_clock(self):
        self.click(("play", 0))
        recipe, origin = self.lab.mix.settings(), self.lab.play_origin
        buffers, samples = self.lab.audio.sounds.copy(), self.lab.samples
        self.key(pygame.K_w)
        self.assertEqual(self.lab.audio.focus, 1)
        for index, sound in enumerate(self.lab.audio.sounds):
            if sound is not None:
                expected = self.lab.mix.levels[index % 3] * self.lab.mix.master if index % 3 == 1 else 0
                self.assertAlmostEqual(sound.get_volume(), expected, delta=.01)
        self.key(pygame.K_w, False)
        self.assertIsNone(self.lab.audio.focus)
        self.assertEqual(self.lab.mix.settings(), recipe)
        self.assertEqual(self.lab.play_origin, origin)
        self.assertEqual(self.lab.audio.sounds, buffers)
        self.assertIs(self.lab.samples, samples)
        for index, sound in enumerate(self.lab.audio.sounds):
            if sound is not None:
                self.assertAlmostEqual(sound.get_volume(), self.lab.mix.levels[index % 3] * self.lab.mix.master,
                                       delta=.01)

    def test_mouse_release_anywhere_and_leaving_the_window_end_focus(self):
        self.click(("play", 0))
        self.mouse(self.lab.buttons[("focus", 0)].center)
        self.assertEqual(self.lab.audio.focus, 0)
        self.mouse((-20, -20), False)
        self.assertIsNone(self.lab.audio.focus)
        self.mouse(self.lab.buttons[("focus", 0)].center)
        self.lab.event(pygame.event.Event(pygame.WINDOWLEAVE))
        self.assertIsNone(self.lab.audio.focus)
        self.assertTrue(self.lab.playing)

    def test_dragging_off_a_focus_button_restores_the_mix(self):
        self.click(("play", 0))
        self.mouse(self.lab.buttons[("focus", 0)].center)
        self.lab.event(pygame.event.Event(pygame.MOUSEMOTION, pos=(30, 40)))
        self.assertIsNone(self.lab.audio.focus)

    def test_keyboard_focus_survives_slider_mouse_release_and_releases_on_its_own_key(self):
        self.click(("play", 0))
        self.key(pygame.K_q)
        self.mouse((50, 640), False)
        self.assertEqual(self.lab.audio.focus, 0)
        self.key(pygame.K_w, False)
        self.assertEqual(self.lab.audio.focus, 0)
        self.key(pygame.K_q, False)
        self.assertIsNone(self.lab.audio.focus)

    def test_focus_is_cleared_on_stop_focus_loss_reset_and_naming(self):
        for action in (lambda: self.key(pygame.K_ESCAPE),
                       lambda: self.lab.event(pygame.event.Event(pygame.WINDOWFOCUSLOST)),
                       self.lab.reset, self.lab.begin_keep):
            if self.lab.naming:
                self.key(pygame.K_ESCAPE)
            if not self.lab.playing:
                self.ready()
                self.click(("play", 0))
            self.key(pygame.K_e)
            self.assertEqual(self.lab.audio.focus, 2)
            action()
            self.assertIsNone(self.lab.audio.focus)

    def test_focus_does_not_start_playback_and_explains_muted_ingredients(self):
        self.key(pygame.K_q)
        self.assertFalse(self.lab.playing)
        self.assertIn("Press Play first", self.lab.message)
        self.click(("play", 0))
        self.lab.mix.enabled[0] = False
        self.lab.changed("Rain off.")
        self.key(pygame.K_q)
        self.assertIsNone(self.lab.audio.focus)
        self.assertIn("silent", self.lab.message)

    def test_new_audio_buffers_respect_a_held_focus_and_release_uses_latest_levels(self):
        self.click(("play", 0))
        self.key(pygame.K_w)
        self.lab.mix.character[1] = .8
        self.lab.mix.levels[0] = .4
        self.lab.changed("Lift Pitch while listening to Bass.")
        self.ready()
        self.assertEqual(self.lab.audio.focus, 1)
        for index, sound in enumerate(self.lab.audio.sounds):
            if sound is not None and index % 3 != 1:
                self.assertEqual(sound.get_volume(), 0)
        self.key(pygame.K_w, False)
        for index, sound in enumerate(self.lab.audio.sounds):
            if sound is not None and index % 3 == 0:
                self.assertAlmostEqual(sound.get_volume(), .4 * self.lab.mix.master, delta=.01)

    def test_muting_the_focused_ingredient_releases_focus_without_losing_other_layers(self):
        self.click(("play", 0))
        self.key(pygame.K_e)
        self.lab.mix.levels[2] = 0
        self.lab.changed("Bells muted.")
        self.assertIsNone(self.lab.audio.focus)
        self.assertTrue(self.lab.playing)

    def test_focused_rain_does_not_animate_bell_onsets(self):
        mix = self.lab.mix
        surface = pygame.Surface((748, 310), pygame.SRCALPHA)
        with patch("garden_view.bell_envelope", return_value=0) as envelope:
            melody_flowers(surface, surface.copy(), mix, mix, .01, True, None, listening_focus=0)
        self.assertTrue(all(not call.kwargs["active"] for call in envelope.call_args_list))

    def test_guide_and_main_transport_hitboxes_work_at_2k_and_4k(self):
        for size in ((2560, 1440), (3840, 2160)):
            self.lab.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
            self.lab.draw()
            self.click(("guide", 2))
            self.click(("guide_recipe", 2))
            self.assertEqual(self.lab.guide_help, 2)
            self.click(("play", 0))
            self.assertTrue(self.lab.playing)
            self.click(("play", 0))
            self.assertFalse(self.lab.playing)
            self.click(("guide_close", 0))
            self.assertIsNone(self.lab.guide_scene)

    def test_all_clue_and_recipe_text_fits_above_the_help_buttons(self):
        for index in range(len(SCENES)):
            for level in (0, 1, 2):
                self.lab.open_guide(index)
                self.lab.guide_help = level
                with patch.object(self.lab, "text", wraps=self.lab.text) as text:
                    self.lab.draw_field_guide()
                body = [call.args for call in text.call_args_list
                        if call.args[1] == GUIDE_RECT.x + 92 and call.args[2] >= GUIDE_RECT.y + 62]
                self.assertTrue(body)
                for value, x, y, size, *_ in body:
                    self.assertLessEqual(y + self.lab.font(size).get_height(), GUIDE_RECT.y + 108)
                    self.assertLessEqual(x + self.lab.font(size).size(value)[0], GUIDE_RECT.right - 20)

    def test_visitor_recipe_numbers_are_optional_and_rejection_remains_specific(self):
        self.click(("letter", 0))
        self.click(("wish", 0))
        self.assertFalse(self.lab.wish_help)
        self.click(("wish_help", 0))
        self.assertTrue(self.lab.wish_help)
        self.lab.choose_preset("Night orbit")
        self.click(("wish", 0))
        self.assertIsNotNone(self.lab.wish_error_at)
        self.assertIn("Raise Rain LEVEL", self.lab.message)

    def test_letter_paper_blocks_the_new_focus_controls_and_keep_button_behind_it(self):
        self.click(("play", 0))
        self.click(("letter", 0))
        self.assertNotIn(("focus", 0), self.lab.buttons)
        self.assertNotIn(("keep", 0), self.lab.buttons)
        self.mouse((PLAY_RECT.x + 40, PLAY_RECT.y + 121))
        self.assertIsNone(self.lab.audio.focus)
        self.mouse((1100, 490))
        self.assertFalse(self.lab.naming)
        self.assertTrue(self.lab.playing)


if __name__ == "__main__":
    unittest.main()
