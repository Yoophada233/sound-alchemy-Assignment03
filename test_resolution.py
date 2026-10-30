# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["pygame==2.6.1"]
# ///
"""Check native 2K/4K drawing, precise input and resolution-dependent caches."""

import os
import time
import unittest
from unittest.mock import patch

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame

from app import Lab, SIZE, PAPER, INK, GARDEN_RECT
from garden_view import draw_garden, flower_targets, garden_buffers, stage_buffers
from raster import viewport, rect as pixel_rect
from sound import Mix


class ResolutionTests(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        self.addCleanup(self.lab.close)
        deadline = time.monotonic() + 10
        while self.lab.ready_revision != self.lab.revision and time.monotonic() < deadline:
            self.lab.update()
            time.sleep(.005)
        self.assertEqual(self.lab.ready_revision, self.lab.revision)

    def resize(self, size):
        self.lab.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
        self.lab.draw()

    def physical(self, position):
        area, ratio = viewport(self.lab.screen.get_size())
        return round(area.x + position[0] * ratio), round(area.y + position[1] * ratio)

    def click(self, position):
        physical = self.physical(position)
        self.lab.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=physical))
        self.lab.event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=physical))

    def test_2k_and_4k_canvas_has_the_full_viewport_pixel_count(self):
        for window, expected in (((2560, 1440), (1920, 1440)), ((3840, 2160), (2880, 2160))):
            with self.subTest(window=window):
                self.resize(window)
                self.assertEqual(self.lab.canvas.get_size(), expected)
                self.assertEqual(self.lab.background.get_size(), expected)
                self.assertEqual(self.lab.screen.get_size(), window)

    def test_text_matches_a_direct_native_size_font_render(self):
        for size in ((2560, 1440), (3840, 2160)):
            with self.subTest(size=size):
                self.resize(size)
                self.lab.canvas.fill(PAPER)
                self.lab.text('Native type', 0, 0, 37, INK, serif=True)
                font = self.lab.font(round(37 * self.lab.render_scale), serif=True)
                glyph = font.render('Native type', True, INK)
                expected = pygame.Surface(glyph.get_size())
                expected.fill(PAPER)
                expected.blit(glyph, (0, 0))
                actual = self.lab.canvas.subsurface(expected.get_rect())
                self.assertEqual(pygame.image.tobytes(actual, 'RGB'), pygame.image.tobytes(expected, 'RGB'))

    def test_high_resolution_frame_does_not_enlarge_a_small_ui_or_alpha_garden(self):
        self.resize((3840, 2160))
        original = pygame.transform.smoothscale
        calls = []

        def observe(surface, size, *args, **kwargs):
            calls.append((surface.get_size(), size, surface.get_flags()))
            return original(surface, size, *args, **kwargs)

        with patch('pygame.transform.smoothscale', side_effect=observe):
            self.lab.draw()
        for source, destination, flags in calls:
            self.assertNotEqual(source, SIZE)
            if flags & pygame.SRCALPHA:
                self.assertLessEqual(destination[0], source[0] + 1)
                self.assertLessEqual(destination[1], source[1] + 1)

    def test_garden_geometry_is_drawn_at_its_destination_density(self):
        import garden_view
        self.resize((3840, 2160))
        area = pixel_rect(self.lab.canvas, GARDEN_RECT)
        with patch('garden_view.place_stage', wraps=garden_view.place_stage) as place:
            draw_garden(self.lab.canvas, area, self.lab.mix, 1.25)
        world = place.call_args.args[2]
        self.assertGreater(world.get_width(), 2000)
        self.assertGreaterEqual(world.get_height(), area.height - 1)

    def test_flower_and_slider_clicks_remain_correct_at_both_resolutions(self):
        for size in ((2560, 1440), (3840, 2160)):
            with self.subTest(size=size):
                self.resize(size)
                before = self.lab.mix.flower_steps[1]
                self.click(flower_targets(GARDEN_RECT, self.lab.mix)[1].center)
                self.assertIs(self.lab.mix.flower_steps[1], not before)
                track = next(rect for key, rect in self.lab.sliders if key == ('level', 0))
                self.click((track.left + track.width * .25, track.centery))
                self.assertAlmostEqual(self.lab.mix.levels[0], .25, delta=.002)

    def test_letterbox_and_tools_do_not_edit_hidden_controls(self):
        self.resize((3840, 2160))
        recipe = self.lab.mix.settings()
        self.lab.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(20, 600)))
        self.assertEqual(self.lab.mix.settings(), recipe)
        self.click(self.lab.buttons[('letter', 0)].center)
        self.lab.draw()
        self.click(flower_targets(GARDEN_RECT, self.lab.mix)[3].center)
        self.assertEqual(self.lab.mix.flower_steps, recipe['flower_steps'])

    def test_naming_candidate_box_tracks_native_pixels_and_resizes(self):
        self.resize((3840, 2160))
        with patch('pygame.key.set_text_input_rect') as position:
            self.lab.begin_keep()
            self.assertEqual(position.call_args.args[0], self.lab.name_input_rect())
            previous = position.call_args.args[0].copy()
            self.resize((2560, 1440))
            self.assertEqual(position.call_args.args[0], self.lab.name_input_rect())
            self.assertLess(position.call_args.args[0].width, previous.width)

    def test_thumbnails_are_regenerated_sharply_without_changing_saved_recipes(self):
        self.lab.begin_keep()
        self.lab.finish_keep()
        card = self.lab.garden.cards[0]
        recipe = self.lab.garden.restore(card['id']).settings()
        self.resize((2560, 1440))
        first = self.lab.garden_thumbnails[card['id']]
        self.assertEqual(first.get_size(), (156, 99))
        self.resize((3840, 2160))
        second = self.lab.garden_thumbnails[card['id']]
        self.assertIsNot(first, second)
        self.assertEqual(second.get_size(), (234, 148))
        self.assertEqual(self.lab.garden.restore(card['id']).settings(), recipe)

    def test_reused_garden_buffers_do_not_leave_light_from_an_earlier_recipe(self):
        area = pygame.Rect(0, 0, 1836, 672)
        surface = pygame.Surface(area.size)
        mix = Mix()
        mix.levels = [1, 1, 1]
        draw_garden(surface, area, mix, .006, True)
        mix.enabled = [False] * 3
        surface.fill(PAPER)
        draw_garden(surface, area, mix, 1.25)
        reused = pygame.image.tobytes(surface, 'RGB')
        garden_buffers.cache_clear()
        stage_buffers.cache_clear()
        surface.fill(PAPER)
        draw_garden(surface, area, mix, 1.25)
        self.assertEqual(reused, pygame.image.tobytes(surface, 'RGB'))

    def test_cached_rgb_sky_stays_opaque_when_placed_in_the_alpha_frame(self):
        area = pygame.Rect(0, 0, 1836, 672)
        surface = pygame.Surface(area.size)
        for _ in range(2):
            surface.fill(PAPER)
            draw_garden(surface, area, Mix(), 1.25)
            sky = surface.get_at((area.centerx, 40))
            self.assertNotEqual(sky, pygame.Color(PAPER))
            self.assertLess(max(sky[:3]), 100)
            self.assertGreater(min(sky[:3]), 0)

    def test_returning_from_4k_to_a_small_window_keeps_state_and_hit_mapping(self):
        self.resize((3840, 2160))
        self.click(flower_targets(GARDEN_RECT, self.lab.mix)[3].center)
        pattern = self.lab.mix.flower_steps.copy()
        self.resize((960, 600))
        self.assertEqual(self.lab.canvas.get_size(), (800, 600))
        self.assertEqual(self.lab.mix.flower_steps, pattern)
        point = flower_targets(GARDEN_RECT, self.lab.mix)[3].center
        mapped = self.lab.point(self.physical(point))
        self.assertAlmostEqual(mapped[0], point[0], delta=1)
        self.assertAlmostEqual(mapped[1], point[1], delta=1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
