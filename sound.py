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
HEADROOM = 0.25
PITCHES = (110.0, 123.4708, 130.8128, 146.8324, 164.8138, 195.9977, 220.0)
NOTE_NAMES = ("A2", "B2", "C3", "D3", "E3", "G3", "A3")
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

    def copy(self):
        other = Mix()
        other.levels = self.levels.copy()
        other.character = self.character.copy()
        other.enabled = self.enabled.copy()
        other.master = self.master
        return other

    def preset(self, name):
        levels, character = PRESETS[name]
        self.levels = levels.copy()
        self.character = character.copy()
        self.enabled = [True, True, True]

    def audible(self):
        return self.master > 0 and any(on and level > 0
                                      for on, level in zip(self.enabled, self.levels))

    def settings(self):
        return {"levels": self.levels.copy(), "character": self.character.copy(),
                "enabled": self.enabled.copy(), "master": self.master,
                "sample_rate": SAMPLE_RATE, "loop_seconds": SECONDS, "seed": SEED}


def validate(mix):
    for values in (mix.levels, mix.character):
        if len(values) != 3 or any(not math.isfinite(v) or not 0 <= v <= 1 for v in values):
            raise ValueError("Each ingredient needs a finite value between zero and one.")
    if len(mix.enabled) != 3 or any(type(on) is not bool for on in mix.enabled):
        raise ValueError("Each ingredient needs an on/off state.")
    if not math.isfinite(mix.master) or not 0 <= mix.master <= 1:
        raise ValueError("Master volume must be between zero and one.")


def fade_edges(samples):
    """An 8 ms fade at each loop edge reduces clicks when playback repeats."""
    fade = round(0.008 * SAMPLE_RATE)
    for i in range(fade):
        gain = i / fade
        samples[i] *= gain
        samples[-1 - i] *= gain
    return samples


def make_rain(density):
    """Seeded noise under short, scattered droplet envelopes."""
    rng = random.Random(SEED)
    count = SAMPLE_RATE * SECONDS
    samples = [rng.uniform(-0.12, 0.12) for _ in range(count)]
    # Neighbour averaging makes a soft background instead of a bright hiss.
    for i in range(1, count):
        samples[i] = 0.7 * samples[i - 1] + 0.3 * samples[i]
    for _ in range(12 + round(density * 80)):
        start = rng.randrange(count)
        frequency = rng.uniform(650, 1600)
        duration = rng.uniform(0.025, 0.075)
        strength = rng.uniform(0.14, 0.36)
        for j in range(round(duration * SAMPLE_RATE)):
            t = j / SAMPLE_RATE
            envelope = min(1, t / 0.002) * math.exp(-t * 85)
            value = math.sin(2 * math.pi * frequency * t) * strength * envelope
            samples[(start + j) % count] += value
    return fade_edges([max(-1, min(1, value)) for value in samples])


def make_bass(pitch):
    frequency = PITCHES[round(pitch * (len(PITCHES) - 1))]
    samples = []
    for i in range(SAMPLE_RATE * SECONDS):
        t = i / SAMPLE_RATE
        pulse = 0.65 + 0.35 * (0.5 - 0.5 * math.cos(2 * math.pi * t))
        fundamental = math.sin(2 * math.pi * frequency * t)
        harmonic = math.sin(4 * math.pi * frequency * t)
        samples.append((0.78 * fundamental + 0.22 * harmonic) * pulse)
    return fade_edges(samples)


def make_bells(sparkle, bass_pitch):
    """A small pentatonic pattern stays related to the bass pitch."""
    count = SAMPLE_RATE * SECONDS
    samples = [0.0] * count
    root = PITCHES[round(bass_pitch * (len(PITCHES) - 1))] * 4
    notes = (0, 7, 12, 4, 9, 7, 4, 12)
    number = 2 + round(sparkle * 6)
    for note in range(number):
        start = round(note * count / number)
        frequency = root * 2 ** (notes[note] / 12)
        for j in range(round(0.70 * SAMPLE_RATE)):
            t = j / SAMPLE_RATE
            envelope = min(1, t / 0.006) * math.exp(-t * (7 - 2 * sparkle))
            tone = (math.sin(2 * math.pi * frequency * t)
                    + 0.25 * math.sin(2 * math.pi * frequency * 2.01 * t)) / 1.25
            samples[(start + j) % count] += tone * envelope * 0.65
    return fade_edges([max(-1, min(1, value)) for value in samples])


def render_layers(mix):
    """Generate all ingredients once; even muted layers stay ready to join the loop."""
    validate(mix)
    return [make_rain(mix.character[0]), make_bass(mix.character[1]),
            make_bells(mix.character[2], mix.character[1])]


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

