"""Listening clues for a field notebook, with optional help and no extra gates."""

from garden import effective_levels, scene_for


# These are listening invitations, not extra conditions for earning a specimen.
# Safe ranges keep the optional nudges away from overlapping landscape recipes.
FIELD_NOTES = {
    "rainy-moss": {
        "title": "Let the rain lead.",
        "clue": "A soft curtain in front, a low pulse behind it. Leave just a little bell-light over the moss.",
        "wish": "Let Rain lead, with soft Bass and only a little bell-light.",
        "listen": "Hold Rain to hear its texture. Release to hear where it sits in the mix.",
        "after": "Rest one flower. Notice how the rain fills the space between the bells.",
        "ranges": ((0, .60, 1), (1, 0, .50), (2, 0, .35)),
    },
    "moonlit-roots": {
        "title": "Find the pulse underneath.",
        "clue": "Bring the warm Bass forward. Keep the rain and high lights quiet enough to feel the roots moving.",
        "wish": "Bring Bass forward. Keep Rain and Bells behind its warm pulse.",
        "listen": "Hold Bass and follow the pulse. Then let the other sounds return.",
        "after": "Leave just one flower ringing. Does the low pulse feel closer now?",
        "ranges": ((1, .60, 1), (0, 0, .50), (2, 0, .50)),
    },
    "firefly-grove": {
        "title": "Make room for small lights.",
        "clue": "Let the Bells come forward and let the rain almost disappear. Listen to the space after each note.",
        "wish": "Let Bells shine through a light shower. Choose any Bass you like.",
        "listen": "Hold Bells to hear your four-flower phrase on its own.",
        "after": "Try two neighbouring flowers, then two separated ones. Which feels more like fireflies?",
        "ranges": ((2, .60, 1), (0, 0, .24)),
    },
    "dawn-chorus": {
        "title": "Let the light linger.",
        "clue": "Keep rain and roots gentle, with clear Bells above them. Raise Sparkle so the notes leave a longer glow.",
        "listen": "Hold E while moving Sparkle. Listen to the end of a bell.",
        "after": "Remove a note and let the previous one linger. The silence is part of your phrase.",
        "ranges": ((0, .25, .65), (1, .20, .60), (2, .45, .85)),
        "character": (2, .50),
    },
    "storm-roots": {
        "title": "A storm with a heartbeat.",
        "clue": "Build a strong rain curtain around a deep, present Bass. Let the Bells retreat into the weather.",
        "listen": "Alternate holding Rain and Bass. Release to hear them working together.",
        "after": "Try one bell in the storm, then none. Keep the version that feels more spacious.",
        "ranges": ((0, .65, 1), (1, .65, 1), (2, 0, .35)),
    },
    "crystal-rain": {
        "title": "Bright notes through heavy rain.",
        "clue": "Bring Rain and Bells forward together. Keep the low Bass behind their bright, watery texture.",
        "listen": "Hold Bells, then release. Can you still follow the notes through the rain?",
        "after": "Try a pair of bells followed by a pair of rests. Listen for their edges in the rain.",
        "ranges": ((0, .70, 1), (2, .65, 1), (1, 0, .50)),
    },
    "starlit-canopy": {
        "title": "A full garden, a long echo.",
        "clue": "Let rain, Bass and Bells all be present. Give the Bells a generous Sparkle to open a roof of stars.",
        "listen": "Hold each layer in turn. Release and notice how the three share the space.",
        "after": "Light all four flowers, then leave one dark. Which phrase gives the sky more room?",
        "ranges": ((0, .50, 1), (1, .65, 1), (2, .65, 1)),
        "character": (2, .65),
    },
    "amber-reeds": {
        "title": "Lift the roots towards the light.",
        "clue": "Use gentle rain, a warm middle Bass and quiet Bells. Lift Pitch to grow a taller, golden garden.",
        "listen": "Hold W while moving Pitch. Release to hear the Bells follow its key.",
        "after": "Keep the same flower pattern and try another Pitch. Which height feels warmer?",
        "ranges": ((0, .15, .45), (1, .35, .55), (2, .15, .40)),
        "character": (1, .65),
    },
}

NAMES = ("Rain", "Bass", "Bells")


def next_nudge(scene_id, mix):
    """Offer one useful direction without exposing numbers or changing the mix."""
    note = FIELD_NOTES[scene_id]
    if scene_for(mix) == scene_id:
        return "This balance is here already. Tap a flower to make the phrase yours, or keep this garden."
    levels = effective_levels(mix)
    for index, low, high in note["ranges"]:
        if levels[index] < low:
            if not mix.enabled[index]:
                return f"Switch {NAMES[index]} on first. Then bring it into the foreground."
            if index == 2 and not any(mix.flower_steps):
                return "Wake a numbered flower first. The Bells need a note to ring."
            return (f"Bring {NAMES[index]} forward with its LEVEL. "
                    "Listen to that layer on its own, then release to compare.")
        if levels[index] > high:
            return (f"Ease {NAMES[index]} back with its LEVEL. "
                    "Leave room to notice the other sounds.")
    if "character" in note:
        index, low = note["character"]
        if mix.character[index] < low:
            return ("Raise Sparkle. Listen for the longer tail after a bell." if index == 2 else
                    "Lift Pitch. The roots grow taller and the bell notes rise with them.")
    return "Change one sound at a time. Notice which part of the garden answers."


def listening_observation(mix):
    """Describe control balance honestly, without claiming to measure audio output."""
    levels = effective_levels(mix)
    if not any(levels):
        return "An empty soundscape. Raise a LEVEL or wake a flower."
    order = sorted(range(3), key=lambda index: levels[index], reverse=True)
    lead, second = order[:2]
    if levels[lead] - levels[second] < .12:
        first = f"{NAMES[lead]} and {NAMES[second]} share the foreground."
    else:
        first = f"{NAMES[lead]} is in the foreground."
    count = sum(mix.flower_steps) if levels[2] > 0 else 0
    phrase = ("The flowers are quiet." if count == 0 else
              "One bell, then room to breathe." if count == 1 else
              "Every beat has a bell." if count == 4 else
              "Your phrase has room between its bells.")
    return first + " " + phrase
