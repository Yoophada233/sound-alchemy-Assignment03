# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["pygame==2.6.1"]
# ///
"""Sound Alchemy: grow, discover and keep a garden made of sound."""

import argparse
import math
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_WINDOWS_DPI_AWARENESS", "permonitorv2")
import pygame

from sound import (HEADROOM, Mix, NOTE_NAMES, PRESETS, SAMPLE_RATE, SECONDS,
                   mix_layers, pcm_bytes, render_layers, save_mix)
from garden import Garden, SCENES, WISHES, effective_levels, scene_for
from fieldguide import FIELD_NOTES, listening_observation, next_nudge
from garden_view import draw_discovery_effect, draw_garden, flower_targets
from backdrop import create_background, create_surround
from specimens import draw_collection_flight, draw_specimen
from artwork import material, clear_caches as clear_art_caches
from raster import draw, make_surface, point as pixel_point, rect as pixel_rect, viewport, initial_window_size

HERE = Path(__file__).resolve().parent
SIZE = (1280, 960)
GARDEN_RECT = pygame.Rect(28, 88, 1224, 448)
VISITOR_RECT = pygame.Rect(920, 194, 310, 326)
TOOLS_RECT = pygame.Rect(948, 776, 304, 104)
GUIDE_RECT = pygame.Rect(50, 176, 730, 144)
PLAY_RECT = pygame.Rect(974, 108, 254, 52)
DISCOVERY_RECT = pygame.Rect(447, 106, 507, 58)
FOCUS_KEYS = (pygame.K_q, pygame.K_w, pygame.K_e)
FLOWER_KEYS = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4)
PAPER = "#0D1C24"
INK = "#EEE9D8"
MUTED = "#A0B4B5"
LINE = "#465B5B"
GOLD = "#C9AD72"
DARK_INK = "#202B2B"
COLORS = ("#86D8CF", "#EAA986", "#C4ACE0")
TINTS = ("#142C32", "#202D31", "#1D2A35")
NAMES = ("Rain", "Bass", "Bells")
CHARACTER_NAMES = ("Drops", "Pitch", "Sparkle")
DESCRIPTIONS = ("A steady, finely textured rain.", "A warm pulse to hold it together.",
                "Little points of light in the mix.")


class AudioPlayer:
    """Three looping layers keep their position while their volumes change."""

    def __init__(self):
        self.available = False
        self.error = ""
        self.bank = 0
        self.bell_channel = 2
        self.sounds = [None] * 6
        self.focus = None
        self.connect()

    def gain(self, mix, index):
        return (mix.levels[index] * mix.master
                if mix.enabled[index] and self.focus in (None, index) else 0)

    def connect(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1,
                                  buffer=512, allowedchanges=0)
            pygame.mixer.set_num_channels(6)
            self.available = True
            self.error = ""
        except pygame.error as error:
            self.available = False
            self.error = str(error)
        return self.available

    def play(self, layers, mix):
        try:
            sounds = [pygame.mixer.Sound(buffer=pcm_bytes([v * HEADROOM for v in layer]))
                      for layer in layers]
            for channel in range(6):
                pygame.mixer.Channel(channel).fadeout(60)
            self.bank = 1 - self.bank
            for index, sound in enumerate(sounds):
                gain = self.gain(mix, index)
                sound.set_volume(gain)
                channel = self.bank * 3 + index
                self.sounds[channel] = sound
                pygame.mixer.Channel(channel).play(sound, loops=-1, fade_ms=60)
            self.bell_channel = self.bank * 3 + 2
            return True
        except pygame.error as error:
            self.available = False
            self.error = str(error)
            self.stop()
            return False

    def replace_bells(self, layers, mix, origin):
        """Join an edited melody at the current sample; Rain and Bass keep running."""
        try:
            data = pcm_bytes([value * HEADROOM for value in layers[2]])
            sample = round((time.monotonic() - origin) * SAMPLE_RATE) % (SAMPLE_RATE * SECONDS)
            offset = sample * 2
            sound = pygame.mixer.Sound(buffer=data[offset:] + data[:offset])
            sound.set_volume(self.gain(mix, 2))
            channel = 5 if self.bell_channel == 2 else 2
            pygame.mixer.Channel(self.bell_channel).fadeout(30)
            self.sounds[channel] = sound
            pygame.mixer.Channel(channel).play(sound, loops=-1, fade_ms=30)
            self.bell_channel = channel
            return True
        except pygame.error as error:
            self.available = False
            self.error = str(error)
            self.stop()
            return False

    def set_levels(self, mix):
        """Sound.set_volume affects the running buffer; no play() call is made."""
        try:
            for channel, sound in enumerate(self.sounds):
                if sound is not None:
                    index = channel % 3
                    gain = self.gain(mix, index)
                    sound.set_volume(gain)
            return True
        except pygame.error as error:
            self.available = False
            self.error = str(error)
            self.stop()
            return False

    def stop(self):
        self.focus = None
        if pygame.mixer.get_init():
            pygame.mixer.stop()


def open_directory(path):
    """Ask the OS to show this export directory, never a shell-built command."""
    if os.name == "nt":
        os.startfile(str(path))
    else:
        command = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.Popen([command, str(path)], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)


