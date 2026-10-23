# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["pygame==2.6.1"]
# ///
"""Exercise the real event handlers with silent SDL devices; no person is simulated."""

import os
import time
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame
from app import Lab
from sound import mix_layers, pcm_bytes

HERE = Path(__file__).resolve().parent


class InteractionTests(unittest.TestCase):
    def setUp(self):
        self.folder = HERE / "out" / "ui-checks" / str(time.time_ns())
        self.lab = Lab(output=self.folder)
        self.addCleanup(self.lab.close)
        self.wait_ready()

    def wait_ready(self):
        deadline = time.monotonic() + 10
        while self.lab.ready_revision != self.lab.revision and time.monotonic() < deadline:
            self.lab.update()
            time.sleep(0.005)
        self.assertEqual(self.lab.ready_revision, self.lab.revision)
        self.lab.draw()

    def click(self, key):
        point = self.lab.buttons[key].center
        self.lab.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=point))
        self.lab.event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=point))

    def test_no_autoplay_and_repeated_play_does_not_stack_audio(self):
        self.assertFalse(self.lab.playing)
        self.assertFalse(pygame.mixer.get_busy())
        self.click(("play", 0))
        self.assertTrue(self.lab.playing)
        self.assertTrue(pygame.mixer.get_busy())
        self.click(("play", 0))
        self.assertFalse(self.lab.playing)
        self.assertFalse(pygame.mixer.get_busy())

    def test_mouse_slider_changes_samples_and_clamps_outside_track(self):
        before = self.lab.samples.copy()
        key, rect = self.lab.sliders[0]
        self.lab.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                          pos=(rect.left, rect.centery)))
        self.lab.event(pygame.event.Event(pygame.MOUSEMOTION,
                                          pos=(rect.left - 100, rect.centery)))
        self.lab.event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1,
                                          pos=(rect.left - 100, rect.centery)))
        self.assertEqual(self.lab.mix.levels[0], 0)
        self.assertIsNone(self.lab.dragging)
        self.wait_ready()
        self.assertNotEqual(before, self.lab.samples)

    def test_zero_level_blocks_parameter_drag_and_raising_it_restores_control(self):
        for index in range(3):
            with self.subTest(ingredient=index):
                key = ("character", index)
                track = next(rect for item, rect in self.lab.sliders if item == key)
                level = next(rect for item, rect in self.lab.sliders if item == ("level", index))
                original = self.lab.mix.character[index]
                self.lab.move_slider(("level", index), (level.left, level.centery))
                revision = self.lab.revision
                self.lab.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                                  pos=track.midright))
                self.assertIsNone(self.lab.dragging)
                self.lab.event(pygame.event.Event(pygame.MOUSEMOTION, pos=track.midleft))
                self.lab.event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1,
                                                  pos=track.midleft))
                self.assertEqual(self.lab.mix.character[index], original)
                self.assertEqual(self.lab.revision, revision)
                self.assertIn("Raise LEVEL", self.lab.message)
                self.lab.move_slider(("level", index), level.center)
                self.assertEqual(self.lab.mix.character[index], original)
                self.lab.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                                  pos=track.midright))
                self.lab.event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1,
                                                  pos=track.midright))
                self.assertEqual(self.lab.mix.character[index], 1)

    def test_off_ingredient_keeps_parameter_until_switched_back_on(self):
        for index in range(3):
            with self.subTest(ingredient=index):
                original = self.lab.mix.character[index]
                self.click(("toggle", index))
                key = ("character", index)
                track = next(rect for item, rect in self.lab.sliders if item == key)
                level = next(rect for item, rect in self.lab.sliders if item == ("level", index))
                self.lab.move_slider(("level", index), level.center)
                self.assertEqual(self.lab.mix.levels[index], .5)
                revision = self.lab.revision
                self.lab.move_slider(key, track.midright)
                self.assertIsNone(self.lab.dragging)
                self.assertEqual(self.lab.mix.character[index], original)
                self.assertEqual(self.lab.revision, revision)
                self.assertIn("Switch", self.lab.message)
                self.click(("toggle", index))
                self.assertEqual(self.lab.mix.character[index], original)
                self.lab.move_slider(key, track.midright)
                self.assertEqual(self.lab.mix.character[index], 1)

    def test_level_and_master_change_without_restarting_or_regenerating(self):
        self.click(("play", 0))
        origin = self.lab.play_origin
        channels = [pygame.mixer.Channel(self.lab.audio.bank * 3 + i) for i in range(3)]
        sounds = [channel.get_sound() for channel in channels]
        with patch.object(self.lab.audio, "play", wraps=self.lab.audio.play) as replay:
            with patch.object(self.lab.pool, "submit", wraps=self.lab.pool.submit) as render:
                for key, fraction in ((("level", 0), 0.15), (("master", 0), 0.5)):
                    rect = next(rect for item, rect in self.lab.sliders if item == key)
                    self.lab.move_slider(key, (rect.left + rect.width * fraction, rect.centery))
                self.lab.update()
                replay.assert_not_called()
                render.assert_not_called()
        self.assertEqual(self.lab.play_origin, origin)
        self.assertTrue(self.lab.playing)
        for i, channel in enumerate(channels):
            self.assertIs(channel.get_sound(), sounds[i])
            self.assertAlmostEqual(sounds[i].get_volume(),
                                   self.lab.mix.levels[i] * self.lab.mix.master, delta=1 / 128)
        self.assertEqual(self.lab.ready_revision, self.lab.revision)

    def test_drag_burst_keeps_the_final_value_release_and_stop(self):
        self.click(("play", 0))
        _, rect = self.lab.sliders[0]
        events = [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                     pos=(rect.left, rect.centery))]
        for fraction in (0.2, 0.4, 0.6, 0.9):
            events.append(pygame.event.Event(pygame.MOUSEMOTION,
                                             pos=(rect.left + rect.width * fraction, rect.centery)))
        events.extend([pygame.event.Event(pygame.MOUSEBUTTONUP, button=1,
                                          pos=(rect.right, rect.centery)),
                       pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE),
                       pygame.event.Event(pygame.QUIT)])
        with patch("pygame.event.get", return_value=events):
            self.lab.run()
        self.assertAlmostEqual(self.lab.mix.levels[0], 0.9)
        self.assertIsNone(self.lab.dragging)
        self.assertFalse(self.lab.playing)

    def test_muted_layer_joins_existing_playback_without_restarting(self):
        self.click(("toggle", 0))
        self.click(("play", 0))
        channel = pygame.mixer.Channel(self.lab.audio.bank * 3)
        sound = channel.get_sound()
        self.assertEqual(sound.get_volume(), 0)
        origin = self.lab.play_origin
        with patch.object(self.lab.audio, "play", wraps=self.lab.audio.play) as replay:
            self.click(("toggle", 0))
            replay.assert_not_called()
        self.assertIs(channel.get_sound(), sound)
        self.assertGreater(sound.get_volume(), 0)
        self.assertEqual(self.lab.play_origin, origin)

    def test_gain_changes_during_pattern_generation_use_the_latest_recipe(self):
        self.lab.choose_preset("Night orbit")
        self.lab.last_edit = 0
        self.lab.update()
        self.lab.mix.master = 0.25
        self.lab.mix.levels[0] = 0.9
        self.lab.changed("Latest volume while the pattern is being made.")
        self.wait_ready()
        self.assertEqual(self.lab.samples, mix_layers(self.lab.layers, self.lab.mix))
        self.lab.export()
        import wave
        with wave.open(str(self.lab.last_saved), "rb") as audio:
            self.assertEqual(audio.readframes(audio.getnframes()), pcm_bytes(self.lab.samples) * 2)

    def test_stop_during_render_is_not_undone_by_background_result(self):
        self.click(("play", 0))
        self.click(("preset", "Glass garden"))
        self.click(("play", 0))
        self.wait_ready()
        self.assertFalse(self.lab.playing)
        self.assertFalse(pygame.mixer.get_busy())

    def test_all_off_gives_feedback_and_reset_restores_a_stopped_recipe(self):
        for index in range(3):
            self.click(("toggle", index))
        self.click(("play", 0))
        self.assertFalse(self.lab.playing)
        self.assertIn("silent", self.lab.message)
        self.click(("reset", 0))
        self.wait_ready()
        self.assertEqual(self.lab.mix.levels, [0.78, 0.32, 0.20])
        self.assertEqual(self.lab.mix.enabled, [True, True, True])
        self.assertFalse(self.lab.playing)

    def test_latest_slider_state_wins_over_an_older_render(self):
        self.lab.choose_preset("Night orbit")
        self.lab.last_edit = 0
        self.lab.update()
        self.lab.choose_preset("Glass garden")
        self.wait_ready()
        self.assertEqual(self.lab.job_mix.levels, self.lab.mix.levels)
        self.assertEqual(self.lab.job_mix.character, self.lab.mix.character)

    def test_export_while_stopped_and_repeated_save_are_safe(self):
        self.click(("save", 0))
        self.assertIsNotNone(self.lab.last_saved)
        first = self.lab.last_saved
        self.click(("save", 0))
        self.assertEqual(self.lab.last_saved, first)
        self.assertEqual(len(list(self.folder.glob("*.wav"))), 1)
        self.assertFalse(self.lab.playing)

    def test_saved_folder_button_only_opens_the_completed_exports_directory(self):
        self.assertNotIn(("folder", 0), self.lab.buttons)
        self.click(("save", 0))
        self.lab.draw()
        with patch("app.open_directory") as opener:
            self.click(("folder", 0))
            opener.assert_called_once_with(self.folder.resolve())
        self.assertTrue(self.lab.last_saved.is_file())

    def test_folder_open_failure_keeps_the_export_and_app_usable(self):
        self.click(("save", 0))
        self.lab.draw()
        with patch("app.open_directory", side_effect=OSError("test: no folder viewer")):
            self.click(("folder", 0))
        self.assertIn("Could not open", self.lab.message)
        self.assertTrue(self.lab.last_saved.is_file())
        self.click(("play", 0))
        self.assertTrue(self.lab.playing)

    def test_moved_export_does_not_open_an_unrelated_folder(self):
        self.lab.last_saved = self.folder / "not-there.wav"
        self.lab.draw()
        with patch("app.open_directory") as opener:
            self.click(("folder", 0))
            opener.assert_not_called()
        self.assertIn("no longer here", self.lab.message)

    def test_unavailable_audio_still_allows_export_and_play_retries(self):
        self.lab.audio.available = False
        with patch.object(self.lab.audio, "connect", return_value=False):
            self.click(("play", 0))
        self.assertFalse(self.lab.playing)
        self.assertIn("unavailable", self.lab.message)
        self.click(("save", 0))
        self.assertTrue(self.lab.last_saved.is_file())
        with patch.object(self.lab.audio, "connect", return_value=True):
            self.click(("play", 0))
        self.assertTrue(self.lab.playing)

    def test_focus_loss_and_escape_stop_immediately(self):
        self.click(("play", 0))
        self.lab.event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        self.assertFalse(self.lab.playing)
        self.click(("play", 0))
        self.lab.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertFalse(self.lab.playing)
        self.assertFalse(pygame.mixer.get_busy())

    def test_export_error_is_reported_without_crashing(self):
        with patch("app.save_mix", side_effect=PermissionError("test: folder is read-only")):
            self.click(("save", 0))
        self.assertIsNone(self.lab.last_saved)
        self.assertIn("Could not save", self.lab.message)
        self.click(("play", 0))
        self.assertTrue(self.lab.playing)

    def test_adjusting_sound_discovers_a_garden_without_requiring_play(self):
        self.assertFalse(self.lab.garden.discovered)
        key, rect = self.lab.sliders[0]
        self.lab.move_slider(key, (rect.left + rect.width * 0.8, rect.centery))
        self.assertIn("rainy-moss", self.lab.garden.discovered)
        self.assertIn("Discovered", self.lab.message)
        self.assertFalse(self.lab.playing)
        self.assertFalse(self.folder.exists())

    def test_unlock_is_announced_visibly_once_without_starting_audio(self):
        self.lab.choose_preset("Rainy window")
        self.assertEqual(self.lab.discovery_current, "rainy-moss")
        with patch.object(self.lab, "text", wraps=self.lab.text) as text:
            self.lab.draw()
        labels = [call.args[0] for call in text.call_args_list]
        self.assertIn("NEW DISCOVERY!", labels)
        self.assertIn("NEW! / click for its recipe hint", labels)
        self.assertFalse(self.lab.playing)
        self.assertFalse(pygame.mixer.get_busy())
        self.click(("discovery_close", 0))
        self.lab.choose_preset("Rainy window")
        self.assertIsNone(self.lab.discovery_current)
        self.assertFalse(self.lab.discovery_queue)

    def test_rapid_discoveries_are_announced_in_order_instead_of_replacing_each_other(self):
        for name in ("Rainy window", "Night orbit", "Glass garden"):
            self.lab.choose_preset(name)
        for scene_id in ("rainy-moss", "moonlit-roots", "dawn-chorus"):
            self.assertEqual(self.lab.discovery_current, scene_id)
            self.lab.draw()
            self.click(("discovery_close", 0))
        self.assertIsNone(self.lab.discovery_current)
        self.assertFalse(self.lab.discovery_queue)
        self.assertEqual(len(self.lab.garden.discovered), 3)

    def test_first_discovery_from_keeping_a_garden_can_be_viewed_in_the_guide(self):
        self.lab.begin_keep()
        self.lab.finish_keep()
        self.assertEqual(self.lab.discovery_current, "rainy-moss")
        self.assertEqual(self.lab.collection_tab, "cards")
        self.lab.draw()
        self.click(("discovery_view", 0))
        self.assertEqual(self.lab.collection_tab, "guide")
        self.assertEqual(self.lab.guide_page, 0)
        self.assertEqual(len(self.lab.garden.cards), 1)

    def test_first_discovery_from_a_wish_is_announced_with_its_stamp(self):
        self.lab.visitor_action()
        self.lab.visitor_action()
        self.assertEqual(self.lab.discovery_current, "rainy-moss")
        self.assertIn("a-soft-rain", self.lab.garden.completed)

    def test_second_discovery_page_has_hints_and_new_unlocks_reveal_the_correct_page(self):
        self.click(("guide_page", 1))
        self.lab.draw()
        self.assertNotIn(("guide", 0), self.lab.buttons)
        self.assertIn(("guide", 7), self.lab.buttons)
        self.click(("guide", 7))
        self.assertIn("Pitch", self.lab.message)
        self.click(("guide_page", -1))
        self.lab.mix.levels = [.3, .45, .25]
        self.lab.mix.character[1] = .8
        self.lab.changed("Grow amber reeds.")
        self.assertEqual(self.lab.discovery_current, "amber-reeds")
        self.assertEqual(self.lab.guide_page, 1)
        self.lab.draw()
        self.assertIn(("guide", 7), self.lab.buttons)

    def test_unlock_notice_pauses_during_naming_then_expires_normally(self):
        self.lab.choose_preset("Rainy window")
        started = self.lab.discovery_started
        self.lab.begin_keep()
        self.lab.update_discoveries(started + 1)
        self.lab.update_discoveries(started + 10)
        self.assertEqual(self.lab.discovery_current, "rainy-moss")
        self.lab.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.lab.update_discoveries(started + 10)
        self.assertEqual(self.lab.discovery_current, "rainy-moss")
        self.lab.update_discoveries(started + 14)
        self.assertIsNone(self.lab.discovery_current)

    def test_celebration_stays_in_garden_and_finishes_without_leftover_pixels(self):
        from garden_view import draw_discovery_effect
        surface = pygame.Surface((1000, 500), pygame.SRCALPHA)
        rect = pygame.Rect(34, 98, 790, 312)
        draw_discovery_effect(surface, rect, (92, 170, 180), .25)
        self.assertTrue(rect.contains(surface.get_bounding_rect()))
        first = pygame.image.tobytes(surface, "RGBA")
        surface.fill((0, 0, 0, 0))
        draw_discovery_effect(surface, rect, (92, 170, 180), .8)
        self.assertNotEqual(pygame.image.tobytes(surface, "RGBA"), first)
        for elapsed in (-1, 1.4, 5):
            surface.fill((0, 0, 0, 0))
            draw_discovery_effect(surface, rect, (92, 170, 180), elapsed)
            self.assertEqual(surface.get_bounding_rect().size, (0, 0))

    def test_master_volume_does_not_unlock_or_change_a_garden(self):
        from garden import scene_for
        before = scene_for(self.lab.mix)
        rect = next(rect for key, rect in self.lab.sliders if key == ("master", 0))
        self.lab.move_slider(("master", 0), (rect.left, rect.centery))
        self.assertEqual(scene_for(self.lab.mix), before)
        self.assertFalse(self.lab.garden.discovered)

    def test_name_entry_keeps_a_restorable_card_and_blocks_global_shortcuts(self):
        expected = self.lab.mix.settings()
        self.click(("keep", 0))
        self.lab.draw()
        self.lab.event(pygame.event.Event(pygame.TEXTINPUT, text="Sea of light"))
        self.lab.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_s))
        self.lab.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        self.assertIsNone(self.lab.last_saved)
        self.assertFalse(self.lab.playing)
        self.lab.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertFalse(self.lab.naming)
        card = self.lab.garden.cards[0]
        self.assertEqual(card["name"], "Sea of light")
        self.assertEqual(self.lab.garden.restore(card["id"]).settings(), expected)
        self.lab.choose_preset("Night orbit")
        self.lab.draw()
        self.click(("restore", card["id"]))
        self.assertEqual(self.lab.mix.settings(), expected)
        self.assertFalse(self.lab.playing)

    def test_empty_name_can_be_fixed_and_escape_does_not_create_a_card(self):
        self.click(("keep", 0))
        self.lab.event(pygame.event.Event(pygame.TEXTINPUT, text="   "))
        self.lab.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertTrue(self.lab.naming)
        self.assertTrue(self.lab.name_error)
        self.assertFalse(self.lab.garden.cards)
        self.lab.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertFalse(self.lab.naming)
        self.assertFalse(self.lab.garden.cards)

    def test_ime_composition_does_not_save_before_the_name_is_committed(self):
        self.click(("keep", 0))
        name = "\u96e8\u4e2d\u82b1\u56ed"
        self.lab.event(pygame.event.Event(pygame.TEXTEDITING, text="yu", start=0, length=2))
        self.lab.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertTrue(self.lab.naming)
        self.assertFalse(self.lab.garden.cards)
        self.lab.event(pygame.event.Event(pygame.TEXTINPUT, text=name))
        self.lab.draw()
        self.lab.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertEqual(self.lab.garden.cards[0]["name"], name)

    def test_optional_wish_accept_share_next_and_no_duplicate_completion(self):
        self.assertIsNone(self.lab.active_wish)
        self.click(("wish", 0))
        self.assertEqual(self.lab.active_wish, "a-soft-rain")
        self.lab.draw()
        self.click(("wish", 0))
        self.assertIn("a-soft-rain", self.lab.garden.completed)
        self.lab.draw()
        self.assertNotIn(("wish", 0), self.lab.buttons)
        self.click(("next_wish", 0))
        self.lab.draw()
        self.click(("wish", 0))
        self.lab.draw()
        self.click(("wish", 0))
        self.assertEqual(len(self.lab.garden.completed), 1)
        self.assertIn("Keep exploring", self.lab.message)
        self.lab.choose_preset("Night orbit")
        self.click(("wish", 0))
        self.assertIn("roots-at-night", self.lab.garden.completed)

    def test_wrong_share_shows_inline_guidance_and_retriggers_after_each_click(self):
        self.lab.choose_preset("Night orbit")
        self.click(("wish", 0))
        self.lab.draw()
        recipe = self.lab.mix.settings()
        self.click(("wish", 0))
        self.assertIsNotNone(self.lab.wish_error_at)
        self.assertEqual(self.lab.mix.settings(), recipe)
        self.assertFalse(self.lab.garden.completed)
        self.assertFalse(self.lab.playing)
        with patch.object(self.lab, "text", wraps=self.lab.text) as text:
            self.lab.draw()
        panel_text = [call.args[0] for call in text.call_args_list
                      if call.args[1] == 869 and 250 <= call.args[2] <= 330]
        self.assertTrue(any("NOT QUITE YET" in line for line in panel_text))
        self.assertTrue(any("Raise Rain LEVEL" in line for line in panel_text))
        self.lab.wish_error_at -= 2
        previous = self.lab.wish_error_at
        self.lab.draw()
        self.assertEqual(self.lab.wish_error_at, previous)
        self.click(("wish", 0))
        self.assertGreater(self.lab.wish_error_at, previous)

    def test_wrong_share_clears_on_edits_success_and_switching_notes(self):
        self.lab.choose_preset("Night orbit")
        self.click(("wish", 0))
        self.lab.draw()
        self.click(("wish", 0))
        self.assertIsNotNone(self.lab.wish_error_at)
        self.lab.choose_preset("Rainy window")
        self.assertIsNone(self.lab.wish_error_at)
        self.lab.draw()
        self.click(("wish", 0))
        self.assertIsNone(self.lab.wish_error_at)
        self.assertIn("a-soft-rain", self.lab.garden.completed)
        self.lab.visitor_action()  # A double click before redraw cannot reject a completed note.
        self.assertIsNone(self.lab.wish_error_at)
        self.click(("next_wish", 0))
        self.lab.draw()
        self.click(("wish", 0))
        self.lab.draw()
        self.click(("wish", 0))
        self.assertIsNotNone(self.lab.wish_error_at)
        self.click(("next_wish", 0))
        self.assertIsNone(self.lab.wish_error_at)
        self.assertEqual(len(self.lab.garden.completed), 1)

    def test_visit_progress_and_kept_cards_do_not_require_disk_writes(self):
        with patch.object(self.lab.garden, "persist", side_effect=AssertionError("Progress must stay in memory")) as writer:
            self.lab.choose_preset("Night orbit")
            self.lab.choose_preset("Rainy window")
            self.click(("keep", 0))
            self.lab.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
            self.lab.visitor_action()
            self.lab.visitor_action()
            writer.assert_not_called()
        self.assertFalse(self.lab.naming)
        self.assertEqual(len(self.lab.garden.cards), 1)
        self.assertTrue(self.lab.garden.discovered)
        self.assertIn("a-soft-rain", self.lab.garden.completed)
        self.assertFalse(self.folder.exists())

    def test_reopening_starts_fresh_and_leaves_existing_collection_files_untouched(self):
        from garden import Garden, SCENES, WISHES
        archive = Garden(self.folder / "gardens")
        archive.save_card("Earlier visitor", self.lab.mix)
        archive.discovered.update(scene["id"] for scene in SCENES)
        archive.completed.update(wish["id"] for wish in WISHES)
        path = archive.persist()
        original = path.read_bytes()
        self.lab.begin_keep()
        self.lab.finish_keep()
        self.lab.visitor_action()
        self.lab.visitor_action()
        self.assertTrue(self.lab.garden.cards)
        self.assertTrue(self.lab.garden.completed)
        self.assertTrue(self.lab.garden.discovered)
        self.lab.close()
        with patch("garden.Path.read_text", side_effect=AssertionError("Do not read an earlier visit")):
            self.lab = Lab(output=self.folder)
        self.addCleanup(self.lab.close)
        self.wait_ready()
        self.assertFalse(self.lab.garden.discovered)
        self.assertFalse(self.lab.garden.completed)
        self.assertFalse(self.lab.garden.cards)
        self.assertIsNone(self.lab.active_wish)
        self.assertEqual(self.lab.wish_index, 0)
        self.assertEqual(self.lab.card_page, 0)
        self.assertEqual(self.lab.guide_page, 0)
        self.assertIsNone(self.lab.discovery_current)
        self.assertFalse(self.lab.discovery_queue)
        self.assertFalse(self.lab.discovery_highlights)
        self.assertFalse(self.lab.playing)
        self.assertEqual(path.read_bytes(), original)

    def test_reset_keeps_collection_and_silent_ingredients_cannot_be_kept(self):
        self.lab.begin_keep()
        self.lab.finish_keep()
        card = self.lab.garden.cards[0]
        self.lab.reset()
        self.assertEqual(self.lab.garden.cards[0], card)
        self.assertIn("rainy-moss", self.lab.garden.discovered)
        self.lab.mix.enabled = [False] * 3
        self.lab.begin_keep()
        self.assertFalse(self.lab.naming)
        self.assertIn("Add a little", self.lab.message)

    def test_collection_pages_keep_earlier_cards_accessible(self):
        for index in range(5):
            self.lab.begin_keep()
            self.lab.garden_name = f"Garden {index}"
            self.lab.finish_keep()
        self.lab.draw()
        self.assertEqual(self.lab.card_page, 1)
        self.click(("page", -1))
        self.lab.draw()
        first = self.lab.garden.cards[0]
        self.assertIn(("restore", first["id"]), self.lab.buttons)
        self.assertNotIn(("page", -1), self.lab.buttons)

    def test_visual_feedback_changes_with_ingredients_and_ignores_master(self):
        from garden_view import draw_garden
        surface = pygame.Surface((748, 310))
        draw_garden(surface, surface.get_rect(), self.lab.mix, 1.0)
        original = pygame.image.tobytes(surface, "RGB")
        self.lab.mix.master = 0
        draw_garden(surface, surface.get_rect(), self.lab.mix, 1.0)
        self.assertEqual(original, pygame.image.tobytes(surface, "RGB"))
        self.lab.mix.enabled = [False] * 3
        draw_garden(surface, surface.get_rect(), self.lab.mix, 1.0)
        bare = pygame.image.tobytes(surface, "RGB")
        self.assertNotEqual(original, bare)
        draw_garden(surface, surface.get_rect(), self.lab.mix, 2.0)
        self.assertEqual(bare, pygame.image.tobytes(surface, "RGB"))


if __name__ == "__main__":
    unittest.main(verbosity=2)

