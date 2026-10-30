"""Asset failures must never remove the instrument or its native-pixel UI."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import artwork
from garden_view import draw_garden, flower_targets
from sound import Mix


class ArtworkTests(unittest.TestCase):
    def tearDown(self):
        artwork.source.cache_clear()
        artwork.cutout.cache_clear()
        artwork.clear_caches()

    def test_shipped_sprite_sheets_have_transparency_and_all_objects(self):
        for name, count in (("flowers", 2), ("specimens", 8), ("accents", 4), ("foliage", 4)):
            sheet = artwork.source(name)
            self.assertIsNotNone(sheet)
            self.assertTrue(sheet.get_flags() & pygame.SRCALPHA)
            self.assertLessEqual(sheet.get_at((0, 0)).a, 1)
            for index in range(count):
                sprite = artwork.cutout(name, index)
                self.assertGreater(sprite.get_width(), 70)
                self.assertGreater(sprite.get_height(), 100)
                self.assertGreater(pygame.mask.from_surface(sprite).count(), 2000)

    def test_missing_and_damaged_files_are_optional_not_launch_failures(self):
        folder = Path(__file__).resolve().parent / "out" / "art-review"
        folder.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=folder) as temporary:
            with patch.object(artwork, "ASSETS", Path(temporary)):
                artwork.source.cache_clear()
                self.assertIsNone(artwork.source("landscape"))
                (Path(temporary) / "flowers.png").write_bytes(b"not a PNG")
                self.assertIsNone(artwork.source("flowers"))
                self.assertIsNone(artwork.source("foliage"))
                artwork.cutout.cache_clear()
                from backdrop import create_background, create_surround
                from foliage import frame
                self.assertEqual(pygame.mask.from_surface(frame((320, 240))).count(), 0)
                self.assertEqual(create_background((320, 240)).get_size(), (320, 240))
                self.assertEqual(create_surround((480, 240), pygame.Rect(80, 0, 320, 240)).get_size(),
                                 (480, 240))

    def test_missing_painting_keeps_procedural_flowers_and_hover_feedback(self):
        mix = Mix()
        first = pygame.Surface((1224, 448))
        second = first.copy()
        with patch("garden_view.landscape", return_value=None):
            draw_garden(first, first.get_rect(), mix, .23)
            draw_garden(second, second.get_rect(), mix, .23, flower_hover=2)
        self.assertEqual(len(flower_targets(first.get_rect(), mix)), 4)
        self.assertNotEqual(pygame.image.tobytes(first, "RGB"), pygame.image.tobytes(second, "RGB"))

    def test_wide_painted_stage_has_real_edge_scenery_instead_of_stretched_columns(self):
        canvas = pygame.Surface((1224, 448))
        mix = Mix()
        mix.enabled = [False, False, False]
        draw_garden(canvas, canvas.get_rect(), mix, 0)
        # The old edge extension repeated one source pixel across a 71px gutter.
        # The new plate must contain real horizontal detail inside that gutter.
        colors = {tuple(canvas.get_at((x, 280))) for x in range(15, 65)}
        self.assertGreater(len(colors), 12)


if __name__ == "__main__":
    unittest.main()
