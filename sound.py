"""Three synthetic ingredients, one repeatable four-second sound scene."""

import json
import math
import random
import sys
import time
import wave
from array import array
from pathlib import Path

SAMPLE_RATE = 22050
SECONDS = 4
SEED = 7
RAIN_MODEL = "minecraft-reference-v4"
# Fitted to the band powers of the user's reference BV1Pe411x7JY (60–90 s).
# These are filter coefficients, not samples copied from the recording.
RAIN_LOW_ALPHA = 0.1871169673
RAIN_UPPER_ALPHA = 0.7808628791
RAIN_FILTERS = (
    (0.8985127978, -1.7970255955, 0.8985127978, -1.7966554257, 0.7973957653),
    (0.9450501546, -1.2872928586, 0.5838864135, -1.2872928586, 0.5289365681),
)
HEADROOM = 0.25
PITCHES = (110.0, 123.4708, 130.8128, 146.8324, 164.8138, 195.9977, 220.0)
NOTE_NAMES = ("A2", "B2", "C3", "D3", "E3", "G3", "A3")
FLOWER_NOTES = (0, 7, 12, 4)
PRESETS = {
    "Rainy window": ([0.78, 0.32, 0.20], [0.62, 0.0, 0.18]),
    "Night orbit": ([0.18, 0.68, 0.44], [0.12, 0.50, 0.38]),
    "Glass garden": ([0.36, 0.26, 0.78], [0.32, 0.83, 0.85]),
}


class Mix:
    """The controls are state; changing a copy never changes the original."""

    def __init__(self):
        self.levels = [0.78, 0.32, 0.20]
        self.character = [0.62, 0.0, 0.18]
        self.enabled = [True, True, True]
        self.master = 0.70
        self.flower_steps = [True, False, True, False]

    def copy(self):
        other = Mix()
        other.levels = self.levels.copy()
        other.character = self.character.copy()
        other.enabled = self.enabled.copy()
        other.master = self.master
        other.flower_steps = list(self.flower_steps)
        return other

    def preset(self, name):
        levels, character = PRESETS[name]
        self.levels = levels.copy()
        self.character = character.copy()
        self.enabled = [True, True, True]

    def audible(self):
        if self.master <= 0:
            return False
        for index, (on, level) in enumerate(zip(self.enabled, self.levels)):
            if on and level > 0 and (index != 2 or any(self.flower_steps)):
                return True
        return False

    def settings(self):
        return {"levels": self.levels.copy(), "character": self.character.copy(),
                "enabled": self.enabled.copy(), "master": self.master,
                "flower_steps": list(self.flower_steps),
                "sample_rate": SAMPLE_RATE, "loop_seconds": SECONDS, "seed": SEED,
                "rain_model": RAIN_MODEL}


def validate(mix):
    for values in (mix.levels, mix.character):
        if len(values) != 3 or any(not math.isfinite(v) or not 0 <= v <= 1 for v in values):
            raise ValueError("Each ingredient needs a finite value between zero and one.")
    if len(mix.enabled) != 3 or any(type(on) is not bool for on in mix.enabled):
        raise ValueError("Each ingredient needs an on/off state.")
    if not math.isfinite(mix.master) or not 0 <= mix.master <= 1:
        raise ValueError("Master volume must be between zero and one.")
    if (not isinstance(mix.flower_steps, (list, tuple)) or len(mix.flower_steps) != 4
            or any(type(on) is not bool for on in mix.flower_steps)):
        raise ValueError("The melody needs four on/off flower steps.")


def fade_edges(samples):
    """An 8 ms fade at each loop edge reduces clicks when playback repeats."""
    fade = round(0.008 * SAMPLE_RATE)
    for i in range(fade):
        gain = i / fade
        samples[i] *= gain
        samples[-1 - i] *= gain
    return samples


