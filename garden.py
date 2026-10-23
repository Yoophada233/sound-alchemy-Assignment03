"""Small discoveries, optional wishes and a collection of reusable sound gardens."""

import json
import math
import time
import unicodedata
from pathlib import Path

from sound import Mix, validate

SCENES = (
    {"id": "rainy-moss", "title": "Rainy moss",
     "hint": "Rain 60% or more; Bass 50% or less; Bells 35% or less.",
     "accent": (61, 137, 119)},
    {"id": "moonlit-roots", "title": "Moonlit roots",
     "hint": "Bass above 60%; Rain and Bells 50% or less.", "accent": (112, 100, 163)},
    {"id": "firefly-grove", "title": "Firefly grove",
     "hint": "Bells 60% or more; Rain below 25%. A light shower leaves room for fireflies.",
     "accent": (190, 146, 61)},
    {"id": "dawn-chorus", "title": "Dawn chorus",
     "hint": "Rain 25-65%; Bass 20-60%; Bells 45-85%; move Sparkle halfway or higher.",
     "accent": (204, 125, 103)},
    {"id": "storm-roots", "title": "Storm roots",
     "hint": "Rain and Bass 65% or more; Bells 35% or less. Let the storm wake deep roots.",
     "accent": (74, 121, 157)},
    {"id": "crystal-rain", "title": "Crystal rain",
     "hint": "Rain 70% or more; Bells 65% or more; Bass 50% or less.",
     "accent": (92, 170, 180)},
    {"id": "starlit-canopy", "title": "Starlit canopy",
     "hint": "Rain 50% or more; Bass and Bells 65% or more; move Sparkle at least 65% right.",
     "accent": (98, 126, 184)},
    {"id": "amber-reeds", "title": "Amber reeds",
     "hint": "Rain 15-45%; Bass 35-55%; Bells 15-40%; move Pitch at least 65% right.",
     "accent": (191, 138, 64)},
)
WISHES = (
    {"id": "a-soft-rain", "visitor": "The tired traveller", "title": "A soft rain",
     "text": "Could you grow a rainy place with only a little light?",
     "scene": "rainy-moss", "hint": "Rain 60% or more; Bass 50% or less; Bells 35% or less."},
    {"id": "roots-at-night", "visitor": "The night gardener", "title": "Roots at night",
     "text": "I would love deep, gently moving roots beneath a quiet sky.",
     "scene": "moonlit-roots", "hint": "Bass 60% or more; Rain and Bells 50% or less."},
    {"id": "a-place-for-fireflies", "visitor": "The little explorer",
     "title": "A place for fireflies",
     "text": "Can you make a bright garden where fireflies gather?",
     "scene": "firefly-grove", "hint": "Bells 60% or more; Rain 45% or less. Bass is up to you."},
)
SCENE_IDS = {scene["id"] for scene in SCENES}
WISH_IDS = {wish["id"] for wish in WISHES}
WISH_LIMITS = {
    "a-soft-rain": ((0, 0.60, 1), (1, 0, 0.50), (2, 0, 0.35)),
    "roots-at-night": ((1, 0.60, 1), (0, 0, 0.50), (2, 0, 0.50)),
    "a-place-for-fireflies": ((2, 0.60, 1), (0, 0, 0.45)),
}


def effective_levels(mix):
    """Creative matching follows ingredient controls, independent of listening volume."""
    validate(mix)
    return tuple(level if on else 0.0 for level, on in zip(mix.levels, mix.enabled))


