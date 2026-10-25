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
import pygame

from sound import (HEADROOM, Mix, NOTE_NAMES, PRESETS, SAMPLE_RATE, SECONDS,
                   mix_layers, pcm_bytes, render_layers, save_mix)
from garden import Garden, SCENES, WISHES, effective_levels, scene_for
from garden_view import draw_discovery_effect, draw_garden, flower_targets
from backdrop import create_background
from specimens import draw_collection_flight, draw_specimen

HERE = Path(__file__).resolve().parent
SIZE = (1280, 960)
GARDEN_RECT = pygame.Rect(28, 88, 1224, 448)
VISITOR_RECT = pygame.Rect(920, 106, 310, 326)
TOOLS_RECT = pygame.Rect(948, 776, 304, 104)
PAPER = "#F2F7F0"
INK = "#213F35"
MUTED = "#60786A"
LINE = "#C0D2C3"
COLORS = ("#397D7B", "#B35C40", "#87669A")
TINTS = ("#EDF6EE", "#F0F3E9", "#EFF0F6")
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
        self.connect()

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
                gain = mix.levels[index] * mix.master if mix.enabled[index] else 0
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
            sound.set_volume(mix.levels[2] * mix.master if mix.enabled[2] else 0)
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
                    gain = mix.levels[index] * mix.master if mix.enabled[index] else 0
                    sound.set_volume(gain)
            return True
        except pygame.error as error:
            self.available = False
            self.error = str(error)
            self.stop()
            return False

    def stop(self):
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
        self.screen = pygame.display.set_mode(SIZE, pygame.RESIZABLE)
        pygame.display.set_caption("Sound garden | a living field notebook")
        self.canvas = pygame.Surface(SIZE)
        self.background = create_background(SIZE)
        self.panel_shadows = {}
        self.fonts = {}
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
        self.message = message

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

    def reset(self):
        self.stop()
        self.mix = Mix()
        self.preset_name = "Rainy window"
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
        width, height = self.screen.get_size()
        scale = min(width / SIZE[0], height / SIZE[1])
        left = (width - SIZE[0] * scale) / 2
        top = (height - SIZE[1] * scale) / 2
        return ((pos[0] - left) / scale, (pos[1] - top) / scale)

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
        width, height = self.screen.get_size()
        scale = min(width / SIZE[0], height / SIZE[1])
        pygame.key.set_text_input_rect(pygame.Rect(
            (width - SIZE[0] * scale) / 2 + 361 * scale,
            (height - SIZE[1] * scale) / 2 + 401 * scale, 558 * scale, 48 * scale))

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
            self.active_wish = wish["id"]
            self.message = "A small invitation, at your own pace. " + wish["hint"]
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
        elif event.type == pygame.WINDOWFOCUSLOST:
            self.dragging = None
            self.pointer = (-1, -1)
            if self.playing:
                self.stop("Stopped while you were away. Press Play to return to your mix.")
        elif self.naming:
            self.name_event(event)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
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
                        self.message = SCENES[value]["hint"]
                    elif kind == "discovery_view":
                        self.collection_tab = "guide"
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
                        self.message = "Another visitor note. You can explore freely or try its invitation."
                    elif kind == "letter":
                        self.letter_open = not self.letter_open
                        self.tools_open = False
                    elif kind == "letter_close":
                        self.letter_open = False
                    elif kind == "tools":
                        self.tools_open = not self.tools_open
                        self.letter_open = False
                    return
            # Letter paper and discovery labels cover anything behind them.
            if self.letter_open and VISITOR_RECT.collidepoint(point):
                return
            if self.discovery_current is not None and pygame.Rect(48, 421, 358, 88).collidepoint(point):
                return
            for index, target in enumerate(flower_targets(GARDEN_RECT, self.mix)):
                if target.collidepoint(point):
                    self.toggle_flower(index)
                    return
        elif event.type == pygame.MOUSEMOTION:
            self.pointer = self.point(event.pos)
            if self.dragging is not None:
                self.move_slider(self.dragging, self.pointer)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = None

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
        font = self.font(size, serif, bold)
        if any("\u3000" <= char <= "\uffef" for char in text):
            key = (size, "cjk", bold)
            if key not in self.fonts:
                path = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "msyh.ttc"
                self.fonts[key] = pygame.font.Font(str(path), size) if path.is_file() else font
            font = self.fonts[key]
        rendered = font.render(text, True, color)
        rect = rendered.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        self.canvas.blit(rendered, rect)

    def panel(self, rect, fill, radius=14):
        """Reuse a soft shadow; the decorative surface never changes a hitbox."""
        rect = pygame.Rect(rect)
        key = (rect.width, rect.height, radius)
        if key not in self.panel_shadows:
            shadow = pygame.Surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA)
            for pad, offset, alpha in ((9, 2, 3), (5, 4, 5), (2, 6, 9)):
                pygame.draw.rect(shadow, (28, 67, 46, alpha),
                                 (10 - pad, 4 + offset, rect.width + pad * 2, rect.height + pad),
                                 border_radius=radius + pad)
            self.panel_shadows[key] = shadow
        self.canvas.blit(self.panel_shadows[key], (rect.x - 10, rect.y - 6))
        pygame.draw.rect(self.canvas, fill, rect, border_radius=radius)
        pygame.draw.rect(self.canvas, LINE, rect, 1, border_radius=radius)
        color = pygame.Color(fill)
        highlight = tuple(round(value * 0.45 + 255 * 0.55) for value in color[:3])
        pygame.draw.line(self.canvas, highlight, (rect.x + radius, rect.y + 1),
                         (rect.right - radius, rect.y + 1))

    def button(self, key, rect, label, active=False, primary=False, disabled=False, size=16):
        rect = pygame.Rect(rect)
        if not disabled:
            self.buttons[key] = rect
        color = "#879E8D" if disabled else INK
        fill = "#DFE8DD" if disabled and (primary or active) else color if primary or active else PAPER
        pygame.draw.rect(self.canvas, fill, rect, border_radius=9)
        pygame.draw.rect(self.canvas, color, rect, 1, border_radius=9)
        self.text(label, rect.centerx, rect.centery - 1, size,
                  color if disabled else PAPER if primary or active else color,
                  center=True, bold=primary)

    def draw_slider(self, key, color, disabled=False):
        color = "#A8B0A4" if disabled else color
        rect = next(rect for item, rect in self.sliders if item == key)
        x = round(rect.left + rect.width * self.slider_value(key))
        pygame.draw.line(self.canvas, "#C4D3C6", (rect.left, rect.centery),
                         (rect.right, rect.centery), 4)
        if x > rect.left:
            pygame.draw.line(self.canvas, color, (rect.left, rect.centery), (x, rect.centery), 4)
        pygame.draw.circle(self.canvas, "#DDE7DD" if disabled else PAPER, (x, rect.centery), 10)
        pygame.draw.circle(self.canvas, color, (x, rect.centery), 10, 2)
        if disabled:
            pygame.draw.line(self.canvas, color, (x - 3, rect.centery), (x + 3, rect.centery), 2)
        else:
            pygame.draw.circle(self.canvas, color, (x, rect.centery), 3)

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

    def draw_ingredient(self, index, now):
        x = 28 + index * 414
        on = self.mix.enabled[index]
        available = self.character_available(index)
        color = COLORS[index] if on else MUTED
        # One workbench, with consistent controls and three small botanical marks.
        if index:
            pygame.draw.line(self.canvas, LINE, (x - 8, 568), (x - 8, 715))
        draw_specimen(self.canvas, (x + 13, 563, 31, 31),
                      ("rainy-moss", "moonlit-roots", "dawn-chorus")[index], color, on)
        self.text(NAMES[index], x + 51, 560, 25, INK, serif=True)
        description = (("Rain nourishes the moss", "Bass wakes the roots",
                        "Click four flowers to write your melody")[index] if available else
                       f"Off: switch {NAMES[index]} on to hear it." if not on else
                       f"Muted: raise LEVEL to hear {NAMES[index]}.")
        self.text(description, x + 20, 596, 11, MUTED if available else INK)
        self.button(("toggle", index), (x + 320, 565, 56, 26),
                    "ON" if on else "OFF", active=on, size=13)
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
            pygame.draw.rect(self.canvas, "#E1E9DD", (x + 12, 670, 372, 51), border_radius=5)
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
        self.panel(VISITOR_RECT, "#F6F4E6", radius=4)
        # A folded sheet is a letter, rather than another permanent dashboard card.
        pygame.draw.polygon(self.canvas, "#D9E1D1",
                            [(x + width - 22, y), (x + width - 22, y + 22), (x + width, y + 22)])
        pygame.draw.line(self.canvas, LINE, (x + 18, y + 72), (x + width - 18, y + 72))
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
            pygame.draw.circle(self.canvas, COLORS[0], (x + width - 37, y + 158), 16, 2)
            pygame.draw.lines(self.canvas, COLORS[0], False,
                              [(x + width - 45, y + 158), (x + width - 39, y + 164),
                               (x + width - 29, y + 151)], 2)
        if rejected:
            elapsed = max(0, time.monotonic() - self.wish_error_at)
            pulse = max(0, 1 - elapsed / 0.9) * (0.5 + 0.5 * math.cos(elapsed * math.tau * 2 / 0.9))
            pygame.draw.rect(self.canvas, COLORS[1], VISITOR_RECT,
                             2 + round(3 * pulse), border_radius=4)
            pygame.draw.rect(self.canvas, "#F4E1D1", (x + 11, y + 149, width - 22, 94), border_radius=4)
            gaps = self.garden.wish_gaps(wish["id"], self.mix)
            self.text(f"NOT QUITE YET / {len(gaps)} TO ADJUST", x + 18, y + 158, 10, COLORS[1], bold=True)
            self.wrapped_text(gaps[0], x + 18, y + 179, width - 36, 13, INK, 18)
            self.text("Adjust this, then share again.", x + 18, y + 222, 11, COLORS[1])
        else:
            self.text("THANK-YOU STAMP RECEIVED" if done else
                      "YOUR INVITATION" if active else "NO TIMER. TAKE YOUR TIME.",
                      x + 18, y + 158, 10, COLORS[0] if done else MUTED, bold=True)
            self.wrapped_text("A little place made someone happy. Keep exploring!" if done else
                              wish["hint"] if active else
                              "Open this invitation for a gentle hint. Or keep exploring on your own.",
                              x + 18, y + 181, width - 36, 13, MUTED, 18)
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
            self.text("Choose a specimen for a growing hint.", 997, 751, 11, MUTED)
            now = time.monotonic()
            for index, scene in enumerate(SCENES):
                rect = pygame.Rect(28 + index * 153, 783, 145, 91)
                found = scene["id"] in self.garden.discovered
                age = now - self.discovery_highlights.get(scene["id"], -100)
                recent = found and age < 10
                self.buttons[("guide", index)] = rect
                pygame.draw.rect(self.canvas, "#E7F0E1" if found else "#F0F4E9", rect, border_radius=3)
                pygame.draw.line(self.canvas, LINE, rect.bottomleft, rect.bottomright)
                self.text(f"{index + 1:02d}", rect.x + 8, rect.y + 7, 9, MUTED)
                draw_specimen(self.canvas, (rect.x + 45, rect.y + 3, 57, 57),
                              scene["id"], scene["accent"], found)
                if recent:
                    self.text("NEW", rect.right - 28, rect.y + 7, 9, scene["accent"], bold=True)
                    if age < 4.5:
                        pygame.draw.rect(self.canvas, scene["accent"], rect, 2, border_radius=3)
                self.text(scene["title"] if found else "Unobserved", rect.centerx, rect.y + 70,
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
                pygame.draw.rect(self.canvas, "#E7F0E1", rect, border_radius=3)
                if card["id"] not in self.garden_thumbnails:
                    # Render the saved recipe, never the current sliders or a generic icon.
                    thumbnail = pygame.Surface((104, 66))
                    draw_garden(thumbnail, thumbnail.get_rect(), self.garden.restore(card["id"]), 1.25)
                    self.garden_thumbnails[card["id"]] = thumbnail
                self.canvas.blit(self.garden_thumbnails[card["id"]], (rect.x + 9, rect.y + 10))
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
        draw_discovery_effect(self.canvas, GARDEN_RECT, scene["accent"], elapsed)
        end = (100 + index * 153, 818) if self.collection_tab == "guide" else (119, 759)
        draw_collection_flight(self.canvas, (650, 423), end,
                               scene["id"], scene["accent"], elapsed)
        x, y = 48, 421 + round(8 * max(0, 1 - elapsed / 0.25))
        pygame.draw.rect(self.canvas, "#0E2924", (x + 3, y + 4, 358, 76), border_radius=3)
        pygame.draw.rect(self.canvas, "#F4F5E7", (x, y, 358, 76), border_radius=3)
        pygame.draw.line(self.canvas, scene["accent"], (x, y), (x, y + 76), 3)
        draw_specimen(self.canvas, (x + 8, y + 9, 54, 54), scene["id"], scene["accent"])
        self.text(f"SPECIMEN {index + 1:02d} / COLLECTED", x + 72, y + 10, 10, scene["accent"], bold=True)
        self.text(scene["title"], x + 71, y + 27, 22, INK, serif=True)
        self.text("Filed in your field notes.", x + 72, y + 55, 11, MUTED)
        self.buttons[("discovery_view", 0)] = pygame.Rect(x + 258, y + 51, 86, 22)
        self.text("View specimen", x + 261, y + 55, 11, scene["accent"], bold=True)
        self.buttons[("discovery_close", 0)] = pygame.Rect(x + 328, y + 5, 25, 25)
        self.text("x", x + 340, y + 17, 15, MUTED, center=True)

    def draw_name_dialog(self):
        shade = pygame.Surface(SIZE, pygame.SRCALPHA)
        shade.fill((21, 40, 34, 160))
        self.canvas.blit(shade, (0, 0))
        self.buttons = {}
        pygame.draw.rect(self.canvas, PAPER, (330, 292, 620, 294), border_radius=18)
        self.text("Keep this little world.", 361, 316, 30, serif=True)
        self.text("Keep it for this visit. Closing the window clears kept gardens.", 362, 365, 15, MUTED)
        pygame.draw.rect(self.canvas, "#FFFFFF", (361, 401, 558, 48), border_radius=7)
        pygame.draw.rect(self.canvas, COLORS[0], (361, 401, 558, 48), 2, border_radius=7)
        if self.name_selected:
            pygame.draw.rect(self.canvas, "#D9E9E4", (370, 410, 540, 30), border_radius=3)
        visible_name = ("" if self.name_selected and self.composition else self.garden_name) + self.composition
        self.text(visible_name + ("|" if int(time.monotonic() * 2) % 2 else ""),
                  376, 410, 18)
        self.text(self.name_error or "Up to 28 characters. Enter to keep / Esc to return.",
                  362, 463, 13, COLORS[1] if self.name_error else MUTED)
        self.button(("confirm_name", 0), (361, 514, 198, 41), "Keep garden", primary=True)
        self.button(("cancel_name", 0), (573, 514, 124, 41), "Back")

    def draw(self):
        now = time.monotonic()
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
        draw_garden(self.canvas, GARDEN_RECT, self.mix, phase, audible,
                    rhythm_mix=rhythm_mix, flower_hover=hover)
        pygame.draw.rect(self.canvas, "#52776A", GARDEN_RECT, 1, border_radius=18)
        scene = next((item for item in SCENES if item["id"] == scene_for(self.mix)), None)
        self.text("YOUR LIVING GARDEN", 51, 106, 10, "#D7E7D8", bold=True)
        self.text(scene["title"] if scene else "A wild little world", 50, 123, 28, "#F3F0DC", serif=True)
        self.text("YOUR MELODY / CLICK FLOWERS 1-4 TO ADD OR REMOVE A NOTE", 51, 165, 11, "#C6D8B9")
        self.text("LISTENING / WATCH THE FLOWERS FOLLOW THE BELLS" if audible else
                  "PREPARING SOUND / VISUAL PREVIEW" if self.playing else
                  "SILENT PREVIEW / PRESS PLAY TO LISTEN", 51, 511, 10, "#D7E7D8")
        self.button(("keep", 0), (1065, 482, 165, 36), "Keep garden", primary=True, size=14)
        pygame.draw.rect(self.canvas, "#F0F5E9", (28, 554, 1224, 174), border_radius=5)
        pygame.draw.line(self.canvas, LINE, (28, 554), (1252, 554))
        pygame.draw.line(self.canvas, LINE, (28, 728), (1252, 728))
        for index in range(3):
            self.draw_ingredient(index, now)
        self.draw_collection()
        pygame.draw.line(self.canvas, LINE, (28, 885), (1252, 885))
        self.button(("play", 0), (28, 894, 170, 40),
                    "Stop listening" if self.playing else "Play your mix", primary=True, size=15)
        self.button(("reset", 0), (210, 894, 92, 40), "Reset", size=14)
        self.text("MASTER", 355, 890, 9, MUTED, bold=True)
        self.text(f"{round(self.mix.master * 100)}%", 522, 890, 11, INK)
        self.draw_slider(("master", 0), INK)
        pending = self.ready_revision != self.revision
        status = "Preparing your sounds..." if pending else "Listening to a 4-second loop" if self.playing else "Ready when you are"
        if not self.audio.available:
            status = "Audio unavailable / Play to retry"
        self.text(status, 604, 904, 12, MUTED)
        self.button(("tools", 0), (1110, 894, 142, 40), "Tools & export", active=self.tools_open, size=14)
        self.text(self.message, 29, 941, 12, MUTED)
        self.draw_discovery(now)
        self.draw_visitor()
        if self.tools_open:
            self.panel(TOOLS_RECT, "#F6F4E6", radius=4)
            self.button(("save", 0), (966, 790, 268, 36), "Save 8-second WAV", disabled=pending, size=14)
            self.button(("folder", 0), (966, 834, 268, 30), "Open exports", disabled=self.last_saved is None, size=14)
        if self.naming:
            self.draw_name_dialog()
        width, height = self.screen.get_size()
        scale = min(width / SIZE[0], height / SIZE[1])
        scaled = pygame.transform.smoothscale(self.canvas,
                                              (round(SIZE[0] * scale), round(SIZE[1] * scale)))
        self.screen.fill(PAPER)
        self.screen.blit(scaled, ((width - scaled.get_width()) // 2,
                                  (height - scaled.get_height()) // 2))
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