def rain_envelope(rng):
    """A small strength change in the rain texture, without a pitched impact."""
    count = round(rng.uniform(0.035, 0.09) * SAMPLE_RATE)
    samples = []
    for i in range(count):
        position = i / (count - 1)
        envelope = 16 * position ** 2 * (1 - position) ** 2
        samples.append(envelope)
    return samples


def filter_rain(samples, coefficients):
    """A small equalizer: the previous two inputs/outputs shape the next sample."""
    b0, b1, b2, a1, a2 = coefficients
    x1 = x2 = y1 = y2 = 0.0
    result = []
    for value in samples:
        output = b0 * value + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        result.append(output)
        x2, x1 = x1, value
        y2, y1 = y1, output
    return result


def make_rain(density):
    """Shape seeded noise using the measured reference, then vary rain density."""
    if not math.isfinite(density) or not 0 <= density <= 1:
        raise ValueError("Rain density must be between zero and one.")
    count = SAMPLE_RATE * SECONDS
    rng = random.Random(SEED)
    # Match the reference's broad spectral balance before adding strength changes.
    samples = []
    low = upper = 0.0
    for _ in range(count):
        white = rng.gauss(0, 1)
        low += RAIN_LOW_ALPHA * (white - low)
        upper += RAIN_UPPER_ALPHA * (low - upper)
        samples.append(upper)
    for coefficients in RAIN_FILTERS:
        samples = filter_rain(samples, coefficients)

    motion = random.Random(SEED + 11)
    knots = [motion.uniform(0.82, 1.18) for _ in range(16)]
    strength = []
    for i in range(count):
        position = i * len(knots) / count
        segment = int(position)
        fraction = position - segment
        blend = fraction * fraction * (3 - 2 * fraction)
        drift = knots[segment] * (1 - blend) + knots[(segment + 1) % len(knots)] * blend
        strength.append(drift)

    shapes = random.Random(SEED + 1)
    grains = [rain_envelope(shapes) for _ in range(16)]
    positions = random.Random(SEED + 2)
    drops = 12 + round(density * 80)
    for _ in range(drops):
        start = positions.randrange(count)
        grain = positions.choice(grains)
        amount = positions.uniform(0.06, 0.16)
        for j, value in enumerate(grain):
            strength[(start + j) % count] += value * amount
    samples = [value * gain for value, gain in zip(samples, strength)]
    rms = math.sqrt(sum(value * value for value in samples) / count)
    gain = (0.045 + density * 0.03) / rms
    return fade_edges([value * gain for value in samples])


def bass_pulse(seconds):
    """The one-second strength cycle shared by the bass and its visible roots."""
    return 0.5 - 0.5 * math.cos(2 * math.pi * seconds)


def bell_pattern(sparkle, flower_steps=None):
    """Return the exact (sample onset, semitone) pairs in one four-second loop."""
    if not math.isfinite(sparkle) or not 0 <= sparkle <= 1:
        raise ValueError("Bell sparkle must be between zero and one.")
    if flower_steps is not None:
        if (not isinstance(flower_steps, (list, tuple)) or len(flower_steps) != 4
                or any(type(on) is not bool for on in flower_steps)):
            raise ValueError("The melody needs four on/off flower steps.")
        return tuple((step * SAMPLE_RATE, FLOWER_NOTES[step])
                     for step, on in enumerate(flower_steps) if on)
    # Keep the original automatic pattern available for older course examples.
    count = SAMPLE_RATE * SECONDS
    notes = (0, 7, 12, 4, 9, 7, 4, 12)
    number = 2 + round(sparkle * 6)
    return tuple((round(note * count / number), notes[note]) for note in range(number))


def make_bass(pitch):
    frequency = PITCHES[round(pitch * (len(PITCHES) - 1))]
    samples = []
    for i in range(SAMPLE_RATE * SECONDS):
        t = i / SAMPLE_RATE
        pulse = 0.65 + 0.35 * bass_pulse(t)
        fundamental = math.sin(2 * math.pi * frequency * t)
        harmonic = math.sin(4 * math.pi * frequency * t)
        samples.append((0.78 * fundamental + 0.22 * harmonic) * pulse)
    return fade_edges(samples)