def scene_for(mix):
    """Keep the first four recipes stable; new discoveries fill their unused regions."""
    rain, bass, bells = effective_levels(mix)
    if (0.25 <= rain <= 0.65 and 0.20 <= bass <= 0.60
            and 0.45 <= bells <= 0.85 and mix.character[2] >= 0.50):
        return "dawn-chorus"
    if rain >= 0.60 and bass <= 0.50 and bells <= 0.35:
        return "rainy-moss"
    if bass >= 0.60 and rain <= 0.50 and bells <= 0.50:
        return "moonlit-roots"
    if bells >= 0.60 and rain <= 0.45:
        return "firefly-grove"
    if rain >= 0.65 and bass >= 0.65 and bells <= 0.35:
        return "storm-roots"
    if rain >= 0.70 and bells >= 0.65 and bass <= 0.50:
        return "crystal-rain"
    if rain >= 0.50 and bass >= 0.65 and bells >= 0.65 and mix.character[2] >= 0.65:
        return "starlit-canopy"
    if (0.15 <= rain <= 0.45 and 0.35 <= bass <= 0.55
            and 0.15 <= bells <= 0.40 and mix.character[1] >= 0.65):
        return "amber-reeds"
    return None


def card_name(value):
    if not isinstance(value, str) or any(unicodedata.category(c).startswith("C") for c in value):
        raise ValueError("Use a name without control characters.")
    name = value.strip()
    if not name or len(name) > 28:
        raise ValueError("Give your garden a name from 1 to 28 characters.")
    return name


def recipe_mix(recipe):
    """Validate untrusted collection data before it can change the audio controls."""
    if not isinstance(recipe, dict):
        raise ValueError("The saved recipe is not an object.")
    for key in ("levels", "character"):
        values = recipe.get(key)
        if (not isinstance(values, list) or len(values) != 3
                or any(type(v) not in (int, float) or not 0 <= v <= 1
                       or not math.isfinite(v) for v in values)):
            raise ValueError("A saved ingredient value is invalid.")
    enabled = recipe.get("enabled")
    if (not isinstance(enabled, list) or len(enabled) != 3
            or any(type(value) is not bool for value in enabled)):
        raise ValueError("A saved on/off state is invalid.")
    master = recipe.get("master")
    if type(master) not in (int, float) or not 0 <= master <= 1 or not math.isfinite(master):
        raise ValueError("The saved listening volume is invalid.")
    # Export metadata describes the recipe; it is never executed or used as a path.
    for key in ("sample_rate", "loop_seconds", "seed"):
        if type(recipe.get(key)) is not int or recipe[key] < 0:
            raise ValueError("The saved recipe metadata is invalid.")
    if not isinstance(recipe.get("rain_model"), str) or not recipe["rain_model"]:
        raise ValueError("The saved rain model is invalid.")
    mix = Mix()
    mix.levels = recipe["levels"].copy()
    mix.character = recipe["character"].copy()
    mix.enabled = enabled.copy()
    mix.master = master
    validate(mix)
    return mix


def checked_snapshot(data):
    if not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1:
        raise ValueError("This collection version is not supported.")
    for key, allowed in (("discovered", SCENE_IDS), ("completed", WISH_IDS)):
        values = data.get(key)
        if (not isinstance(values, list) or any(not isinstance(v, str) or v not in allowed
                                                for v in values)
                or len(values) != len(set(values))):
            raise ValueError("The collection's progress is invalid.")
    cards = data.get("cards")
    if not isinstance(cards, list):
        raise ValueError("The saved cards are invalid.")
    ids = set()
    clean_cards = []
    for card in cards:
        if not isinstance(card, dict):
            raise ValueError("A saved card is invalid.")
        card_id = card.get("id")
        if not isinstance(card_id, str) or not card_id.isascii() or not card_id.isdigit() or card_id in ids:
            raise ValueError("A saved card has an invalid or repeated id.")
        ids.add(card_id)
        name = card_name(card.get("name"))
        if name != card["name"]:
            raise ValueError("A saved card name contains extra spaces.")
        scene = card.get("scene")
        if scene is not None and (not isinstance(scene, str) or scene not in SCENE_IDS):
            raise ValueError("A saved card has an unknown scene.")
        mix = recipe_mix(card.get("recipe"))
        if not any(effective_levels(mix)):
            raise ValueError("A saved garden must contain at least one ingredient.")
        if scene_for(mix) != scene:
            raise ValueError("A saved garden does not match its scene.")
        clean_cards.append({"id": card_id, "name": name, "scene": scene,
                            "recipe": mix.settings()})
    return {"version": 1, "discovered": data["discovered"].copy(),
            "completed": data["completed"].copy(), "cards": clean_cards}