class Lab:
    """Inputs edit the Mix; shared source layers drive playback and feedback."""

    def __init__(self, output=HERE / "out" / "mixes"):
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode(initial_window_size(SIZE), pygame.RESIZABLE)
        pygame.display.set_caption("Sound garden | a moonlit music box")
        self.render_scale = 1.0
        self.canvas = make_surface(SIZE)
        self.background = create_background(SIZE)
        self.surround = None
        self.surround_area = None
        self.console_ready = False
        self.panel_shadows = {}
        self.fonts = {}
        self.text_images = {}
        self.specimen_images = {}
        self.audio = AudioPlayer()
        self.pool = ThreadPoolExecutor(max_workers=1)
        self.future = None
        self.job_revision = -1
        self.job_mix = None
        self.mix = Mix()
        self.revision = 0
        self.ready_revision = -1
        self.layers = []
        self.layer_character = None
        self.layer_steps = None
        self.rhythm_character = None
        self.rhythm_steps = None
        self.samples = []
        self.waveform = []
        self.playing = False
        self.audio_started = False
        self.visual_origin = time.monotonic()
        self.running = True
        self.preset_name = "Rainy window"
        self.dragging = None
        self.pointer = (-1, -1)
        self.last_edit = 0
        self.last_export = -10
        self.output = Path(output)
        self.garden = Garden()
        self.wish_index = 0
        self.active_wish = None
        self.wish_error_at = None
        self.collection_tab = "guide"
        self.card_page = 0
        self.letter_open = False
        self.tools_open = False
        self.garden_thumbnails = {}
        self.discovery_queue = []
        self.discovery_current = None
        self.discovery_started = 0
        self.discovery_paused_at = None
        self.discovery_highlights = {}
        self.naming = False
        self.garden_name = ""
        self.composition = ""
        self.name_selected = False
        self.name_error = ""
        self.last_saved = None
        self.has_listened = False
        self.flower_edits = 0
        self.guide_scene = None
        self.guide_help = 0
        self.wish_help = False
        self.focus_source = None
        self.lesson_hidden = False
        self.cursor_kind = None
        self.message = "Click the four numbered flowers to write a melody. Press Play to hear your garden."
        if not self.audio.available:
            self.message = "No audio device yet. You can still mix and save; Play retries the connection."
        self.buttons = {}
        self.sliders = []
        for index in range(3):
            x = 28 + index * 414
            self.sliders.append((("level", index), pygame.Rect(x + 20, 631, 356, 18)))
            self.sliders.append((("character", index), pygame.Rect(x + 20, 690, 356, 18)))
        self.sliders.append((("master", 0), pygame.Rect(355, 906, 200, 18)))
        self.update()
        self.draw()

    def changed(self, message, discover=True):
        self.wish_error_at = None
        self.revision += 1
        self.last_edit = time.monotonic()
        self.message = message
        if self.audio.focus is not None and not effective_levels(self.mix)[self.audio.focus]:
            self.end_focus()
        if self.playing and not self.mix.audible():
            self.stop(self.silent_hint())
        elif self.playing and not self.audio.set_levels(self.mix):
            self.stop("Audio was interrupted. Check your output device and press Play to retry.")
        if (self.layer_character == tuple(self.mix.character)
                and self.layer_steps == tuple(self.mix.flower_steps)):
            self.refresh_mix()
        if discover:
            found = self.garden.discover(self.mix)
            if found:
                title = next(scene["title"] for scene in SCENES if scene["id"] == found)
                self.message = message + f" Discovered {title}!"
                self.announce_discovery(found)

    def announce_discovery(self, scene_id):
        if scene_id in self.discovery_highlights or scene_id in self.discovery_queue:
            return
        self.discovery_queue.append(scene_id)
        if self.discovery_current is None:
            self.next_discovery()

    def next_discovery(self):
        self.discovery_current = self.discovery_queue.pop(0) if self.discovery_queue else None
        self.discovery_paused_at = None
        if self.discovery_current is not None:
            self.discovery_started = time.monotonic()
            self.discovery_highlights[self.discovery_current] = self.discovery_started

    def update_discoveries(self, now):
        if self.discovery_current is None:
            return
        if self.naming:
            if self.discovery_paused_at is None:
                self.discovery_paused_at = now
            return
        if self.discovery_paused_at is not None:
            self.discovery_started += now - self.discovery_paused_at
            self.discovery_highlights[self.discovery_current] = self.discovery_started
            self.discovery_paused_at = None
        if now - self.discovery_started >= 4.5:
            self.next_discovery()

    def refresh_mix(self):
        self.samples = mix_layers(self.layers, self.mix)
        self.ready_revision = self.revision
        self.waveform = [self.samples[i] for i in range(0, len(self.samples), 96)]

    def stop(self, message="Stopped. Your recipe is still here."):
        self.playing = False
        self.audio_started = False
        self.audio.stop()
        self.focus_source = None
        self.message = message

    def begin_focus(self, index, source="mouse"):
        """Temporarily isolate a running layer; recipes and loop time stay intact."""
        if not self.playing or not self.audio_started:
            self.message = "Press Play first, then hold Rain, Bass or Bells to hear one layer."
            return
        if not self.character_available(index):
            self.message = f"{NAMES[index]} is silent. Switch it on and raise its LEVEL first."
            return
        if index == 2 and not any(self.mix.flower_steps):
            self.message = "The Bells are resting. Wake a numbered flower first."
            return
        if self.mix.master <= 0:
            self.message = "Raise MASTER to hear your garden."
            return
        self.audio.focus = index
        self.focus_source = source
        if not self.audio.set_levels(self.mix):
            self.stop("Audio was interrupted. Press Play to retry.")

    def end_focus(self):
        if self.audio.focus is None:
            return
        self.audio.focus = None
        self.focus_source = None
        if self.playing and not self.audio.set_levels(self.mix):
            self.stop("Audio was interrupted. Press Play to retry.")

    def open_guide(self, index):
        self.guide_scene = SCENES[index]["id"]
        self.guide_help = 0
        self.collection_tab = "guide"
        self.message = FIELD_NOTES[self.guide_scene]["clue"]

    def toggle_play(self):
        if self.playing:
            self.stop()
        elif not self.mix.audible():
            self.message = self.silent_hint()
        elif not self.audio.available and not self.audio.connect():
            self.message = "Audio unavailable. Check your output device, then try Play; saving still works."
        else:
            self.playing = True
            self.message = "Listening. Change one ingredient and notice what moves."
            if self.ready_revision == self.revision:
                self.play_samples()

    def play_samples(self, keep_clock=False):
        success = (self.audio.replace_bells(self.layers, self.mix, self.play_origin)
                   if keep_clock else self.audio.play(self.layers, self.mix))
        if not success:
            self.playing = False
            self.audio_started = False
            self.message = "Audio was interrupted. Check your output device and press Play to retry."
        else:
            if not keep_clock:
                self.play_origin = time.monotonic()
            self.rhythm_character = self.layer_character
            self.rhythm_steps = self.layer_steps
            self.audio_started = True
            self.has_listened = True

    def reset(self):
        self.stop()
        self.mix = Mix()
        self.preset_name = "Rainy window"
        self.guide_help = 0
        self.changed("Reset sounds and four-flower melody. This visit's field notes are still here.", discover=False)

    def choose_preset(self, name):
        self.mix.preset(name)
        self.preset_name = name
        self.changed(name + " loaded. Your four-flower melody is kept.")

    def export(self):
        if time.monotonic() - self.last_export < 1.5:
            return
        if self.ready_revision != self.revision:
            self.message = "Finishing your changes. Save again when the mix is ready."
            return
        if not self.mix.audible():
            self.message = "There is nothing to save yet. Raise an ingredient's LEVEL or wake a numbered flower."
            return
        try:
            path = save_mix(self.output, self.mix, self.samples)
        except (OSError, ValueError) as error:
            self.message = "Could not save. Check that the project folder is writable, then try again."
            print("Export error:", error)
            return
        self.last_export = time.monotonic()
        self.last_saved = path
        self.message = "Saved 8 seconds + recipe. Open exports to listen or share."

    def open_saved_folder(self):
        if self.last_saved is None or not self.last_saved.is_file():
            self.message = "That saved file is no longer here. Save a new mix, then open its folder."
            return
        try:
            open_directory(self.last_saved.parent.resolve())
        except OSError as error:
            self.message = "Could not open the folder. Your saved mix is still in out/mixes."
            print("Folder open error:", error)

    def update(self):
        self.update_discoveries(time.monotonic())
        if self.future is not None and self.future.done():
            future = self.future
            self.future = None
            try:
                layers = future.result()
            except Exception as error:
                # A worker failure is reported once; it must not break Stop or the window.
                self.stop("This mix could not be made. Try Reset, then change one control.")
                print("Sound generation error:", error)
                self.ready_revision = -1
                self.last_edit = float("inf")
            else:
                if (tuple(self.job_mix.character) == tuple(self.mix.character)
                        and tuple(self.job_mix.flower_steps) == tuple(self.mix.flower_steps)):
                    self.layers = layers
                    self.layer_character = tuple(self.job_mix.character)
                    self.layer_steps = tuple(self.job_mix.flower_steps)
                    self.refresh_mix()
                    if self.playing:
                        keep_clock = (self.audio_started
                                      and self.rhythm_character == self.layer_character)
                        self.play_samples(keep_clock=keep_clock)
        if (self.future is None and self.ready_revision != self.revision
                and time.monotonic() - self.last_edit >= 0.09):
            self.job_revision = self.revision
            self.job_mix = self.mix.copy()
            self.future = self.pool.submit(render_layers, self.job_mix,
                                           self.layers, self.layer_character)

    def point(self, pos):
        area, scale = viewport(self.screen.get_size(), SIZE)
        return ((pos[0] - area.x) / scale, (pos[1] - area.y) / scale)

    def name_input_rect(self):
        area, scale = viewport(self.screen.get_size(), SIZE)
        return pygame.Rect(area.x + round(361 * scale), area.y + round(401 * scale),
                           round(558 * scale), round(48 * scale))

    def slider_value(self, key):
        kind, index = key
        if kind == "master":
            return self.mix.master
        return self.mix.levels[index] if kind == "level" else self.mix.character[index]

    def character_available(self, index):
        return self.mix.enabled[index] and self.mix.levels[index] > 0

    def character_hint(self, index):
        if not self.mix.enabled[index]:
            return f"Switch {NAMES[index]} on to enable {CHARACTER_NAMES[index]}."
        return f"Raise LEVEL above 0% to enable {CHARACTER_NAMES[index]}."

    def silent_hint(self):
        if self.character_available(2) and not any(self.mix.flower_steps):
            return "Your mix is silent. Click a numbered flower to bring a bell back, then press Play."
        return "Your mix is silent. Raise a level or switch an ingredient on, then press Play."

    def toggle_flower(self, index):
        if not self.character_available(2):
            self.message = ("Switch Bells ON to edit the four flowers." if not self.mix.enabled[2]
                            else "Raise Bells LEVEL above 0% to edit and hear the four flowers.")
            return
        self.mix.flower_steps[index] = not self.mix.flower_steps[index]
        self.flower_edits += 1
        self.preset_name = None
        action = "will ring" if self.mix.flower_steps[index] else "will rest"
        message = f"Flower {index + 1} {action}. {sum(self.mix.flower_steps)} / 4 notes in your loop."
        if not any(self.mix.flower_steps):
            message = "All four flowers are resting. Click a flower to bring a bell back."
        elif self.mix.master == 0:
            message += " Raise MASTER to hear it."
        elif not self.playing:
            message += " Press Play to listen."
        self.changed(message)

    def move_slider(self, key, point):
        kind, index = key
        if kind == "character" and not self.character_available(index):
            self.dragging = None
            self.message = self.character_hint(index)
            return
        rect = next(rect for item, rect in self.sliders if item == key)
        value = max(0, min(1, (point[0] - rect.left) / rect.width))
        if abs(self.slider_value(key) - value) < 0.001:
            return
        if kind == "master":
            self.mix.master = value
            message = f"Master volume: {round(value * 100)}%."
        elif kind == "level":
            self.mix.levels[index] = value
            self.preset_name = None
            message = (f"{NAMES[index]} muted. {self.character_hint(index)}" if value == 0 else
                       f"{NAMES[index]} level: {round(value * 100)}%." +
                       (" Press Play to hear it." if not self.playing and self.mix.enabled[index] else ""))
        else:
            self.mix.character[index] = value
            self.preset_name = None
            message = ("Rain density changed.", "Bass pitch changed; the bells follow its key.",
                       "Bell resonance changed. Your four flower beats stay in place.")[index]
        self.changed(message, discover=kind != "master")

    def begin_keep(self):
        self.end_focus()
        if not any(effective_levels(self.mix)):
            self.message = "Add a little Rain, Bass or Bells before keeping a garden."
            return
        scene = next((item for item in SCENES if item["id"] == scene_for(self.mix)), None)
        self.garden_name = scene["title"] if scene else "My wild garden"
        self.composition = ""
        self.naming = True
        self.name_selected = True
        self.name_error = ""
        self.dragging = None
        pygame.key.start_text_input()
        pygame.key.set_text_input_rect(self.name_input_rect())

    def finish_keep(self):
        previous_discoveries = self.garden.discovered.copy()
        try:
            self.garden.save_card(self.garden_name, self.mix)
        except ValueError as error:
            self.name_error = str(error)
            return
        self.naming = False
        pygame.key.stop_text_input()
        self.collection_tab = "cards"
        self.card_page = (len(self.garden.cards) - 1) // 4
        self.message = "Garden kept for this visit. Click its card to restore it; closing this window clears the collection."
        for scene_id in self.garden.discovered - previous_discoveries:
            self.announce_discovery(scene_id)

    def restore_garden(self, card_id):
        try:
            restored = self.garden.restore(card_id)
        except (ValueError, KeyError):
            self.message = "That garden could not be restored. Your current sounds are still here."
            return
        self.stop()
        self.mix = restored
        self.preset_name = None
        self.changed("Garden restored. Press Play to listen, or change it into something new.", discover=False)

    def visitor_action(self):
        wish = WISHES[self.wish_index]
        previous_discoveries = self.garden.discovered.copy()
        if wish["id"] in self.garden.completed:
            return
        if self.active_wish != wish["id"]:
            self.wish_error_at = None
            self.wish_help = False
            self.active_wish = wish["id"]
            self.message = "A small invitation, at your own pace. " + FIELD_NOTES[wish["scene"]]["clue"]
        elif self.garden.complete(wish["id"], self.mix):
            self.wish_error_at = None
            self.message = f"A visitor left a thank-you stamp for {wish['title']}. Keep your garden if you like it!"
            for scene_id in self.garden.discovered - previous_discoveries:
                self.announce_discovery(scene_id)
        else:
            self.wish_error_at = time.monotonic()
            self.message = "Keep exploring. " + self.garden.wish_gaps(wish["id"], self.mix)[0]

    def name_event(self, event):
        if event.type == pygame.TEXTEDITING:
            self.composition = event.text
        elif event.type == pygame.TEXTINPUT:
            self.composition = ""
            if self.name_selected:
                self.garden_name = ""
                self.name_selected = False
            self.garden_name = (self.garden_name + event.text)[:28]
            self.name_error = ""
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.naming = False
                pygame.key.stop_text_input()
            elif event.key == pygame.K_RETURN:
                if not self.composition:
                    self.finish_keep()
            elif event.key == pygame.K_a and getattr(event, "mod", 0) & pygame.KMOD_CTRL:
                self.name_selected = True
            elif event.key == pygame.K_BACKSPACE:
                self.garden_name = "" if self.name_selected else self.garden_name[:-1]
                self.name_selected = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            point = self.point(event.pos)
            if self.buttons.get(("confirm_name", 0), pygame.Rect(0, 0, 0, 0)).collidepoint(point):
                self.finish_keep()
            elif self.buttons.get(("cancel_name", 0), pygame.Rect(0, 0, 0, 0)).collidepoint(point):
                self.naming = False
                pygame.key.stop_text_input()

    def event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            self.end_focus()
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = None
            if self.focus_source == "mouse":
                self.end_focus()
        elif event.type == pygame.KEYUP:
            if (self.focus_source == "keyboard" and self.audio.focus is not None
                    and event.key == FOCUS_KEYS[self.audio.focus]):
                self.end_focus()
        elif event.type == pygame.WINDOWLEAVE:
            if self.focus_source == "mouse":
                self.end_focus()
        elif event.type == pygame.WINDOWFOCUSLOST:
            self.dragging = None
            self.pointer = (-1, -1)
            if self.playing:
                self.stop("Stopped while you were away. Press Play to return to your mix.")
        elif self.naming:
            self.name_event(event)
        elif event.type == pygame.KEYDOWN:
            if getattr(event, "repeat", False):
                return
            if event.key in FLOWER_KEYS:
                self.toggle_flower(FLOWER_KEYS.index(event.key))
            elif event.key in FOCUS_KEYS:
                self.begin_focus(FOCUS_KEYS.index(event.key), "keyboard")
            elif event.key == pygame.K_SPACE:
                self.toggle_play()
            elif event.key == pygame.K_ESCAPE:
                self.letter_open = False
                self.tools_open = False
                self.stop()
            elif event.key == pygame.K_r:
                self.reset()
            elif event.key == pygame.K_s:
                self.export()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            point = self.point(event.pos)
            self.pointer = point
            if self.tools_open and TOOLS_RECT.collidepoint(point):
                # Disabled controls and the paper around them still cover cards below.
                if self.buttons.get(("save", 0), pygame.Rect(0, 0, 0, 0)).collidepoint(point):
                    self.export()
                elif self.buttons.get(("folder", 0), pygame.Rect(0, 0, 0, 0)).collidepoint(point):
                    self.open_saved_folder()
                return
            for key, rect in self.sliders:
                if rect.inflate(12, 20).collidepoint(point):
                    if key[0] == "character" and not self.character_available(key[1]):
                        self.dragging = None
                        self.message = self.character_hint(key[1])
                        return
                    self.dragging = key
                    self.move_slider(key, point)
                    return
            # Popovers are drawn last; their buttons receive clicks first.
            for key, rect in reversed(list(self.buttons.items())):
                if (self.letter_open and VISITOR_RECT.collidepoint(point)
                        and key[0] not in ("letter_close", "wish", "next_wish", "wish_help")):
                    continue
                if rect.collidepoint(point):
                    kind, value = key
                    if kind == "preset":
                        self.choose_preset(value)
                    elif kind == "toggle":
                        self.mix.enabled[value] = not self.mix.enabled[value]
                        self.preset_name = None
                        self.changed(f"{NAMES[value]} is now {'on' if self.mix.enabled[value] else 'off'}.")
                    elif kind == "play":
                        self.toggle_play()
                    elif kind == "reset":
                        self.reset()
                    elif kind == "save":
                        self.export()
                    elif kind == "folder":
                        self.open_saved_folder()
                    elif kind == "keep":
                        self.begin_keep()
                    elif kind == "tab":
                        self.collection_tab = value
                    elif kind == "guide":
                        self.open_guide(value)
                    elif kind in ("guide_help", "guide_recipe"):
                        self.guide_help = value
                    elif kind == "guide_close":
                        self.guide_scene = None
                        self.lesson_hidden = True
                    elif kind == "lesson_close":
                        self.lesson_hidden = True
                    elif kind == "focus":
                        self.begin_focus(value)
                    elif kind == "discovery_view":
                        self.open_guide(next(index for index, scene in enumerate(SCENES)
                                             if scene["id"] == self.discovery_current))
                    elif kind == "discovery_close":
                        self.next_discovery()
                    elif kind == "restore":
                        self.restore_garden(value)
                    elif kind == "page":
                        self.card_page = max(0, min((len(self.garden.cards) - 1) // 4,
                                                    self.card_page + value))
                    elif kind == "wish":
                        self.visitor_action()
                    elif kind == "next_wish":
                        self.wish_index = (self.wish_index + 1) % len(WISHES)
                        self.active_wish = None
                        self.wish_error_at = None
                        self.wish_help = False
                        self.message = "Another visitor note. You can explore freely or try its invitation."
                    elif kind == "letter":
                        self.end_focus()
                        self.letter_open = not self.letter_open
                        self.tools_open = False
                    elif kind == "letter_close":
                        self.letter_open = False
                    elif kind == "wish_help":
                        self.wish_help = not self.wish_help
                    elif kind == "tools":
                        self.tools_open = not self.tools_open
                        self.letter_open = False
                    return
            # Letter paper and discovery labels cover anything behind them.
            if self.guide_scene is not None and GUIDE_RECT.collidepoint(point):
                return
            if self.letter_open and VISITOR_RECT.collidepoint(point):
                return
            if self.discovery_current is not None and DISCOVERY_RECT.collidepoint(point):
                return
            for index, target in enumerate(flower_targets(GARDEN_RECT, self.mix)):
                if target.collidepoint(point):
                    self.toggle_flower(index)
                    return
        elif event.type == pygame.MOUSEMOTION:
            self.pointer = self.point(event.pos)
            if self.focus_source == "mouse" and self.audio.focus is not None:
                held = self.buttons.get(("focus", self.audio.focus))
                if held is None or not held.collidepoint(self.pointer):
                    self.end_focus()
            if self.dragging is not None:
                self.move_slider(self.dragging, self.pointer)

    def font(self, size, serif=False, bold=False):
        key = (size, serif, bold)
        if key not in self.fonts:
            # Direct font loading avoids a Pygame Windows registry-enumeration error.
            name = "georgia.ttf" if serif else "segoeuib.ttf" if bold else "segoeui.ttf"
            path = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / name
            font = pygame.font.Font(str(path) if path.is_file() else None, size)
            font.set_bold(bold)
            self.fonts[key] = font
        return self.fonts[key]

    def text(self, text, x, y, size=16, color=INK, serif=False, bold=False, center=False):
        native_size = max(1, round(size * self.render_scale))
        image_key = (text, native_size, tuple(pygame.Color(color)), serif, bold)
        rendered = self.text_images.get(image_key)
        if rendered is None:
            font = self.font(native_size, serif, bold)
            if any("\u3000" <= char <= "\uffef" for char in text):
                key = (native_size, "cjk", bold)
                if key not in self.fonts:
                    path = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "msyh.ttc"
                    self.fonts[key] = pygame.font.Font(str(path), native_size) if path.is_file() else font
                font = self.fonts[key]
            rendered = font.render(text, True, color)
            if len(self.text_images) >= 256:
                self.text_images.pop(next(iter(self.text_images)))
            self.text_images[image_key] = rendered
        rect = rendered.get_rect()
        if center:
            rect.center = pixel_point(self.canvas, (x, y))
        else:
            rect.topleft = pixel_point(self.canvas, (x, y))
        self.canvas.blit(rendered, rect)

    def specimen(self, rect, scene_id, accent, found=True):
        area = pixel_rect(self.canvas, rect)
        key = (scene_id, tuple(pygame.Color(accent)), found, area.size)
        if key not in self.specimen_images:
            image = pygame.Surface(area.size, pygame.SRCALPHA)
            draw_specimen(image, image.get_rect(), scene_id, accent, found)
            self.specimen_images[key] = image
        self.canvas.blit(self.specimen_images[key], area.topleft)

    def panel(self, rect, fill, radius=14):
        """Reuse a soft shadow; the decorative surface never changes a hitbox."""
        rect = pygame.Rect(rect)
        key = (rect.width, rect.height, radius)
        if key not in self.panel_shadows:
            shadow = make_surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA, self.render_scale)
            for pad, offset, alpha in ((9, 2, 3), (5, 4, 5), (2, 6, 9)):
                draw.rect(shadow, (0, 8, 15, alpha * 4),
                                 (10 - pad, 4 + offset, rect.width + pad * 2, rect.height + pad),
                                 border_radius=radius + pad)
            self.panel_shadows[key] = shadow
        self.canvas.blit(self.panel_shadows[key], pixel_point(self.canvas, (rect.x - 10, rect.y - 6)))
        area = pixel_rect(self.canvas, rect)
        self.canvas.blit(material(area.size, fill, round(radius * self.render_scale)), area.topleft)
        draw.rect(self.canvas, LINE, rect, 1, border_radius=radius)
        color = pygame.Color(fill)
        highlight = tuple(min(255, value + 27) for value in color[:3])
        draw.line(self.canvas, highlight, (rect.x + radius, rect.y + 1),
                         (rect.right - radius, rect.y + 1))

    def button(self, key, rect, label, active=False, primary=False, disabled=False, size=16):
        rect = pygame.Rect(rect)
        if not disabled:
            self.buttons[key] = rect
        color = "#758586" if disabled else GOLD if active or primary else "#8A9C98"
        fill = "#17252C" if disabled else "#28413E" if primary or active else "#13262D"
        if not disabled and not primary and not active and rect.collidepoint(self.pointer):
            fill = "#2A4044"
            color = GOLD
        area = pixel_rect(self.canvas, rect)
        self.canvas.blit(material(area.size, fill, round(9 * self.render_scale)), area.topleft)
        draw.rect(self.canvas, color, rect, 1, border_radius=9)
        self.text(label, rect.centerx, rect.centery - 1, size,
                  color if disabled else INK,
                  center=True, bold=primary)

    def draw_slider(self, key, color, disabled=False):
        color = "#53696C" if disabled else color
        rect = next(rect for item, rect in self.sliders if item == key)
        x = round(rect.left + rect.width * self.slider_value(key))
        draw.line(self.canvas, "#09171E", (rect.left, rect.centery + 1),
                         (rect.right, rect.centery + 1), 7)
        draw.line(self.canvas, "#46575D", (rect.left, rect.centery),
                         (rect.right, rect.centery), 4)
        if x > rect.left:
            draw.line(self.canvas, color, (rect.left, rect.centery), (x, rect.centery), 4)
        draw.circle(self.canvas, "#07141A", (x, rect.centery + 2), 11)
        draw.circle(self.canvas, "#223239" if disabled else "#C6B688", (x, rect.centery), 10)
        draw.circle(self.canvas, color if disabled else "#F1DFB0", (x, rect.centery), 9, 1)
        if disabled:
            draw.line(self.canvas, color, (x - 3, rect.centery), (x + 3, rect.centery), 2)
        else:
            draw.circle(self.canvas, "#E5D7B2", (x - 1, rect.centery - 2), 6)

    def wrapped_text(self, message, x, y, width, size=14, color=INK, line_height=21):
        line = ""
        for word in message.split():
            trial = (line + " " + word).strip()
            if line and self.font(size).size(trial)[0] > width:
                self.text(line, x, y, size, color)
                y += line_height
                line = word
            else:
                line = trial
        if line:
            self.text(line, x, y, size, color)
        return y + line_height

    def draw_transport(self, phase, audible):
        """Keep the one Play/Stop control next to the instrument, above any letter."""
        x, y, width, height = PLAY_RECT
        self.buttons[("play", 0)] = PLAY_RECT
        fill = "#E8CF91" if PLAY_RECT.collidepoint(self.pointer) else "#CEB37B"
        area = pixel_rect(self.canvas, PLAY_RECT)
        self.canvas.blit(material(area.size, fill, round(15 * self.render_scale)), area.topleft)
        draw.rect(self.canvas, "#EBDCAB", PLAY_RECT, 1, border_radius=15)
        draw.circle(self.canvas, "#8A734A", (x + 31, y + 26), 18, 1)
        if self.playing:
            draw.rect(self.canvas, DARK_INK, (x + 25, y + 20, 12, 12), border_radius=2)
        else:
            draw.polygon(self.canvas, DARK_INK, ((x + 27, y + 18), (x + 27, y + 34), (x + 39, y + 26)))
        self.text("Stop listening" if self.playing else "Play your garden",
                  x + 145, y + 26, 18, DARK_INK, bold=True, center=True)
        if self.audio.focus is not None:
            status = f"Only {NAMES[self.audio.focus]} / release for the mix"
        elif not self.audio.available:
            status = "Audio unavailable / Play to retry"
        elif self.playing and self.ready_revision != self.revision:
            status = "Preparing your latest phrase..."
        elif audible:
            status = "Listening / SPACE to stop"
        elif self.mix.master == 0:
            status = "MASTER is silent / raise it below"
        else:
            status = "Sound is off / SPACE also plays"
        self.text(status, x, y + 60, 12, "#DCE6D2")
        if self.letter_open:
            return
        slot = int(phase % SECONDS) if audible else None
        self.text("FOUR BEATS", x, y + 81, 10, "#B5CBB7", bold=True)
        for index, on in enumerate(self.mix.flower_steps):
            center = (x + 161 + index * 27, y + 89)
            draw.circle(self.canvas, "#E8D29C" if on else "#24473D", center, 5)
            draw.circle(self.canvas, "#A6BFA6", center, 5, 1)
            if slot == index:
                draw.circle(self.canvas, "#F8EDCB", center, 9, 2)
        for index, name in enumerate(NAMES):
            rect = pygame.Rect(x + index * 87, y + 106, 80, 30)
            self.buttons[("focus", index)] = rect
            selected = self.audio.focus == index
            hover = rect.collidepoint(self.pointer)
            draw.rect(self.canvas, "#E8D29C" if selected else "#34584A" if hover else "#203F36",
                      rect, border_radius=5)
            draw.rect(self.canvas, "#B1C6AA", rect, 1, border_radius=5)
            self.text(f"{'QWE'[index]}  {name}", rect.centerx, rect.centery, 13,
                      DARK_INK if selected else "#E2EBD8", center=True, bold=selected)
        self.text("HOLD a button or key to hear one layer", x, y + 144, 11, "#C9D9C2")

    def draw_field_guide(self):
        if self.guide_scene is None:
            if self.lesson_hidden:
                self.text("Four flowers. A phrase of your own.", 51, 180, 21, "#ECEDD8", serif=True)
                self.text("Click a flower or use keys 1-4. Choose a specimen below for a listening clue.",
                          51, 215, 14, "#CADBC2")
                return
            if not self.has_listened:
                step, title = "01 / LISTEN", "This garden is an instrument."
                detail = "Press Play, then tap a numbered flower. Each flower adds or rests one bell."
            elif not self.flower_edits:
                step, title = "02 / MAKE A PHRASE", "Make one beat yours."
                detail = "Tap any numbered flower, or press 1-4. Hear the gap when a flower rests."
            else:
                step, title = "03 / FOLLOW YOUR CURIOSITY", "What else could grow here?"
                detail = "Choose a specimen below. Follow its listening clue, then keep a garden you like."
            draw.line(self.canvas, "#CEBE8C", (51, 181), (51, 257), 3)
            self.text(step, 67, 179, 11, "#DBC797", bold=True)
            self.text(title, 66, 201, 24, "#F4ECCC", serif=True)
            self.wrapped_text(detail, 67, 239, 650, 14, "#D5E1CD", 20)
            self.buttons[("lesson_close", 0)] = pygame.Rect(746, 176, 30, 30)
            self.text("x", 761, 191, 17, "#B3C8AF", center=True)
            return
        scene = next(item for item in SCENES if item["id"] == self.guide_scene)
        index = SCENES.index(scene)
        note = FIELD_NOTES[self.guide_scene]
        found = self.guide_scene in self.garden.discovered
        x, y, width, height = GUIDE_RECT
        self.panel(GUIDE_RECT, "#152C34", radius=8)
        draw.line(self.canvas, scene["accent"], (x, y + 5), (x, y + height - 5), 3)
        self.specimen((x + 10, y + 24, 67, 67), scene["id"], scene["accent"], found)
        self.text(f"FIELD NOTE {index + 1:02d} / " + ("COLLECTED / TRY A VARIATION" if found else "FOLLOW A CLUE"),
                  x + 92, y + 11, 10, MUTED, bold=True)
        self.text(scene["title"] if found else note["title"], x + 91, y + 29, 21, INK, serif=True)
        if self.guide_help == 2:
            body = scene["hint"] + " Switch the needed sounds on; Bells need a lit flower."
        elif self.guide_help == 1:
            body = next_nudge(scene["id"], self.mix)
        else:
            body = note["after"] if found else note["clue"]
        self.wrapped_text(body, x + 92, y + 62, width - 114, 14, INK, 19)
        self.button(("guide_help", 0 if self.guide_help == 1 else 1), (x + 92, y + 108, 153, 27),
                    "Back to the clue" if self.guide_help == 1 else "A gentle nudge", size=12)
        self.button(("guide_recipe", 0 if self.guide_help == 2 else 2), (x + 255, y + 108, 151, 27),
                    "Hide the recipe" if self.guide_help == 2 else "Show exact recipe", size=12)
        self.text("No wrong turns. Explore at your pace.", x + 422, y + 114, 11, MUTED)
        self.buttons[("guide_close", 0)] = pygame.Rect(x + width - 33, y + 6, 27, 27)
        self.text("x", x + width - 19, y + 19, 16, MUTED, center=True)

    def draw_flower_labels(self):
        for index, target in enumerate(flower_targets(GARDEN_RECT, self.mix)):
            available = self.character_available(2)
            on = self.mix.flower_steps[index] and available
            rect = pygame.Rect(target.centerx - 29, target.bottom - 22, 58, 20)
            draw.rect(self.canvas, "#E1D6AA" if on else "#1B3D32", rect, border_radius=6)
            draw.rect(self.canvas, "#B4C5A2", rect, 1, border_radius=6)
            self.text("MUTED" if not available else "RING" if on else "REST", rect.centerx, rect.centery, 10,
                      DARK_INK if on else "#D2DFC5", bold=True, center=True)

    def update_cursor(self):
        buttons = (rect for key, rect in self.buttons.items()
                   if (not self.naming or key[0] in ("confirm_name", "cancel_name"))
                   and (not (self.letter_open and VISITOR_RECT.collidepoint(self.pointer))
                        or key[0] in ("letter_close", "wish", "next_wish", "wish_help")))
        interactive = any(rect.collidepoint(self.pointer) for rect in buttons)
        if not self.naming and not (self.letter_open and VISITOR_RECT.collidepoint(self.pointer)):
            interactive |= any(rect.inflate(12, 20).collidepoint(self.pointer) for _, rect in self.sliders)
            interactive |= any(rect.collidepoint(self.pointer) for rect in flower_targets(GARDEN_RECT, self.mix))
        kind = pygame.SYSTEM_CURSOR_HAND if interactive else pygame.SYSTEM_CURSOR_ARROW
        if kind != self.cursor_kind:
            self.cursor_kind = kind
            try:
                pygame.mouse.set_cursor(kind)
            except pygame.error:
                pass  # Dummy SDL devices do not provide system cursors.

    def draw_ingredient(self, index, now):
        x = 28 + index * 414
        on = self.mix.enabled[index]
        available = self.character_available(index)
        color = COLORS[index] if on else MUTED
        # One workbench, with consistent controls and three small botanical marks.
        self.specimen((x + 13, 563, 31, 31),
                      ("rainy-moss", "moonlit-roots", "dawn-chorus")[index], color, on)
        self.text(NAMES[index], x + 51, 560, 25, INK, serif=True)
        description = (("Rain nourishes the moss", "Bass wakes the roots",
                        "Click four flowers to write your melody")[index] if available else
                       f"Off: switch {NAMES[index]} on to hear it." if not on else
                       f"Muted: raise LEVEL to hear {NAMES[index]}.")
        self.text(description, x + 20, 596, 11, MUTED if available else INK)
        self.button(("toggle", index), (x + 310, 565, 66, 26),
                    "ON" if on else "OFF", active=on, size=13)
        draw.circle(self.canvas, color if on else "#455C62", (x + 319, 578), 3)
        self.text("VOLUME / LEVEL", x + 20, 616, 10, MUTED, bold=True)
        level = self.mix.levels[index]
        reading = "<1%" if level > 0 and round(level * 100) == 0 else f"{round(level * 100)}%"
        self.text(reading, x + 376 - self.font(13).size(reading)[0], 613, 13, color)
        self.draw_slider(("level", index), color)
        self.text("Silent", x + 20, 651, 9, MUTED)
        self.text("Loud", x + 356, 651, 9, MUTED)
        value = self.mix.character[index]
        reading = (f"{12 + round(value * 80)} / loop" if index == 0 else
                   NOTE_NAMES[round(value * 6)] if index == 1 else
                   f"{round(value * 100)}% glow")
        if not available:
            draw.rect(self.canvas, "#111E27", (x + 12, 670, 372, 51), border_radius=5)
            reading = "DISABLED"
        self.text(CHARACTER_NAMES[index].upper(), x + 20, 674, 10, MUTED, bold=True)
        self.text(reading, x + 376 - self.font(13).size(reading)[0], 671, 13,
                  color if available else MUTED)
        self.draw_slider(("character", index), color, disabled=not available)
        left, right = (("Sparse rain", "Dense rain"), ("Lower / shorter", "Higher / taller"),
                       ("Short / gentle", "Long / luminous"))[index]
        if available:
            self.text(left, x + 20, 711, 9, MUTED)
            self.text(right, x + 376 - self.font(9).size(right)[0], 711, 9, MUTED)
        else:
            self.text(self.character_hint(index), x + 20, 710, 10, MUTED)

    def draw_visitor(self):
        if not self.letter_open:
            return
        x, y, width, height = VISITOR_RECT
        self.panel(VISITOR_RECT, "#1C3037", radius=9)
        # A folded sheet is a letter, rather than another permanent dashboard card.
        draw.polygon(self.canvas, "#576258",
                            [(x + width - 22, y), (x + width - 22, y + 22), (x + width, y + 22)])
        draw.line(self.canvas, LINE, (x + 18, y + 72), (x + width - 18, y + 72))
        wish = WISHES[self.wish_index]
        done = wish["id"] in self.garden.completed
        active = self.active_wish == wish["id"]
        rejected = active and not done and self.wish_error_at is not None
        self.text("A LETTER FROM", x + 18, y + 14, 9, MUTED, bold=True)
        self.text(wish["visitor"], x + 18, y + 28, 12, MUTED)
        self.text(wish["title"], x + 18, y + 48, 23, serif=True)
        self.buttons[("letter_close", 0)] = pygame.Rect(x + width - 45, y + 10, 25, 25)
        self.text("x", x + width - 32, y + 21, 15, MUTED, center=True)
        self.wrapped_text(wish["text"], x + 18, y + 88, width - 36, 14, line_height=20)
        if done:
            draw.circle(self.canvas, COLORS[0], (x + width - 37, y + 158), 16, 2)
            draw.lines(self.canvas, COLORS[0], False,
                              [(x + width - 45, y + 158), (x + width - 39, y + 164),
                               (x + width - 29, y + 151)], 2)
        if rejected:
            elapsed = max(0, time.monotonic() - self.wish_error_at)
            pulse = max(0, 1 - elapsed / 0.9) * (0.5 + 0.5 * math.cos(elapsed * math.tau * 2 / 0.9))
            draw.rect(self.canvas, COLORS[1], VISITOR_RECT,
                             2 + round(3 * pulse), border_radius=4)
            draw.rect(self.canvas, "#3B3030", (x + 11, y + 149, width - 22, 94), border_radius=4)
            gaps = self.garden.wish_gaps(wish["id"], self.mix)
            self.text(f"NOT QUITE YET / {len(gaps)} TO ADJUST", x + 18, y + 158, 10, COLORS[1], bold=True)
            self.wrapped_text(gaps[0], x + 18, y + 179, width - 36, 13, INK, 18)
            self.text("Adjust this, then share again.", x + 18, y + 222, 11, COLORS[1])
        else:
            self.text("THANK-YOU STAMP RECEIVED" if done else
                      "YOUR INVITATION" if active else "NO TIMER. TAKE YOUR TIME.",
                      x + 18, y + 158, 10, COLORS[0] if done else MUTED, bold=True)
            self.wrapped_text("A little place made someone happy. Keep exploring!" if done else
                              (wish["hint"] if self.wish_help else FIELD_NOTES[wish["scene"]]["wish"]) if active else
                              "Open this invitation for a gentle hint. Or keep exploring on your own.",
                              x + 18, y + 181, width - 36, 13, MUTED, 18)
            if active and not done:
                self.button(("wish_help", 0), (x + 18, y + 229, 172, 24),
                            "Hide recipe numbers" if self.wish_help else "Need recipe numbers?", size=11)
        self.button(("wish", 0), (x + 18, y + 260, 172, 36),
                    "Thank you!" if done else "Share this garden" if active else "Open invitation",
                    primary=active, disabled=done, size=14)
        self.button(("next_wish", 0), (x + 200, y + 260, 92, 36), "Next note", size=14)
        self.text(f"VISITOR NOTES / OPTIONAL                       {len(self.garden.completed)} / 3",
                  x + 18, y + 306, 9, MUTED)

    def draw_collection(self):
        self.button(("tab", "guide"), (28, 744, 181, 29),
                    f"Specimens  {len(self.garden.discovered)} / {len(SCENES)}",
                    active=self.collection_tab == "guide", size=14)
        self.button(("tab", "cards"), (220, 744, 176, 29),
                    f"Kept gardens  {len(self.garden.cards)}",
                    active=self.collection_tab == "cards", size=14)
        self.text("FIELD NOTES  /  this visit only", 417, 751, 11, MUTED)
        if self.collection_tab == "guide":
            self.text("Choose a specimen. Follow a listening clue.", 965, 751, 12, INK)
            now = time.monotonic()
            for index, scene in enumerate(SCENES):
                rect = pygame.Rect(28 + index * 153, 783, 145, 91)
                found = scene["id"] in self.garden.discovered
                age = now - self.discovery_highlights.get(scene["id"], -100)
                recent = found and age < 10
                self.buttons[("guide", index)] = rect
                hovered = rect.collidepoint(self.pointer)
                if hovered or found:
                    draw.rect(self.canvas, "#263A3D" if hovered else "#172C32", rect, border_radius=8)
                draw.line(self.canvas, GOLD if found else LINE, rect.bottomleft, rect.bottomright)
                if scene["id"] == self.guide_scene:
                    draw.rect(self.canvas, scene["accent"], rect, 2, border_radius=3)
                self.text(f"{index + 1:02d}", rect.x + 8, rect.y + 7, 9, MUTED)
                self.specimen((rect.x + 29, rect.y + 1, 87, 66),
                              scene["id"], scene["accent"], found)
                if recent:
                    self.text("NEW", rect.right - 28, rect.y + 7, 9, scene["accent"], bold=True)
                    if age < 4.5:
                        draw.rect(self.canvas, scene["accent"], rect, 2, border_radius=3)
                self.text(scene["title"] if found else "Explore this", rect.centerx, rect.y + 70,
                          12, INK if found else MUTED, center=True, bold=found)
        else:
            pages = max(1, (len(self.garden.cards) + 3) // 4)
            self.card_page = max(0, min(self.card_page, pages - 1))
            self.text(f"{self.card_page + 1} / {pages}", 1090, 751, 11, MUTED)
            self.button(("page", -1), (1150, 744, 42, 29), "<", disabled=self.card_page == 0, size=14)
            self.button(("page", 1), (1204, 744, 42, 29), ">", disabled=self.card_page >= pages - 1, size=14)
            cards = self.garden.cards[self.card_page * 4:self.card_page * 4 + 4]
            if not cards:
                self.text("Keep a garden above to press its picture into your notebook.", 47, 816, 16, MUTED)
            for index, card in enumerate(cards):
                rect = pygame.Rect(28 + index * 309, 783, 297, 91)
                self.buttons[("restore", card["id"])] = rect
                self.panel(rect, "#182E35", radius=8)
                if card["id"] not in self.garden_thumbnails:
                    # Render the saved recipe, never the current sliders or a generic icon.
                    thumbnail = make_surface((104, 66), ratio=self.render_scale)
                    draw_garden(thumbnail, thumbnail.get_rect(), self.garden.restore(card["id"]), 1.25)
                    self.garden_thumbnails[card["id"]] = thumbnail
                self.canvas.blit(self.garden_thumbnails[card["id"]], pixel_point(self.canvas, (rect.x + 9, rect.y + 10)))
                name = card["name"]
                limit = 10 if any(ord(c) > 255 for c in name) else 23
                while len(name) > 1 and (self.font(15, serif=True).size(name + "...")[0] > 163
                                         or len(name) > limit):
                    name = name[:-1]
                self.text(name + ("..." if name != card["name"] else ""),
                          rect.x + 123, rect.y + 17, 15, serif=True)
                self.text("Kept for this visit", rect.x + 123, rect.y + 43, 11, MUTED)
                self.text("Click to return", rect.x + 123, rect.y + 61, 10, MUTED)

    def draw_discovery(self, now):
        if self.discovery_current is None or self.naming:
            return
        index, scene = next((index, item) for index, item in enumerate(SCENES)
                            if item["id"] == self.discovery_current)
        elapsed = max(0, now - self.discovery_started)
        draw_discovery_effect(self.canvas, pixel_rect(self.canvas, GARDEN_RECT), scene["accent"], elapsed)
        end = (100 + index * 153, 818) if self.collection_tab == "guide" else (119, 759)
        draw_collection_flight(self.canvas, pixel_point(self.canvas, (650, 423)),
                               pixel_point(self.canvas, end), scene["id"], scene["accent"], elapsed,
                               pixel_ratio=self.render_scale)
        x, y, width, height = DISCOVERY_RECT
        self.panel(DISCOVERY_RECT, "#22393E", radius=8)
        draw.line(self.canvas, scene["accent"], (x, y + 4), (x, y + height - 4), 3)
        self.specimen((x + 6, y + 3, 51, 51), scene["id"], scene["accent"])
        self.text(f"SPECIMEN {index + 1:02d} / COLLECTED", x + 65, y + 8, 10, scene["accent"], bold=True)
        self.text(scene["title"], x + 64, y + 25, 21, INK, serif=True)
        self.button(("discovery_view", 0), (x + 345, y + 15, 119, 30), "View specimen", size=12)
        self.buttons[("discovery_close", 0)] = pygame.Rect(x + width - 32, y + 5, 25, 25)
        self.text("x", x + width - 20, y + 17, 15, MUTED, center=True)

    def draw_name_dialog(self):
        shade = make_surface(SIZE, pygame.SRCALPHA, self.render_scale)
        shade.fill((21, 40, 34, 160))
        self.canvas.blit(shade, (0, 0))
        self.buttons = {}
        self.panel((330, 292, 620, 294), "#1B3038", radius=18)
        self.text("Keep this little world.", 361, 316, 30, serif=True)
        self.text("Keep it for this visit. Closing the window clears kept gardens.", 362, 365, 15, MUTED)
        draw.rect(self.canvas, "#0D2029", (361, 401, 558, 48), border_radius=7)
        draw.rect(self.canvas, COLORS[0], (361, 401, 558, 48), 2, border_radius=7)
        if self.name_selected:
            draw.rect(self.canvas, "#345957", (370, 410, 540, 30), border_radius=3)
        visible_name = ("" if self.name_selected and self.composition else self.garden_name) + self.composition
        self.text(visible_name + ("|" if int(time.monotonic() * 2) % 2 else ""),
                  376, 410, 18)
        self.text(self.name_error or "Up to 28 characters. Enter to keep / Esc to return.",
                  362, 463, 13, COLORS[1] if self.name_error else MUTED)
        self.button(("confirm_name", 0), (361, 514, 198, 41), "Keep garden", primary=True)
        self.button(("cancel_name", 0), (573, 514, 124, 41), "Back")

    def draw(self):
        now = time.monotonic()
        area, scale = viewport(self.screen.get_size(), SIZE)
        if (self.surround is None or self.surround.get_size() != self.screen.get_size()
                or self.surround_area != area):
            self.surround = create_surround(self.screen.get_size(), area)
            self.surround_area = area.copy()
        if self.canvas.get_size() != area.size or self.render_scale != scale:
            self.render_scale = scale
            self.canvas = make_surface(SIZE, ratio=scale)
            self.background = create_background(self.canvas.get_size())
            self.console_ready = False
            self.panel_shadows.clear()
            self.garden_thumbnails.clear()
            self.fonts.clear()
            self.text_images.clear()
            self.specimen_images.clear()
            clear_art_caches()
            if self.naming:
                pygame.key.set_text_input_rect(self.name_input_rect())
        if not self.console_ready:
            # The three instrument cases are static. Bake their translucent
            # edges into the native background once, rather than every frame.
            self.canvas.blit(self.background, (0, 0))
            for index in range(3):
                self.panel((28 + index * 414, 554, 396, 174), TINTS[index], radius=12)
            self.background.blit(self.canvas, (0, 0))
            self.console_ready = True
        self.canvas.blit(self.background, (0, 0))
        self.buttons = {}
        self.text("Sound garden.", 28, 12, 37, serif=True)
        self.text("A little world, grown by ear.", 31, 60, 13, MUTED)
        self.text("STARTER SEEDS", 610, 61, 9, MUTED, bold=True)
        for index, name in enumerate(PRESETS):
            self.button(("preset", name), (610 + index * 158, 20, 148, 34), name,
                        active=self.preset_name == name, size=14)
        self.button(("letter", 0), (1092, 20, 160, 34),
                    f"Letters  {len(self.garden.completed)} / 3", active=self.letter_open, size=14)
        self.text("A visitor has a small wish for you.", 1065, 61, 11, MUTED)
        audible = self.playing and self.audio_started
        phase = now - (self.play_origin if audible else self.visual_origin)
        rhythm_mix = self.mix.copy()
        if audible and self.rhythm_character is not None:
            rhythm_mix.character = list(self.rhythm_character)
            rhythm_mix.flower_steps = list(self.rhythm_steps)
        hover = None
        if not self.naming and not (self.letter_open and VISITOR_RECT.collidepoint(self.pointer)):
            hover = next((index for index, target in enumerate(flower_targets(GARDEN_RECT, self.mix))
                          if target.collidepoint(self.pointer)), None)
        draw_garden(self.canvas, pixel_rect(self.canvas, GARDEN_RECT), self.mix, phase, audible,
                    rhythm_mix=rhythm_mix, flower_hover=hover, listening_focus=self.audio.focus)
        draw.rect(self.canvas, "#877B5C", GARDEN_RECT, 2, border_radius=18)
        draw.rect(self.canvas, "#354E53", GARDEN_RECT.inflate(-6, -6), 1, border_radius=16)
        scene = next((item for item in SCENES if item["id"] == scene_for(self.mix)), None)
        self.text("YOUR LIVING GARDEN", 51, 106, 10, "#D7E7D8", bold=True)
        self.text(scene["title"] if scene else "A wild little world", 50, 123, 28, "#F3F0DC", serif=True)
        self.draw_transport(phase, audible)
        self.draw_field_guide()
        self.draw_flower_labels()
        if hover is not None:
            instruction = (f"Flower {hover + 1}: click to rest this note." if self.mix.flower_steps[hover]
                           else f"Flower {hover + 1}: click to add a bell.")
            if not self.character_available(2):
                instruction = "Switch Bells ON and raise its LEVEL to play the flowers."
        elif self.guide_scene is not None:
            instruction = FIELD_NOTES[self.guide_scene]["listen"]
        else:
            instruction = "Each numbered flower is one beat. Light a flower to ring; close it to leave a rest."
        self.text(instruction, 51, 507, 13, "#DFE8D1")
        if not self.letter_open:
            self.button(("keep", 0), (1065, 482, 165, 36), "Keep garden", primary=True, size=14)
        for index in range(3):
            self.draw_ingredient(index, now)
        self.draw_collection()
        draw.line(self.canvas, LINE, (28, 885), (1252, 885))
        self.button(("reset", 0), (28, 894, 100, 40), "Reset sounds", size=13)
        self.text("SPACE  play / stop", 145, 898, 12, INK)
        self.text("1-4  play the flowers", 145, 916, 12, MUTED)
        self.text("MASTER", 355, 890, 9, MUTED, bold=True)
        self.text(f"{round(self.mix.master * 100)}%", 522, 890, 11, INK)
        self.draw_slider(("master", 0), COLORS[0])
        pending = self.ready_revision != self.revision
        self.text("LISTENING CLOSELY" if self.audio.focus is not None else "YOUR SOUND BALANCE",
                  604, 895, 10, MUTED, bold=True)
        observation = (f"Only {NAMES[self.audio.focus]}. Release to bring your full garden back."
                       if self.audio.focus is not None else listening_observation(self.mix))
        self.wrapped_text(observation, 604, 912, 470, 12, INK, 16)
        self.button(("tools", 0), (1110, 894, 142, 40), "Tools & export", active=self.tools_open, size=14)
        self.text(self.message, 29, 941, 12, MUTED)
        self.draw_discovery(now)
        self.draw_visitor()
        if self.tools_open:
            self.panel(TOOLS_RECT, "#1C3037", radius=8)
            self.button(("save", 0), (966, 790, 268, 36), "Save 8-second WAV", disabled=pending, size=14)
            self.button(("folder", 0), (966, 834, 268, 30), "Open exports", disabled=self.last_saved is None, size=14)
        if self.naming:
            self.draw_name_dialog()
        self.update_cursor()
        self.screen.blit(self.surround, (0, 0))
        self.screen.blit(self.canvas, area.topleft)
        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()
        try:
            while self.running:
                events = pygame.event.get()
                for index, event in enumerate(events):
                    # Keep the latest point in a burst of moves, preserving clicks/releases.
                    if (event.type == pygame.MOUSEMOTION and index + 1 < len(events)
                            and events[index + 1].type == pygame.MOUSEMOTION):
                        continue
                    self.event(event)
                self.update()
                self.draw()
                clock.tick(30)
        finally:
            self.close()

    def close(self):
        self.audio.stop()
        self.pool.shutdown(wait=True, cancel_futures=True)
        pygame.quit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screenshot", type=Path, help="Render a silent screenshot, then exit")
    args = parser.parse_args()
    if args.screenshot:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
    lab = Lab()
    if args.screenshot:
        try:
            deadline = time.monotonic() + 10
            while lab.ready_revision != lab.revision and time.monotonic() < deadline:
                lab.update()
                time.sleep(0.01)
            if lab.ready_revision != lab.revision:
                raise RuntimeError("The initial mix did not finish rendering.")
            lab.draw()
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(lab.canvas, str(args.screenshot))
            print("saved", args.screenshot)
        finally:
            lab.close()
    else:
        lab.run()


if __name__ == "__main__":
    main()