def make_bells(sparkle, bass_pitch, flower_steps=None):
    """A small pentatonic pattern stays related to the bass pitch."""
    count = SAMPLE_RATE * SECONDS
    samples = [0.0] * count
    root = PITCHES[round(bass_pitch * (len(PITCHES) - 1))] * 4
    for start, semitone in bell_pattern(sparkle, flower_steps):
        frequency = root * 2 ** (semitone / 12)
        for j in range(round(0.70 * SAMPLE_RATE)):
            t = j / SAMPLE_RATE
            envelope = min(1, t / 0.006) * math.exp(-t * (7 - 2 * sparkle))
            tone = (math.sin(2 * math.pi * frequency * t)
                    + 0.25 * math.sin(2 * math.pi * frequency * 2.01 * t)) / 1.25
            samples[(start + j) % count] += tone * envelope * 0.65
    return fade_edges([max(-1, min(1, value)) for value in samples])


def render_layers(mix, previous=None, previous_character=None):
    """Generate all ingredients once; even muted layers stay ready to join the loop."""
    validate(mix)
    count = SAMPLE_RATE * SECONDS
    if (previous is not None and previous_character is not None
            and tuple(mix.character) == tuple(previous_character)
            and len(previous) == 3 and all(len(layer) == count for layer in previous)):
        # A flower click edits only the melody; the rain and bass keep their loops.
        return [previous[0], previous[1],
                make_bells(mix.character[2], mix.character[1], mix.flower_steps)]
    return [make_rain(mix.character[0]), make_bass(mix.character[1]),
            make_bells(mix.character[2], mix.character[1], mix.flower_steps)]


def mix_layers(layers, mix):
    """Rebalance cached ingredients without generating or restarting their patterns."""
    validate(mix)
    count = SAMPLE_RATE * SECONDS
    if len(layers) != 3 or any(len(layer) != count for layer in layers):
        raise ValueError("Mixing needs three complete ingredient loops.")
    gains = [level * mix.master * HEADROOM if on else 0
             for on, level in zip(mix.enabled, mix.levels)]
    rain, bass, bells = gains
    return [a * rain + b * bass + c * bells for a, b, c in zip(*layers)]


def render_mix(mix):
    """Make a standalone signal from the same ingredients used by live playback."""
    validate(mix)
    if not mix.audible():
        return [0.0] * (SAMPLE_RATE * SECONDS)
    return mix_layers(render_layers(mix), mix)


def pcm_bytes(samples):
    """Normalized samples become little-endian signed 16-bit mono PCM."""
    if not samples or any(not math.isfinite(v) or abs(v) > 1 for v in samples):
        raise ValueError("Audio samples must be nonempty, finite and within -1 to 1.")
    pcm = array("h", (round(value * 32767) for value in samples))
    if sys.byteorder != "little":
        pcm.byteswap()
    return pcm.tobytes()


def save_mix(folder, mix, samples):
    """Write two loops and a recipe without replacing any earlier export."""
    validate(mix)
    if len(samples) != SAMPLE_RATE * SECONDS:
        raise ValueError("Export needs one complete four-second loop.")
    data = pcm_bytes(samples)
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    stem = "mix-" + time.strftime("%Y%m%d-%H%M%S") + f"-{time.time_ns() % 1000000000:09d}"
    path = folder / (stem + ".wav")
    with path.open("xb") as stream:
        with wave.open(stream, "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(SAMPLE_RATE)
            audio.writeframes(data * 2)
    settings = mix.settings()
    settings["export_seconds"] = SECONDS * 2
    with path.with_suffix(".json").open("x", encoding="utf-8") as stream:
        json.dump(settings, stream, indent=2)
        stream.write("\n")
    return path