class Garden:
    """A fresh visit by default; an explicit folder can still read legacy archives."""

    def __init__(self, folder=None):
        self.folder = Path(folder) if folder is not None else None
        self.discovered = set()
        self.completed = set()
        self.cards = []
        self.warning = ""
        if self.folder is None:
            return
        try:
            def snapshot_order(path):
                stamp = path.stem.removeprefix("collection-")
                return (int(stamp) if stamp.isascii() and stamp.isdigit() else -1, path.name)
            snapshots = sorted(self.folder.glob("collection-*.json"),
                               key=snapshot_order, reverse=True)
        except OSError:
            self.warning = "Could not read your collection folder. You can still explore."
            return
        skipped = 0
        for path in snapshots:
            try:
                data = checked_snapshot(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, UnicodeError, ValueError, TypeError, OverflowError, RecursionError):
                skipped += 1
                continue
            self.discovered = set(data["discovered"])
            self.completed = set(data["completed"])
            self.cards = data["cards"]
            if skipped:
                self.warning = "A newer collection could not be read. Your earlier collection was recovered."
            break
        else:
            if skipped:
                self.warning = "Your saved collection could not be read. Earlier files are still safe."

    def discover(self, mix):
        scene = scene_for(mix)
        if scene is None or scene in self.discovered:
            return None
        self.discovered.add(scene)
        return scene

    def save_card(self, name, mix):
        name = card_name(name)
        mix = recipe_mix(mix.settings())
        if not any(effective_levels(mix)):
            raise ValueError("Add at least one sound before saving a garden.")
        scene = scene_for(mix)
        if scene:
            self.discovered.add(scene)
        card_id = time.time_ns()
        ids = {card["id"] for card in self.cards}
        while str(card_id) in ids:
            card_id += 1
        card = {"id": str(card_id), "name": name, "scene": scene, "recipe": mix.settings()}
        self.cards.append(card)
        # Give callers a separate recipe, so their UI cannot accidentally change the saved card.
        return {**card, "recipe": recipe_mix(card["recipe"]).settings()}

    def restore(self, card_id):
        for card in self.cards:
            if card["id"] == card_id:
                return recipe_mix(card["recipe"])
        raise ValueError("That garden card is no longer available.")

    def wish_gaps(self, wish_id, mix):
        """The same ranges drive acceptance and specific recovery instructions."""
        levels = effective_levels(mix)
        gaps = []
        for index, minimum, maximum in WISH_LIMITS[wish_id]:
            value = levels[index]
            name = ("Rain", "Bass", "Bells")[index]
            if value < minimum:
                if not mix.enabled[index]:
                    gaps.append(f"Switch {name} ON and set LEVEL to {round(minimum * 100)}% or more.")
                else:
                    gaps.append(f"Raise {name} LEVEL to {round(minimum * 100)}% or more (now {round(value * 100)}%).")
            elif value > maximum:
                gaps.append(f"Lower {name} LEVEL to {round(maximum * 100)}% or less (now {round(value * 100)}%).")
        return gaps

    def matching(self, wish_id, mix):
        # A wish accepts a broad recipe, even when it also discovers another scene.
        return wish_id in WISH_IDS and not self.wish_gaps(wish_id, mix)

    def complete(self, wish_id, mix):
        if wish_id in self.completed or not self.matching(wish_id, mix):
            return False
        self.completed.add(wish_id)
        self.discover(mix)
        return True

    def persist(self):
        if self.folder is None:
            return None
        data = checked_snapshot({"version": 1, "discovered": sorted(self.discovered),
                                 "completed": sorted(self.completed), "cards": self.cards})
        text = json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        self.folder.mkdir(parents=True, exist_ok=True)
        stamp = time.time_ns()
        while True:
            path = self.folder / f"collection-{stamp:020d}.json"
            try:
                with path.open("x", encoding="utf-8") as output:
                    output.write(text)
            except FileExistsError:
                stamp += 1
                continue
            return path
