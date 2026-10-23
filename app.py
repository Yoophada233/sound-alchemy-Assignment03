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
from garden_view import draw_discovery_effect, draw_garden
from backdrop import create_background

HERE = Path(__file__).resolve().parent
SIZE = (1280, 900)
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
            for index in range(3):
                pygame.mixer.Channel(self.bank * 3 + index).fadeout(60)
            self.bank = 1 - self.bank
            for index, sound in enumerate(sounds):
                gain = mix.levels[index] * mix.master if mix.enabled[index] else 0
                sound.set_volume(gain)
                channel = self.bank * 3 + index
                self.sounds[channel] = sound
                pygame.mixer.Channel(channel).play(sound, loops=-1, fade_ms=60)
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
        pygame.display.set_caption("Sound Alchemy | a garden made of sound")
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
        self.samples = []
        self.waveform = []
        self.playing = False
        self.visual_origin = time.monotonic()
        self.running = True
        self.preset_name = "Rainy window"
        self.dragging = None
        self.last_edit = 0
        self.last_export = -10
        self.output = Path(output)
        self.garden = Garden()
        self.wish_index = 0
        self.active_wish = None
        self.wish_error_at = None
        self.collection_tab = "guide"
        self.guide_page = 0
        self.card_page = 0
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
        self.message = "A fresh visit! Move a slider to grow your garden. Discoveries and kept gardens reset on reopen."
        if not self.audio.available:
            self.message = "No audio device yet. You can still mix and save; Play retries the connection."
        self.buttons = {}
        self.sliders = []
        for index in range(3):
            x = 34 + index * 410
            self.sliders.append((("level", index), pygame.Rect(x + 24, 522, 344, 18)))
            self.sliders.append((("character", index), pygame.Rect(x + 24, 588, 344, 18)))
        self.sliders.append((("master", 0), pygame.Rect(399, 814, 220, 18)))
        self.update()
        self.draw()

    def changed(self, message, discover=True):
        self.wish_error_at = None
        self.revision += 1
        self.last_edit = time.monotonic()
        self.message = message
        if self.playing and not self.mix.audible():
            self.stop("Your mix is silent. Raise a level or switch an ingredient on, then press Play.")
        elif self.playing and not self.audio.set_levels(self.mix):
            self.stop("Audio was interrupted. Check your output device and press Play to retry.")
        if self.layer_character == tuple(self.mix.character):
            self.refresh_mix()
        if discover:
            found = self.garden.discover(self.mix)
            if found:
                title = next(scene["title"] for scene in SCENES if scene["id"] == found)
                self.message = f"Discovered {title}! Keep this garden, or try another combination."
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
            if self.collection_tab == "guide":
                self.guide_page = next(index for index, item in enumerate(SCENES)
                                       if item["id"] == self.discovery_current) // 4

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
        self.audio.stop()
        self.message = message

    def toggle_play(self):
        if self.playing:
            self.stop()
        elif not self.mix.audible():
            self.message = "Your mix is silent. Raise a level or switch an ingredient on, then press Play."
        elif not self.audio.available and not self.audio.connect():
            self.message = "Audio unavailable. Check your output device, then try Play; saving still works."
        else:
            self.playing = True
            self.message = "Listening. Change one ingredient and notice what moves."
            if self.ready_revision == self.revision:
                self.play_samples()

    def play_samples(self):
        if not self.audio.play(self.layers, self.mix):
            self.playing = False
            self.message = "Audio was interrupted. Check your output device and press Play to retry."
        else:
            self.play_origin = time.monotonic()

    def reset(self):
        self.stop()
        self.mix = Mix()
        self.preset_name = "Rainy window"
        self.changed("Reset sounds. This visit's discoveries and kept gardens are still here.", discover=False)

    def choose_preset(self, name):
        self.mix.preset(name)
        self.preset_name = name
        self.changed(name + " loaded. Adjust one slider to make a different place.")

    def export(self):
        if time.monotonic() - self.last_export < 1.5:
            return
        if self.ready_revision != self.revision:
            self.message = "Finishing your changes. Save again when the mix is ready."
            return
        if not self.mix.audible():
            self.message = "There is nothing to save yet. Switch on an ingredient and raise its level."
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
                if tuple(self.job_mix.character) == tuple(self.mix.character):
                    self.layers = layers
                    self.layer_character = tuple(self.job_mix.character)
                    self.refresh_mix()
                    if self.playing:
                        self.play_samples()
        if (self.future is None and self.ready_revision != self.revision
                and time.monotonic() - self.last_edit >= 0.09):
            self.job_revision = self.revision
            self.job_mix = self.mix.copy()
            self.future = self.pool.submit(render_layers, self.job_mix)

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
                       "Bell pattern changed.")[index]
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
            if self.playing:
                self.stop("Stopped while you were away. Press Play to return to your mix.")
        elif self.naming:
            self.name_event(event)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.toggle_play()
            elif event.key == pygame.K_ESCAPE:
                self.stop()
            elif event.key == pygame.K_r:
                self.reset()
            elif event.key == pygame.K_s:
                self.export()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            point = self.point(event.pos)
            for key, rect in self.sliders:
                if rect.inflate(12, 20).collidepoint(point):
                    if key[0] == "character" and not self.character_available(key[1]):
                        self.dragging = None
                        self.message = self.character_hint(key[1])
                        return
                    self.dragging = key
                    self.move_slider(key, point)
                    return
            for key, rect in self.buttons.items():
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
                    elif kind == "guide_page":
                        self.guide_page = max(0, min((len(SCENES) - 1) // 4, self.guide_page + value))
                    elif kind == "discovery_view":
                        self.collection_tab = "guide"
                        self.guide_page = next(index for index, item in enumerate(SCENES)
                                               if item["id"] == self.discovery_current) // 4
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
                    return
        elif event.type == pygame.MOUSEMOTION and self.dragging is not None:
            self.move_slider(self.dragging, self.point(event.pos))
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

    def button(self, key, rect, label, active=False, primary=False, disabled=False):
        rect = pygame.Rect(rect)
        if not disabled:
            self.buttons[key] = rect
        color = "#879E8D" if disabled else INK
        fill = "#DFE8DD" if disabled and (primary or active) else color if primary or active else PAPER
        pygame.draw.rect(self.canvas, fill, rect, border_radius=9)
        pygame.draw.rect(self.canvas, color, rect, 1, border_radius=9)
        self.text(label, rect.centerx, rect.centery - 1, 16,
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
        x = 34 + index * 410
        on = self.mix.enabled[index]
        available = self.character_available(index)
        color = COLORS[index] if on else MUTED
        self.panel((x, 426, 392, 214), TINTS[index] if on else "#E3EBE1")
        self.text(NAMES[index], x + 23, 435, 29, INK, serif=True)
        description = (("Rain nourishes the moss", "Bass wakes the roots",
                        "Bells open flowers + lights")[index] if available else
                       f"Off: switch {NAMES[index]} on to hear it." if not on else
                       f"Muted: raise LEVEL to hear {NAMES[index]}.")
        self.text(description, x + 24, 476, 13, MUTED if available else INK)
        self.button(("toggle", index), (x + 310, 441, 58, 28),
                    "ON" if on else "OFF", active=on)
        self.text("VOLUME / LEVEL", x + 24, 502, 11, MUTED, bold=True)
        level = self.mix.levels[index]
        reading = "<1%" if level > 0 and round(level * 100) == 0 else f"{round(level * 100)}%"
        self.text(reading, x + 329, 499, 14, color)
        self.draw_slider(("level", index), color)
        self.text("Silent", x + 24, 544, 10, MUTED)
        self.text("Loud", x + 345, 544, 10, MUTED)
        label = CHARACTER_NAMES[index].upper()
        value = self.mix.character[index]
        reading = (f"{12 + round(value * 80)} / loop" if index == 0 else
                   NOTE_NAMES[round(value * 6)] if index == 1 else
                   f"{2 + round(value * 6)} / loop")
        if not available:
            pygame.draw.rect(self.canvas, "#DDE7DD", (x + 15, 562, 362, 70), border_radius=8)
        self.text(label, x + 24, 568, 11, MUTED, bold=True)
        if not available:
            reading = "DISABLED"
        self.text(reading, x + 368 - self.font(14).size(reading)[0], 565, 14,
                  color if available else MUTED)
        self.draw_slider(("character", index), color, disabled=not available)
        left, right = (("Sparse rain", "Dense rain"), ("Lower / shorter", "Higher / taller"),
                       ("Fewer notes + flowers", "More notes + flowers"))[index]
        if available:
            self.text(left, x + 24, 611, 10, MUTED)
            self.text(right, x + 368 - self.font(10).size(right)[0], 611, 10, MUTED)
        else:
            self.text(self.character_hint(index), x + 24, 611, 11, MUTED)

    def draw_visitor(self):
        x = 846
        self.panel((x, 98, 400, 312), "#EDF4EB", radius=16)
        self.text("VISITOR NOTES / OPTIONAL", x + 23, 116, 11, MUTED, bold=True)
        self.text(f"{len(self.garden.completed)} / 3", x + 333, 115, 12, MUTED)
        wish = WISHES[self.wish_index]
        done = wish["id"] in self.garden.completed
        active = self.active_wish == wish["id"]
        rejected = active and not done and self.wish_error_at is not None
        if rejected:
            elapsed = max(0, time.monotonic() - self.wish_error_at)
            # Two short border pulses acknowledge every click; text stays readable.
            pulse = max(0, 1 - elapsed / 0.9) * (0.5 + 0.5 * math.cos(elapsed * math.tau * 2 / 0.9))
            pygame.draw.rect(self.canvas, COLORS[1], (x, 98, 400, 312),
                             2 + round(3 * pulse), border_radius=16)
            pygame.draw.rect(self.canvas, "#F7E2D4", (x + 14, 242, 372, 92), border_radius=9)
        self.text(wish["title"], x + 23, 145, 25, serif=True)
        if done:
            pygame.draw.circle(self.canvas, COLORS[0], (x + 358, 163), 18, 2)
            pygame.draw.lines(self.canvas, COLORS[0], False,
                              [(x + 349, 162), (x + 356, 169), (x + 367, 155)], 3)
        self.wrapped_text(wish["text"], x + 23, 188, 352, 15, line_height=22)
        if rejected:
            gaps = self.garden.wish_gaps(wish["id"], self.mix)
            self.text(f"NOT QUITE YET / {len(gaps)} TO ADJUST", x + 23, 252, 11, COLORS[1], bold=True)
            self.wrapped_text(gaps[0], x + 23, 274, 352, 13, INK, 19)
            self.text("Adjust this, then share again.", x + 23, 318, 11, COLORS[1])
        else:
            self.text("THANK-YOU STAMP RECEIVED" if done else
                      "YOUR INVITATION" if active else "NO TIMER. EXPLORE AT YOUR OWN PACE.",
                      x + 23, 252, 10, COLORS[0] if done else MUTED, bold=True)
            self.wrapped_text("A little place made someone happy. Keep exploring!" if done else
                              wish["hint"] if active else
                              "Open a note for a gentle hint. You can switch notes whenever you like.",
                              x + 23, 274, 352, 13, MUTED, 19)
            self.text("FROM / " + wish["visitor"], x + 23, 321, 10, MUTED)
        self.button(("wish", 0), (x + 23, 345, 190, 37),
                    "Thank you!" if done else "Share this garden" if active else "Open invitation",
                    primary=active, disabled=done)
        self.button(("next_wish", 0), (x + 225, 345, 152, 37), "Next note")

    def draw_collection(self):
        self.button(("tab", "guide"), (34, 655, 175, 29),
                    f"Discoveries  {len(self.garden.discovered)} / {len(SCENES)}",
                    active=self.collection_tab == "guide")
        self.button(("tab", "cards"), (220, 655, 185, 29),
                    f"Kept gardens  {len(self.garden.cards)}", active=self.collection_tab == "cards")
        if self.collection_tab == "guide":
            self.text("Click a card for its recipe hint. New visit on reopen.", 423, 662, 12, MUTED)
            pages = max(1, (len(SCENES) + 3) // 4)
            self.guide_page = max(0, min(self.guide_page, pages - 1))
            self.text(f"{self.guide_page + 1} / {pages}", 1090, 661, 12, MUTED)
            self.button(("guide_page", -1), (1150, 655, 42, 29), "<", disabled=self.guide_page == 0)
            self.button(("guide_page", 1), (1204, 655, 42, 29), ">", disabled=self.guide_page >= pages - 1)
            for slot, scene in enumerate(SCENES[self.guide_page * 4:self.guide_page * 4 + 4]):
                index = self.guide_page * 4 + slot
                rect = pygame.Rect(34 + slot * 307, 695, 291, 76)
                found = scene["id"] in self.garden.discovered
                age = time.monotonic() - self.discovery_highlights.get(scene["id"], -100)
                recent = found and age < 10
                self.buttons[("guide", index)] = rect
                self.panel(rect, "#E6F0E3" if found else "#EAF1E7", radius=11)
                if recent:
                    width = 2 + round((0.5 + 0.5 * math.sin(age * math.tau * 1.6)) * 2)
                    pygame.draw.rect(self.canvas, scene["accent"], rect, width, border_radius=11)
                pygame.draw.circle(self.canvas, scene["accent"] if found else "#CFD4C9",
                                   (rect.x + 28, rect.y + 29), 9)
                self.text(scene["title"] if found else "An undiscovered garden",
                          rect.x + 46, rect.y + 14, 14, bold=found)
                self.text("NEW! / click for its recipe hint" if recent else
                          "FOUND / click for its recipe hint" if found else "?  click for a gentle hint",
                          rect.x + 19, rect.y + 46, 12, MUTED)
        else:
            self.text("Click to restore. Kept gardens last until you close this window.", 423, 662, 12, MUTED)
            pages = max(1, (len(self.garden.cards) + 3) // 4)
            self.card_page = max(0, min(self.card_page, pages - 1))
            self.text(f"{self.card_page + 1} / {pages}", 1090, 661, 12, MUTED)
            self.button(("page", -1), (1150, 655, 42, 29), "<", disabled=self.card_page == 0)
            self.button(("page", 1), (1204, 655, 42, 29), ">", disabled=self.card_page >= pages - 1)
            cards = self.garden.cards[self.card_page * 4:self.card_page * 4 + 4]
            if not cards:
                self.text("Your first garden is waiting. Adjust the sounds, then choose Keep garden above.",
                          51, 719, 17, MUTED)
            for index, card in enumerate(cards):
                rect = pygame.Rect(34 + index * 307, 695, 291, 76)
                self.buttons[("restore", card["id"])] = rect
                self.panel(rect, "#E6F0E3", radius=11)
                scene = next((item for item in SCENES if item["id"] == card["scene"]), None)
                name = card["name"]
                # A collection card is narrower than the full editable name.
                while len(name) > 1 and (self.font(16, serif=True).size(name)[0] > 248
                                         or len(name) > 16 and any(ord(c) > 255 for c in name)):
                    name = name[:-1]
                self.text(name + ("..." if name != card["name"] else ""),
                          rect.x + 17, rect.y + 13, 16, serif=True)
                self.text((scene["title"] if scene else "Wild garden") + " / restore",
                          rect.x + 17, rect.y + 47, 12, MUTED)

    def draw_discovery(self, now):
        if self.discovery_current is None or self.naming:
            return
        scene = next(item for item in SCENES if item["id"] == self.discovery_current)
        elapsed = max(0, now - self.discovery_started)
        draw_discovery_effect(self.canvas, (34, 98, 790, 312), scene["accent"], elapsed)
        rise = round(12 * max(0, 1 - elapsed / 0.25))
        x, y = 442, 111 + rise
        pygame.draw.rect(self.canvas, "#102F29", (x + 4, y + 5, 362, 134), border_radius=13)
        pygame.draw.rect(self.canvas, "#F4FAF1", (x, y, 362, 134), border_radius=13)
        pygame.draw.rect(self.canvas, scene["accent"], (x, y, 362, 134), 2, border_radius=13)
        self.text("NEW DISCOVERY!", x + 19, y + 13, 12, scene["accent"], bold=True)
        self.text(scene["title"], x + 18, y + 34, 27, INK, serif=True)
        self.text("Added to your field guide.", x + 20, y + 76, 13, MUTED)
        self.text(f"{len(self.discovery_queue)} more discoveries waiting" if self.discovery_queue else
                  "Your sound recipe made this happen.", x + 20, y + 104, 11, MUTED)
        self.button(("discovery_view", 0), (x + 233, y + 87, 110, 31), "View card")
        self.buttons[("discovery_close", 0)] = pygame.Rect(x + 328, y + 9, 25, 25)
        self.text("x", x + 340, y + 19, 16, MUTED, center=True)
        remaining = max(0, 1 - elapsed / 4.5)
        pygame.draw.rect(self.canvas, scene["accent"], (x + 19, y + 127, round(324 * remaining), 3),
                         border_radius=1)

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
        self.text("Sound garden.", 32, 15, 44, serif=True)
        self.text("Tune a little world. Keep what you discover.", 36, 73, 15, MUTED)
        self.text("STARTER SEEDS", 654, 20, 10, MUTED, bold=True)
        for index, name in enumerate(PRESETS):
            self.button(("preset", name), (654 + index * 200, 43, 192, 34), name,
                        active=self.preset_name == name)
        phase = now - (getattr(self, "play_origin", self.visual_origin)
                       if self.playing else self.visual_origin)
        self.panel((34, 98, 790, 312), "#173B30", radius=18)
        draw_garden(self.canvas, (34, 98, 790, 312), self.mix, phase, self.playing)
        pygame.draw.rect(self.canvas, "#52776A", (34, 98, 790, 312), 1, border_radius=18)
        scene = next((item for item in SCENES if item["id"] == scene_for(self.mix)), None)
        self.text("YOUR LIVING GARDEN", 56, 115, 10, "#D7E7D8", bold=True)
        self.text(scene["title"] if scene else "A wild little world", 55, 133, 25, "#F3F0DC", serif=True)
        self.text("LISTENING" if self.playing else "SILENT VISUAL PREVIEW / PRESS PLAY TO LISTEN",
                  56, 383, 10, "#D7E7D8")
        self.button(("keep", 0), (637, 357, 165, 36), "Keep garden", primary=True)
        self.draw_visitor()
        for index in range(3):
            self.draw_ingredient(index, now)
        self.draw_collection()
        pygame.draw.line(self.canvas, LINE, (34, 786), (1246, 786))
        self.button(("play", 0), (34, 799, 180, 43),
                    "Stop listening" if self.playing else "Play your mix", primary=True)
        self.button(("reset", 0), (225, 799, 94, 43), "Reset")
        self.text("MASTER", 399, 795, 10, MUTED, bold=True)
        self.text(f"{round(self.mix.master * 100)}%", 583, 794, 12, INK)
        self.draw_slider(("master", 0), INK)
        pending = self.ready_revision != self.revision
        self.button(("save", 0), (659, 799, 210, 43), "Save 8-second WAV", disabled=pending)
        self.button(("folder", 0), (880, 799, 156, 43), "Open exports", disabled=self.last_saved is None)
        status = "UPDATING AUDIO" if pending else "PLAYING / 4s LOOP" if self.playing else "READY / STOPPED"
        if not self.audio.available:
            status = "NO AUDIO DEVICE"
        self.text(status, 1060, 797, 10, MUTED, bold=True)
        pygame.draw.line(self.canvas, LINE, (1060, 829), (1244, 829))
        if self.waveform:
            points = [(1060 + i * 184 / (len(self.waveform) - 1), 829 - sample * 78)
                      for i, sample in enumerate(self.waveform)]
            pygame.draw.lines(self.canvas, COLORS[0], False, points, 1)
        self.wrapped_text(self.message, 35, 850, 1205, 14, line_height=18)
        self.text("SPACE play / stop    ESC stop    R reset sounds    S export WAV", 35, 885, 10, MUTED)
        self.text("LOCAL SYNTHESIS / NO RECORDING", 1050, 885, 9, MUTED)
        self.draw_discovery(now)
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

