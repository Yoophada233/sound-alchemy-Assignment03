# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = []
# ///
"""Check discoveries, optional wishes and safe collection recovery."""

import json
import copy
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from garden import Garden, SCENES, WISHES, effective_levels, scene_for
from sound import Mix

HERE = Path(__file__).resolve().parent
RECIPES = ((0.80, 0.25, 0.20), (0.20, 0.80, 0.20),
           (0.15, 0.20, 0.80), (0.50, 0.40, 0.65))


class GardenTests(unittest.TestCase):
    def setUp(self):
        self.folder = HERE / "out" / "garden-checks" / str(time.time_ns())
        self.garden = Garden(self.folder)

    def mix(self, index):
        mix = Mix()
        mix.levels = list(RECIPES[index])
        if index == 3:
            mix.character[2] = 0.75
        return mix

    def test_new_session_creates_no_files_and_no_free_progress(self):
        self.assertFalse(self.folder.exists())
        self.assertEqual(self.garden.discovered, set())
        self.assertEqual(self.garden.completed, set())
        self.assertEqual(self.garden.cards, [])

    def test_all_four_scenes_can_be_discovered_once(self):
        for index, scene in enumerate(SCENES):
            mix = self.mix(index)
            self.assertEqual(self.garden.discover(mix), scene["id"])
            self.assertIsNone(self.garden.discover(mix))
        self.assertEqual(self.garden.discovered, {s["id"] for s in SCENES})

    def test_muted_ingredients_count_as_zero_but_master_is_independent(self):
        mix = self.mix(0)
        mix.master = 0
        self.assertEqual(scene_for(mix), "rainy-moss")
        mix.enabled[0] = False
        self.assertEqual(effective_levels(mix), (0, 0.25, 0.20))
        self.assertIsNone(scene_for(mix))

    def test_dawn_needs_sparkle_and_has_precedence_over_fireflies(self):
        mix = self.mix(3)
        mix.levels[0] = 0.40
        self.assertEqual(scene_for(mix), "dawn-chorus")
        mix.character[2] = 0.20
        self.assertEqual(scene_for(mix), "firefly-grove")

    def test_card_and_restoration_are_independent_copies(self):
        mix = self.mix(0)
        card = self.garden.save_card("  My first rain  ", mix)
        self.assertEqual(card["name"], "My first rain")
        mix.levels[0] = 0
        card["recipe"]["levels"][0] = 0
        restored = self.garden.restore(card["id"])
        self.assertEqual(restored.levels, list(RECIPES[0]))
        restored.enabled[0] = False
        self.assertTrue(self.garden.restore(card["id"]).enabled[0])

    def test_duplicate_names_get_unique_ids(self):
        with patch("garden.time.time_ns", return_value=123):
            first = self.garden.save_card("Rain", self.mix(0))
            second = self.garden.save_card("Rain", self.mix(0))
        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(len(self.garden.cards), 2)

    def test_invalid_names_and_silent_gardens_do_not_add_cards(self):
        for name in ("", "  ", "a" * 29, "line\nbreak", "tab\t", "\u200b", None):
            with self.assertRaises(ValueError):
                self.garden.save_card(name, self.mix(0))
        mix = self.mix(0)
        mix.enabled = [False, False, False]
        with self.assertRaises(ValueError):
            self.garden.save_card("Silent", mix)
        self.assertEqual(self.garden.cards, [])
        mix.enabled[0] = True
        mix.master = 0
        self.assertEqual(self.garden.save_card("Quiet listening", mix)["scene"], "rainy-moss")

    def test_every_wish_is_reachable_and_repeated_completion_is_not_a_reward(self):
        for index, wish in enumerate(WISHES):
            wrong = self.mix((index + 1) % 3)
            self.assertFalse(self.garden.complete(wish["id"], wrong))
            self.assertTrue(self.garden.matching(wish["id"], self.mix(index)))
            self.assertTrue(self.garden.complete(wish["id"], self.mix(index)))
            self.assertFalse(self.garden.complete(wish["id"], self.mix(index)))
        self.assertEqual(self.garden.completed, {w["id"] for w in WISHES})
        self.assertFalse(self.garden.complete("unknown-wish", self.mix(0)))

    def test_firefly_wish_accepts_a_dawn_garden_and_matches_its_visible_hint(self):
        mix = Mix()
        mix.preset("Glass garden")
        self.assertEqual(scene_for(mix), "dawn-chorus")
        self.assertTrue(self.garden.matching("a-place-for-fireflies", mix))
        self.assertTrue(self.garden.complete("a-place-for-fireflies", mix))
        self.assertIn("dawn-chorus", self.garden.discovered)
        # The wish accepts its exact inclusive boundaries regardless of Bass.
        mix.levels = [0.45, 1.0, 0.60]
        self.assertTrue(self.garden.matching("a-place-for-fireflies", mix))
        mix.enabled[2] = False
        self.assertFalse(self.garden.matching("a-place-for-fireflies", mix))

    def test_moonlit_wish_does_not_fail_at_an_overlapping_dawn_boundary(self):
        mix = self.mix(3)
        mix.levels = [0.40, 0.60, 0.50]
        self.assertEqual(scene_for(mix), "dawn-chorus")
        self.assertTrue(self.garden.matching("roots-at-night", mix))

    def test_round_trip_preserves_cards_progress_and_earlier_snapshots(self):
        card = self.garden.save_card("My garden", self.mix(0))
        self.garden.complete(WISHES[0]["id"], self.mix(0))
        with patch("garden.time.time_ns", return_value=456):
            first = self.garden.persist()
            original = first.read_bytes()
            second = self.garden.persist()
        self.assertNotEqual(first, second)
        self.assertEqual(first.read_bytes(), original)
        loaded = Garden(self.folder)
        self.assertEqual(loaded.cards, self.garden.cards)
        self.assertEqual(loaded.discovered, self.garden.discovered)
        self.assertEqual(loaded.completed, self.garden.completed)
        self.assertEqual(loaded.restore(card["id"]).settings(), self.mix(0).settings())
        self.assertEqual(loaded.warning, "")

    def test_corrupt_newest_snapshot_recovers_earlier_valid_snapshot(self):
        self.garden.save_card("Earlier rain", self.mix(0))
        earlier = self.garden.persist()
        corrupt = self.folder / "collection-99999999999999999999.json"
        corrupt.write_text("{interrupted", encoding="utf-8")
        loaded = Garden(self.folder)
        self.assertEqual(loaded.cards[0]["name"], "Earlier rain")
        self.assertIn("recovered", loaded.warning)
        self.assertTrue(earlier.exists())
        self.assertTrue(corrupt.exists())

    def test_invalid_recipe_in_newer_snapshot_is_not_restored(self):
        self.garden.save_card("Earlier rain", self.mix(0))
        earlier = self.garden.persist()
        valid = json.loads(earlier.read_text(encoding="utf-8"))
        for index, bad in enumerate((True, "0.8", float("nan"), float("inf"), -0.1, 1.1)):
            valid["cards"][0]["recipe"]["levels"][0] = bad
            path = self.folder / f"collection-{99999999999999999990 + index}.json"
            path.write_text(json.dumps(valid), encoding="utf-8")
        loaded = Garden(self.folder)
        self.assertEqual(loaded.restore(loaded.cards[0]["id"]).levels, list(RECIPES[0]))
        self.assertIn("recovered", loaded.warning)

    def test_no_valid_snapshot_starts_empty_and_reports_the_problem(self):
        self.folder.mkdir(parents=True)
        (self.folder / "collection-123.json").write_text("[]", encoding="utf-8")
        loaded = Garden(self.folder)
        self.assertEqual(loaded.cards, [])
        self.assertTrue(loaded.warning)

    def test_invalid_progress_names_and_recipe_shapes_cannot_replace_valid_data(self):
        self.garden.save_card("Keep this garden", self.mix(0))
        path = self.garden.persist()
        original = json.loads(path.read_text(encoding="utf-8"))
        changes = (
            lambda data: data.update(version=True),
            lambda data: data.update(discovered=["unknown-scene"]),
            lambda data: data.update(completed=[WISHES[0]["id"], WISHES[0]["id"]]),
            lambda data: data["cards"][0].update(name="Invalid\nname"),
            lambda data: data["cards"][0].update(scene="unknown-scene"),
            lambda data: data["cards"][0]["recipe"].update(enabled=[1, True, True]),
            lambda data: data["cards"][0]["recipe"].update(character=[0.5]),
            lambda data: data["cards"][0]["recipe"].update(master=True),
            lambda data: data["cards"][0]["recipe"].update(sample_rate="22050"),
            lambda data: data["cards"].append(copy.deepcopy(data["cards"][0])),
        )
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                data = copy.deepcopy(original)
                change(data)
                invalid = self.folder / f"collection-{99999999999999999900 + index}.json"
                invalid.write_text(json.dumps(data), encoding="utf-8")
                loaded = Garden(self.folder)
                self.assertEqual(loaded.cards, self.garden.cards)
                self.assertIn("recovered", loaded.warning)

    def test_numeric_snapshot_order_works_with_unpadded_names(self):
        self.garden.save_card("Older", self.mix(0))
        with patch("garden.time.time_ns", return_value=1):
            path = self.garden.persist()
        older = json.loads(path.read_text(encoding="utf-8"))
        newer = copy.deepcopy(older)
        newer["cards"][0]["name"] = "Newer"
        (self.folder / "collection-9.json").write_text(json.dumps(older), encoding="utf-8")
        (self.folder / "collection-10.json").write_text(json.dumps(newer), encoding="utf-8")
        self.assertEqual(Garden(self.folder).cards[0]["name"], "Newer")

    def test_custom_recipe_is_saved_without_claiming_a_discovery(self):
        mix = Mix()
        mix.levels = [0.1, 0.1, 0.1]
        card = self.garden.save_card("A small beginning", mix)
        self.assertIsNone(card["scene"])
        self.garden.persist()
        self.assertEqual(len(Garden(self.folder).cards), 1)
        self.assertFalse(self.garden.discovered)

    def test_missing_card_and_unwritable_destination_are_clear_failures(self):
        with self.assertRaises(ValueError):
            self.garden.restore("missing")
        self.folder.mkdir(parents=True)
        blocker = self.folder / "file-instead-of-folder"
        blocker.write_text("Keep this file.", encoding="utf-8")
        garden = Garden(blocker)
        with self.assertRaises(OSError):
            garden.persist()
        self.assertEqual(blocker.read_text(encoding="utf-8"), "Keep this file.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
