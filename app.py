# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["pygame==2.6.1"]
# ///
"""Sound Alchemy: turn three synthetic ingredients into a small listening scene."""

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

HERE = Path(__file__).resolve().parent
SIZE = (1180, 860)
PAPER = "#F5F2EB"
INK = "#243B36"
MUTED = "#6F7972"
LINE = "#D5D9CF"
COLORS = ("#397D7B", "#B35C40", "#87669A")
TINTS = ("#E9F0EB", "#F6E9DD", "#EEE8F1")
NAMES = ("Rain", "Bass", "Bells")
DESCRIPTIONS = ("A soft bed of falling grains.", "A warm pulse to hold it together.",
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
        pygame.display.set_caption("Sound Alchemy | a small listening lab")
        self.canvas = pygame.Surface(SIZE)
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
        self.running = True
        self.preset_name = "Rainy window"
        self.dragging = None
        self.last_edit = 0
        self.last_export = -10
        self.output = Path(output)
        self.last_saved = None
        self.message = "Choose a place, then press Play. Make it yours with the sliders."
        if not self.audio.available:
            self.message = "No audio device yet. You can still mix and save; Play retries the connection."
        self.buttons = {}
        self.sliders = []
        for index in range(3):
            x = 50 + index * 368
            self.sliders.append((("level", index), pygame.Rect(x + 24, 447, 296, 18)))
            self.sliders.append((("character", index), pygame.Rect(x + 24, 511, 296, 18)))
        self.sliders.append((("master", 0), pygame.Rect(536, 769, 296, 18)))
        self.update()
        self.draw()

    def changed(self, message):
        self.revision += 1
        self.last_edit = time.monotonic()
        self.message = message
        if self.playing and not self.mix.audible():
            self.stop("Your mix is silent. Raise a level or switch an ingredient on, then press Play.")
        elif self.playing and not self.audio.set_levels(self.mix):
            self.stop("Audio was interrupted. Check your output device and press Play to retry.")
        if self.layer_character == tuple(self.mix.character):
            self.refresh_mix()

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
        self.changed("Reset to Rainy window. Press Play when you are ready.")

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
        self.message = "Saved 8 seconds + recipe. Open saved folder to listen or share."

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

    def move_slider(self, key, point):
        rect = next(rect for item, rect in self.sliders if item == key)
        value = max(0, min(1, (point[0] - rect.left) / rect.width))
        if abs(self.slider_value(key) - value) < 0.001:
            return
        kind, index = key
        if kind == "master":
            self.mix.master = value
            message = f"Master volume: {round(value * 100)}%."
        elif kind == "level":
            self.mix.levels[index] = value
            self.preset_name = None
            message = f"{NAMES[index]} level: {round(value * 100)}%."
        else:
            self.mix.character[index] = value
            self.preset_name = None
            message = ("Rain density changed.", "Bass pitch changed; the bells follow its key.",
                       "Bell pattern changed.")[index]
        self.changed(message)

    def event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.WINDOWFOCUSLOST:
            self.dragging = None
            if self.playing:
                self.stop("Stopped while you were away. Press Play to return to your mix.")
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
        rendered = self.font(size, serif, bold).render(text, True, color)
        rect = rendered.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        self.canvas.blit(rendered, rect)

    def button(self, key, rect, label, active=False, primary=False, disabled=False):
        rect = pygame.Rect(rect)
        if not disabled:
            self.buttons[key] = rect
        color = LINE if disabled else INK
        fill = color if primary or active else PAPER
        pygame.draw.rect(self.canvas, fill, rect, border_radius=9)
        pygame.draw.rect(self.canvas, color, rect, 1, border_radius=9)
        self.text(label, rect.centerx, rect.centery - 1, 16,
                  PAPER if primary or active else color, center=True, bold=primary)

    def draw_slider(self, key, color):
        rect = next(rect for item, rect in self.sliders if item == key)
        x = round(rect.left + rect.width * self.slider_value(key))
        pygame.draw.line(self.canvas, "#CDD1C8", (rect.left, rect.centery),
                         (rect.right, rect.centery), 4)
        if x > rect.left:
            pygame.draw.line(self.canvas, color, (rect.left, rect.centery), (x, rect.centery), 4)
        pygame.draw.circle(self.canvas, PAPER, (x, rect.centery), 10)
        pygame.draw.circle(self.canvas, color, (x, rect.centery), 10, 2)
        pygame.draw.circle(self.canvas, color, (x, rect.centery), 3)

    def draw_ingredient(self, index, now):
        x = 50 + index * 368
        on = self.mix.enabled[index]
        color = COLORS[index] if on else MUTED
        pygame.draw.rect(self.canvas, TINTS[index] if on else "#ECEDE7",
                         (x, 252, 344, 306), border_radius=16)
        pygame.draw.rect(self.canvas, LINE, (x, 252, 344, 306), 1, border_radius=16)
        self.text(f"0{index + 1} / INGREDIENT", x + 24, 273, 12, color, bold=True)
        toggle = pygame.Rect(x + 263, 270, 57, 28)
        self.buttons[("toggle", index)] = toggle
        pygame.draw.rect(self.canvas, color if on else "#D3D6CD", toggle, border_radius=14)
        self.text("ON" if on else "OFF", toggle.centerx, toggle.centery - 1, 12,
                  PAPER if on else INK, center=True, bold=True)
        self.text(NAMES[index], x + 23, 302, 35, INK, serif=True)
        self.text(DESCRIPTIONS[index], x + 24, 349, 14, MUTED)
        # Small ingredient sketches are schematic. The large waveform below is measured data.
        phase = now if self.playing and on else 0
        if index == 0:
            for n in range(17):
                px = x + 30 + (n * 47) % 280
                py = 380 + ((n * 11 + phase * 17) % 29)
                pygame.draw.line(self.canvas, color, (px, py), (px - 3, py + 5), 2)
        elif index == 1:
            points = [(x + 24 + n * 3, 393 + math.sin(n * 0.13 + phase * 2) * 10)
                      for n in range(99)]
            pygame.draw.lines(self.canvas, color, False, points, 2)
        else:
            for n in range(8):
                px = x + 39 + n * 38
                py = 393 + math.sin(n * 1.9) * 7
                radius = 3 + round(2 * (0.5 + 0.5 * math.sin(phase * 2 + n)))
                pygame.draw.polygon(self.canvas, color,
                                    [(px, py - radius), (px + radius, py),
                                     (px, py + radius), (px - radius, py)])
        self.text("LEVEL", x + 24, 423, 12, MUTED, bold=True)
        self.text(f"{round(self.mix.levels[index] * 100)}%", x + 280, 420, 15, color)
        self.draw_slider(("level", index), color)
        self.text("Quiet", x + 24, 467, 11, MUTED)
        self.text("Loud", x + 320 - self.font(11).size("Loud")[0], 467, 11, MUTED)
        label = ("DROPS", "PITCH", "SPARKLE")[index]
        value = self.mix.character[index]
        if index == 0:
            reading = f"{12 + round(value * 80)} / loop"
        elif index == 1:
            reading = NOTE_NAMES[round(value * 6)]
        else:
            reading = f"{2 + round(value * 6)} / loop"
        self.text(label, x + 24, 487, 12, MUTED, bold=True)
        self.text(reading, x + 320 - self.font(15).size(reading)[0], 484, 15, color)
        self.draw_slider(("character", index), color)
        left, right = (("Sparse rain", "Dense rain"), ("Lower", "Higher"),
                       ("Fewer notes", "More notes"))[index]
        self.text(left, x + 24, 535, 11, MUTED)
        self.text(right, x + 320 - self.font(11).size(right)[0], 535, 11, MUTED)

    def draw(self):
        now = time.monotonic()
        self.canvas.fill(PAPER)
        self.buttons = {}
        for n, height in enumerate((9, 21, 15, 27)):
            pygame.draw.rect(self.canvas, INK, (50 + n * 7, 49 - height, 3, height), border_radius=1)
        self.text("SOUND ALCHEMY", 91, 27, 15, bold=True)
        self.text("A SMALL LISTENING LAB", 900, 30, 12, MUTED)
        pygame.draw.line(self.canvas, LINE, (50, 64), (1130, 64))
        self.text("Sound alchemy.", 47, 81, 60, serif=True)
        self.text("Three ingredients. One place of your own.", 51, 158, 18, MUTED)
        self.text("01  LISTEN", 927, 96, 14, MUTED)
        self.text("02  CHANGE ONE THING", 927, 123, 14, MUTED)
        self.text("03  MAKE IT YOURS", 927, 150, 14, MUTED)
        self.text("START WITH A PLACE", 51, 206, 12, MUTED, bold=True)
        for n, name in enumerate(PRESETS):
            self.button(("preset", name), (247 + n * 190, 195, 176, 36), name,
                        active=self.preset_name == name)
        for n in range(3):
            self.draw_ingredient(n, now)
        pygame.draw.rect(self.canvas, "#E8EBE2", (50, 580, 1080, 140), border_radius=15)
        self.text("YOUR MIX", 74, 599, 12, MUTED, bold=True)
        pending = self.ready_revision != self.revision
        status = "UPDATING" if pending else "PLAYING" if self.playing else "READY / STOPPED"
        if not self.audio.available:
            status = "PREVIEW / NO AUDIO DEVICE"
        self.text(status, 74, 621, 12, INK, bold=True)
        self.text("ONE LOOP / 4 SECONDS", 939, 600, 12, MUTED)
        pygame.draw.line(self.canvas, "#C8D0C3", (75, 672), (1106, 672))
        if self.waveform:
            points = [(75 + i * 1030 / (len(self.waveform) - 1),
                       672 - sample * 175) for i, sample in enumerate(self.waveform)]
            pygame.draw.lines(self.canvas, COLORS[0], False, points, 2)
            if self.playing and not pending:
                position = ((now - getattr(self, "play_origin", now)) % SECONDS) / SECONDS
                x = round(75 + position * 1030)
                pygame.draw.line(self.canvas, "#B35C40", (x, 651), (x, 704), 1)
        elif pending:
            self.text("Preparing your first mix...", 440, 661, 15, MUTED)
        self.button(("play", 0), (50, 742, 190, 48),
                    "Stop listening" if self.playing else "Play your mix", primary=True)
        self.button(("reset", 0), (253, 742, 100, 48), "Reset")
        self.text("MASTER", 536, 741, 12, MUTED, bold=True)
        self.text(f"{round(self.mix.master * 100)}%", 793, 738, 15, INK)
        self.draw_slider(("master", 0), INK)
        self.button(("save", 0), (906, 742, 224, 48), "Save 8-second WAV",
                    disabled=pending)
        self.button(("folder", 0), (906, 799, 224, 29), "Open saved folder",
                    disabled=self.last_saved is None)
        self.text(self.message, 51, 810, 15, INK)
        self.text("SPACE  play / stop     ESC  stop     R  reset     S  save", 51, 838, 11, MUTED)
        self.text("SYNTHESIZED LOCALLY / NO RECORDING", 875, 838, 10, MUTED)
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

