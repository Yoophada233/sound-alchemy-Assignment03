"""A small living landscape drawn directly from the three sound controls."""

import math
from functools import lru_cache

import pygame

from garden import scene_for
from sound import SAMPLE_RATE, SECONDS, bass_pulse, bell_pattern
from raster import draw, density, make_surface, point as pixel_point, rect as pixel_rect
from artwork import landscape, paint_sprite


WIDTH = 748
HEIGHT = 310
FLOWER_HEADS = ((142, 198), (294, 190), (446, 198), (598, 190))


def bell_envelope(seconds, sparkle, flower_index, flower_count, active=True,
                  flower_steps=None):
    """Let the flower assigned to each real bell follow its attack and decay.

    The modulo also includes a note still ringing from the previous loop. A
    stopped or muted layer has no audio-triggered light, even in visual preview.
    """
    if not active or flower_count <= 0:
        return 0.0
    strength = 0.0
    for index, (onset, _) in enumerate(bell_pattern(sparkle, flower_steps)):
        assigned = index % flower_count if flower_steps is None else onset // SAMPLE_RATE
        if assigned != flower_index:
            continue
        age = (seconds - onset / SAMPLE_RATE) % SECONDS
        if age < round(0.70 * SAMPLE_RATE) / SAMPLE_RATE:
            strength += min(1, age / 0.006) * math.exp(-age * (7 - 2 * sparkle))
    return min(1, strength)


def rhythm_levels(mix, playing):
    """Keep growth independent from master, but silence the sound-led gestures."""
    if not playing or mix.master <= 0:
        return 0.0, 0.0
    return tuple(mix.levels[index] * mix.master if mix.enabled[index] else 0.0
                 for index in (1, 2))


def blend(first, second, amount):
    amount = max(0, min(1, amount))
    return tuple(round(a + (b - a) * amount) for a, b in zip(first, second))


def curve(start, middle, end, steps=12):
    points = []
    for index in range(steps + 1):
        t = index / steps
        points.append(((1 - t) ** 2 * start[0] + 2 * (1 - t) * t * middle[0] + t ** 2 * end[0],
                       (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * middle[1] + t ** 2 * end[1]))
    return points


def glow(surface, position, color, radius, strength=1):
    """Soft nested light, with no hard outer halo or persistent particles."""
    x, y = position
    for step in range(10, 0, -1):
        fraction = step / 10
        alpha = 26 * (1 - fraction) ** 2
        draw.circle(surface, (*color, round(alpha * strength)),
                           (round(x), round(y)), max(1, round(radius * fraction)))


def fern(surface, x, y, height, lean, color, wet):
    area = pixel_rect(surface, (x + lean - height * .38, y - height, height * .76, height))
    if paint_sprite(surface, area, "accents", 3, dim=height < 18):
        return
    tip = (x + lean, y - height)
    draw.lines(surface, color, False,
                      curve((x, y), (x + lean * 0.15, y - height * 0.62), tip), 2)
    for index in range(1, 6):
        t = index / 7
        stem_x = x + lean * t * t
        stem_y = y - height * t
        length = height * (0.25 - t * 0.13)
        for side in (-1, 1):
            leaf_tip = (stem_x + side * length, stem_y - length * 0.52)
            draw.lines(surface, color, False,
                              curve((stem_x, stem_y),
                                    (stem_x + side * length * 0.78, stem_y - length * 0.08),
                                    leaf_tip, 5), 2)
    if wet > 0.6:
        draw.circle(surface, (159, 208, 183), (round(tip[0]), round(tip[1] + 3)), 1)


def flower(surface, lights, x, y, height, sway, openness, color, phase, brightness=0):
    head = (x + sway, y - height)
    stem = curve((x, y), (x + sway * .05, y - height * .55), head)
    draw.lines(surface, (95, 102, 66), False, stem, 2)
    draw.lines(surface, (175, 153, 95), False, stem, .7)
    for side, fraction in ((-1, .30), (1, .48)):
        sx, sy = x + sway * fraction, y - height * fraction
        leaf = [(sx, sy), (sx + side * 6, sy - 10),
                (sx + side * 14, sy - 13), (sx + side * 11, sy - 3)]
        draw.polygon(surface, (53, 93, 75), leaf)
        draw.lines(surface, (124, 150, 110), False, leaf, .65)
    width = 57 + openness * 7
    area = pixel_rect(surface, (head[0] - width / 2, head[1] - 23, width, 42))
    if paint_sprite(surface, area, "flowers", 0, dim=color[0] < 160):
        glow(lights, head, (255, 214, 124), 24 + brightness * 18,
             .16 + brightness * 2.3)
        return
    draw.lines(surface, (87, 151, 126), False,
                      curve((x, y), (x + sway * 0.05, y - height * 0.55), head), 2)
    for side, fraction in ((-1, 0.32), (1, 0.52)):
        stem_x = x + sway * fraction * fraction
        stem_y = y - height * fraction
        draw.polygon(surface, (73, 137, 114),
                            [(stem_x, stem_y), (stem_x + side * 12, stem_y - 9),
                             (stem_x + side * 9, stem_y - 1)])
    radius = 3 + openness * 4
    glow(lights, head, color, 13 + openness * 9 + brightness * 15,
         0.12 + openness * 0.12 + brightness * 1.7)
    color = blend(color, (255, 245, 193), min(1, brightness * 0.85))
    for petal in range(5):
        angle = petal * math.tau / 5 - math.pi / 2 + math.sin(phase) * 0.04
        center = (round(head[0] + math.cos(angle) * radius * 0.7),
                  round(head[1] + math.sin(angle) * radius * 0.7))
        draw.circle(surface, color, center, max(2, round(radius * 0.57)))
    draw.circle(surface, (255, 237, 176), (round(head[0]), round(head[1])), 2)


def storm_clouds(surface, now):
    """Slow layered storm clouds leave a few narrow openings in the sky."""
    for layer in range(2):
        color = (25, 45, 54) if layer == 0 else (33, 55, 64)
        for index in range(9):
            x = index * 98 - 45 + math.sin(now * 0.12 + layer) * 8
            y = 28 + layer * 33 + 12 * math.sin(index * 1.6)
            draw.ellipse(surface, color, (x, y - 29, 149, 62))
        draw.polygon(surface, color,
                            [(0, 0), (WIDTH, 0), (WIDTH, 27 + layer * 15),
                             (0, 29 + layer * 17)])
    for index in range(5):
        x = 81 + index * 147
        draw.arc(surface, (51, 73, 82), (x, 29 + index % 2 * 17, 91, 30),
                        0.2, 2.4, 1)


def crystal_clusters(surface, lights, now):
    """Faceted, blue crystal groups grow out of reflective rain-fed pools."""
    for cluster, x in enumerate((94, 222, 370, 514, 652)):
        y = 260 + 9 * math.sin(cluster * 1.8)
        if paint_sprite(surface, pixel_rect(surface, (x - 26, y - 52, 52, 55)), "accents", 0):
            glow(lights, (x, y - 20), (124, 201, 237), 27,
                 .6 + .3 * math.sin(now * 1.5 + cluster))
            continue
        draw.ellipse(surface, (47, 100, 117), (x - 34, y - 2, 72, 11))
        draw.arc(surface, (120, 179, 190), (x - 30, y - 1, 66, 8), 0.05, 2.7, 1)
        for stem, (offset, height) in enumerate(((-14, 29), (0, 58), (16, 38))):
            height += ((cluster * 7 + stem * 5) % 17)
            base = x + offset
            tip = (base + (stem - 1) * 3, y - height)
            left = (base - 8, y - height + 16)
            right = (base + 9, y - height + 17)
            bottom = (base + 4, y)
            draw.polygon(surface, (104, 170, 184), [tip, left, (base - 6, y), bottom, right])
            draw.polygon(surface, (55, 116, 145), [tip, right, bottom])
            draw.polygon(surface, (160, 211, 213), [tip, left, (base, y - height + 24)])
            draw.line(surface, (190, 231, 227), tip, left, 1)
            draw.line(surface, (128, 197, 211), tip, bottom, 1)
            glow(lights, tip, (130, 216, 238), 24,
                 0.7 + 0.2 * math.sin(now * 1.5 + cluster + stem))
        draw.line(surface, (76, 137, 156), (x - 18, y + 13), (x + 22, y + 13), 1)


def star_canopy(surface, lights, now):
    """Two overhead branches hold constellations across a cool night sky."""
    for side in (-1, 1):
        start_x = 0 if side == 1 else WIDTH
        if paint_sprite(surface, pixel_rect(surface, (0 if side == 1 else WIDTH - 160, 6, 160, 110)),
                        "accents", 2, dim=True):
            continue
        branch = curve((start_x, 143), (start_x + side * 72, 12),
                       (start_x + side * 263, 19), 24)
        draw.lines(surface, (59, 97, 94), False, branch, 4)
        for index in range(1, 6):
            point = branch[index * 3]
            tip = (point[0] + side * 19, point[1] - 15)
            draw.line(surface, (83, 120, 108), point, tip, 2)
            draw.ellipse(surface, (74, 114, 101), (tip[0] - 6, tip[1] - 5, 12, 6))
    constellations = (((101, 98), (157, 63), (219, 86), (268, 48)),
                      ((317, 112), (373, 75), (421, 92), (462, 55), (507, 101)),
                      ((550, 128), (593, 94), (652, 114), (691, 74)))
    for number, points in enumerate(constellations):
        draw.lines(surface, (102, 143, 161), False, points, 1)
        for index, (x, y) in enumerate(points):
            shimmer = 0.65 + 0.3 * math.sin(now * 1.3 + index + number * 2)
            glow(lights, (x, y), (171, 204, 242), 17, shimmer)
            color = blend((141, 184, 205), (236, 239, 225), shimmer)
            draw.line(surface, color, (x - 3, y), (x + 3, y), 1)
            draw.line(surface, color, (x, y - 3), (x, y + 3), 1)
            draw.circle(surface, (229, 238, 225), (x, y), 1)


def amber_reeds(surface, lights, now, bass):
    """Tall oat-like heads give the warm, high-pitch garden its own silhouette."""
    if paint_sprite(surface, pixel_rect(surface, (15, 197, 65, 91)), "accents", 1):
        for index, x in enumerate((195, 365, 535, 690)):
            lean = math.sin(now * math.tau + index) * bass * 2
            height = 73 + index % 3 * 11
            paint_sprite(surface, pixel_rect(surface, (x - 27 + lean, 281 - height, 55, height)),
                         "accents", 1)
            glow(lights, (x, 281 - height), (233, 189, 116), 18, .3)
        return
    for index in range(16):
        x = 18 + (index * 89) % 715
        y = 259 + index % 3 * 12
        height = 75 + (index * 17) % 61
        lean = math.sin(now * math.tau + index * 0.9) * bass * 9
        tip = (x + lean, y - height)
        draw.lines(surface, (167, 151, 86), False,
                          curve((x, y), (x + lean * 0.2, y - height * 0.6), tip, 14), 2)
        for side, fraction in ((-1, 0.3), (1, 0.48)):
            start = (x + lean * fraction * fraction, y - height * fraction)
            draw.lines(surface, (128, 139, 77), False,
                              curve(start, (start[0] + side * 14, start[1] - 9),
                                    (start[0] + side * 21, start[1] - 27), 7), 2)
        for grain in range(5):
            stem_y = tip[1] + grain * 5
            stem_x = tip[0] - lean * grain * 0.025
            spread = 3 + math.sin((grain + 1) / 6 * math.pi) * 4
            color = (221, 187, 112) if grain % 2 else (236, 205, 133)
            draw.line(surface, color, (stem_x, stem_y),
                             (stem_x - spread, stem_y - 5), 3)
            draw.line(surface, color, (stem_x, stem_y + 2),
                             (stem_x + spread, stem_y - 3), 3)
        if index % 4 == 0:
            glow(lights, tip, (239, 196, 117), 23, 0.6)


def stage_geometry(rect):
    """Share the exact padded-world dimensions with drawing and hit testing."""
    rect = pygame.Rect(rect)
    scale = min(rect.width / WIDTH, rect.height / HEIGHT)
    world_width = max(WIDTH, round(rect.width / scale))
    world_height = max(HEIGHT, round(rect.height / scale))
    return world_width, world_height, (world_width - WIDTH) // 2, (world_height - HEIGHT) // 2


def flower_targets(rect, mix, now=0):
    """Return four generous, stable flower targets in window coordinates.

    Mix and time are accepted alongside the renderer's API, but plant sway,
    volume and recipe changes never move these four instrument controls.
    """
    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return ()
    width, height, left, top = stage_geometry(rect)
    scale_x, scale_y = rect.width / width, rect.height / height
    targets = []
    for x, y in FLOWER_HEADS:
        x0 = rect.left + round((left + x - 34) * scale_x)
        y0 = rect.top + round((top + y - 29) * scale_y)
        x1 = rect.left + round((left + x + 34) * scale_x)
        y1 = rect.top + round((top + y + 62) * scale_y)
        targets.append(pygame.Rect(x0, y0, x1 - x0, y1 - y0))
    return tuple(targets)


@lru_cache(maxsize=2)
def garden_buffers(ratio):
    # Use a true RGB surface: disabling alpha on an RGBA surface can copy zero
    # alpha bits into the transparent stage and hide otherwise opaque scenery.
    canvas = make_surface((WIDTH, HEIGHT), ratio=ratio)
    lights = make_surface((WIDTH, HEIGHT), pygame.SRCALPHA, ratio)
    return canvas, lights


@lru_cache(maxsize=2)
def stage_buffers(world_width, world_height, ratio):
    stage = make_surface((world_width, world_height), pygame.SRCALPHA, ratio)
    mask = pygame.Surface(stage.get_size(), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(),
                     border_radius=max(1, round(17 * ratio)))
    return stage, mask


def place_stage(surface, rect, canvas, frame=True, backdrop=None):
    """Fit the cut-paper world without stretching its flowers or crescent moon.

    A wider window reveals quiet foreground branches at the edges. Those dark
    silhouettes connect the miniature to its frame instead of adding black bars.
    """
    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return
    world_width, world_height, left, top = stage_geometry(rect)
    ratio = density(canvas)
    stage, mask = stage_buffers(world_width, world_height, ratio)
    stage.fill((0, 0, 0, 0))
    if backdrop is not None:
        stage.blit(backdrop, (0, 0))
    def edge(area, size, position):
        target = tuple(max(1, round(value * ratio)) for value in size)
        strip = canvas.subsurface(pixel_rect(canvas, area))
        stage.blit(pygame.transform.scale(strip, target), pixel_point(stage, position))

    if frame and backdrop is None:
        if world_width > WIDTH:
            if left:
                edge((0, 0, 1, HEIGHT), (left, HEIGHT), (0, top))
            right = world_width - WIDTH - left
            if right:
                edge((WIDTH - 1, 0, 1, HEIGHT), (right, HEIGHT), (left + WIDTH, top))
        if world_height > HEIGHT:
            if top:
                edge((0, 0, WIDTH, 1), (world_width, top), (0, 0))
            bottom = world_height - HEIGHT - top
            if bottom:
                edge((0, HEIGHT - 1, WIDTH, 1), (world_width, bottom), (0, top + HEIGHT))
    stage.blit(canvas, pixel_point(stage, (left, top)))
    if frame and backdrop is None:
        for side in (1, -1):
            edge = 5 if side == 1 else world_width - 5
            stem = curve((edge, world_height + 8),
                         (edge + side * 9, world_height * 0.44),
                         (edge + side * 25, 9), 18)
            draw.lines(stage, (17, 43, 36), False, stem, 5)
            for index in range(1, 7):
                point = stem[index * 2]
                reach = 19 + (index * 7) % 17
                for direction, lift in ((side, 14), (-side, 9)):
                    tip = (point[0] + direction * reach, point[1] - lift - reach * 0.4)
                    draw.polygon(stage, (21, 48, 39),
                                        [point, (point[0] + direction * reach * 0.7,
                                                 point[1] - 2), tip,
                                         (point[0] + direction * reach * 0.35,
                                          point[1] - lift)])
            draw.line(stage, (38, 67, 54), (edge, 12),
                             (edge, world_height - 7), 1)
    stage.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    if stage.get_size() != rect.size:
        stage = pygame.transform.smoothscale(stage, rect.size)
    surface.blit(stage, rect.topleft)


def beat_number(surface, center, number, selected, focused=False):
    """Contrasting seed buttons make the four plants read as an instrument."""
    x, y = center
    edge = (246, 225, 167) if focused else (163, 142, 91)
    fill = (223, 196, 131) if selected else (17, 37, 42)
    ink = (33, 39, 35) if selected else (230, 223, 199)
    draw.circle(surface, (6, 16, 23), (x, y + 2), 13)
    draw.circle(surface, fill, (x, y), 11)
    draw.circle(surface, edge, (x, y), 11, 1)
    if focused:
        draw.circle(surface, edge, (x, y), 14, 1)
    image = number_image(number, max(1, round(22 * density(surface))), ink)
    surface.blit(image, image.get_rect(center=pixel_point(surface, (x, y))))


@lru_cache(maxsize=48)
def number_image(number, size, color):
    if not pygame.font.get_init():
        pygame.font.init()
    return pygame.font.Font(None, size).render(str(number), True, color)


def firefly_position(seconds):
    """Reach each numbered plant exactly at its one-second audio onset."""
    slot = int(seconds % SECONDS)
    fraction = seconds % 1
    start, end = FLOWER_HEADS[slot], FLOWER_HEADS[(slot + 1) % 4]
    ease = fraction * fraction * (3 - 2 * fraction)
    x = start[0] + (end[0] - start[0]) * ease
    y = start[1] + (end[1] - start[1]) * ease - 20 - 15 * math.sin(fraction * math.pi)
    return x, y


def melody_flowers(surface, lights, mix, rhythm_mix, now, playing, hover, listening_focus=None):
    """Four grounded plants form the little sequencer, including silent rests."""
    steps = mix.flower_steps
    audible_steps = rhythm_mix.flower_steps
    _, gain = rhythm_levels(mix, playing and listening_focus in (None, 2))
    sparkle = rhythm_mix.character[2]
    volume = mix.levels[2] if mix.enabled[2] else 0
    colors = ((221, 219, 153), (225, 188, 144), (197, 215, 171), (216, 191, 195))
    for index, ((x, y), selected, color) in enumerate(zip(FLOWER_HEADS, steps, colors)):
        focused = hover == index
        beat = bell_envelope(now, sparkle, index, 4,
                             active=playing and gain > 0, flower_steps=audible_steps)
        beat *= math.sqrt(gain)
        if volume <= 0:
            color = blend((86, 122, 101), color, 0.35)
        if focused:
            draw.circle(surface, (183, 185, 137), (x, y), 23, 1)
            for side in (-1, 1):
                draw.line(surface, (199, 205, 156),
                                 (x + side * 28, y - 2), (x + side * 28, y + 2), 1)
        if selected:
            openness = 0.42 + volume * 0.18 + beat * 0.45
            flower(surface, lights, x, 256, 256 - y, 0, openness,
                   color, index * 1.7, beat)
        else:
            # A closed bud is still an obvious, reachable instrument control.
            draw.lines(surface, (70, 116, 94), False,
                              curve((x, 256), (x - 3, y + 24), (x, y)), 2)
            draw.polygon(surface, (67, 112, 89),
                                [(x, y + 29), (x - 12, y + 20), (x - 8, y + 28)])
            if not paint_sprite(surface, pixel_rect(surface, (x - 8, y - 15, 16, 30)),
                                "flowers", 1, dim=volume <= 0):
                draw.ellipse(surface, (100, 137, 103), (x - 5, y - 7, 10, 14))
                draw.line(surface, (148, 164, 118), (x, y - 5), (x + 1, y + 4), 1)
            if beat:
                # Pending synthesis can still contain this newly removed note.
                glow(lights, (x, y), color, 29, beat * 1.7)
        beat_number(surface, (x, y + 28), index + 1, selected, focused)

    if playing:
        # A whole orbit takes one audio loop; rests keep their place in time.
        x, y = firefly_position(now)
        active = gain > 0 and any(audible_steps)
        color = (241, 235, 173) if active else (117, 150, 128)
        if active:
            glow(lights, (x, y), color, 15, 1)
        draw.ellipse(surface, (116, 155, 130), (x - 6, y - 3, 5, 3))
        draw.ellipse(surface, (116, 155, 130), (x + 2, y - 3, 5, 3))
        draw.circle(surface, color, (round(x), round(y)), 3)


def draw_garden(surface, rect, mix, now, playing=False, rhythm_mix=None,
                flower_hover=None, listening_focus=None):
    """Paint a quiet world, then draw its live musical responses over the art."""
    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return
    world_width, world_height, left, top = stage_geometry(rect)
    ratio = min(rect.width / world_width, rect.height / world_height)
    canvas, lights = garden_buffers(ratio)
    scene = scene_for(mix)
    plate = landscape((round(world_width * ratio), round(world_height * ratio)), scene)
    if plate is None:
        _draw_procedural_garden(surface, rect, mix, now, playing, rhythm_mix,
                               flower_hover, listening_focus)
        return
    canvas.blit(plate, pixel_point(canvas, (-left, -top)))
    lights.fill((0, 0, 0, 0))
    rain, bass, bells = [level if on else 0 for level, on in zip(mix.levels, mix.enabled)]
    if not any(mix.flower_steps):
        bells = 0
    drops, pitch, sparkle = mix.character
    rhythm_mix = mix if rhythm_mix is None else rhythm_mix
    bass_gain, _ = rhythm_levels(mix, playing and listening_focus in (None, 1))
    pulse = bass_gain * bass_pulse(now)

    # A separate crescent is crisp at every density. Its cut-out is transparent,
    # so the mountain painting shows through without a mismatched sky-colour disc.
    moon = make_surface((52, 52), pygame.SRCALPHA, ratio)
    draw.circle(moon, (237, 222, 170), (25, 27), 14)
    draw.circle(moon, (0, 0, 0, 0), (31, 22), 13)
    canvas.blit(moon, pixel_point(canvas, (492, 22)))
    glow(lights, (517, 49), (231, 217, 176), 25, .3)

    # Rain adds water and moss; low notes illuminate roots along the near shore.
    for index in range(12):
        x = 20 + index * 64
        y = 289 + 3 * math.sin(index * 2.1)
        if rain > .05:
            color = blend((26, 48, 40), (94, 126, 75), rain * .7)
            fern(canvas, x, y, 6 + rain * 10, 2, color, 0)
        if bass > .025:
            reach = 9 + 17 * bass
            root = curve((x, y - 8), (x + 12, y), (x - 6, y + reach / 2))
            color = blend((41, 55, 51), (190, 167, 107), bass * .4 + pulse * .6)
            draw.lines(canvas, color, False, root, .8)
            for side in (-1, 1):
                draw.lines(canvas, color, False,
                           curve((x + 3, y), (x + side * 8, y + 3),
                                 (x + side * 14, y + 5), 5), .6)
            glow(lights, (x, y), (207, 170, 106), 13, pulse * 1.6)
    for index, x in enumerate((70, 233, 370, 516, 676)):
        height = 8 + rain * 9 + bass * (10 + pitch * 27)
        fern(canvas, x, 288 + index % 2 * 4, height,
             math.sin(now * .7 + index) * bass * 2,
             blend((31, 66, 58), (120, 152, 100), max(rain, bass) * .6), rain)

    if scene == "storm-roots":
        storm_clouds(canvas, now)
    elif scene == "starlit-canopy":
        star_canopy(canvas, lights, now)
    elif scene == "crystal-rain":
        crystal_clusters(canvas, lights, now)
    elif scene == "amber-reeds":
        amber_reeds(canvas, lights, now, bass)
    elif scene == "dawn-chorus":
        glow(lights, (520, 152), (245, 169, 114), 120, 1.5)

    for index in range(round(bells * (5 + sparkle * 16))):
        x = 40 + (index * 97) % 669 + 5 * math.sin(now * .6 + index)
        y = 148 + (index * 31) % 83 + 4 * math.sin(now * .7 + index * 2)
        strength = .5 + .5 * math.sin(now * 1.8 + index)
        glow(lights, (x, y), (245, 210, 128), 12, strength * bells * 1.8)
        draw.circle(canvas, blend((91, 112, 95), (248, 220, 153), strength), (x, y), .8)
    melody_flowers(canvas, lights, mix, rhythm_mix, now, playing, flower_hover, listening_focus)
    # Composite light and precipitation together; one native-size alpha pass.
    for index in range(round(rain * (24 + drops * 72))):
        depth = .4 + (index % 5) * .14
        x = (index * 79.37 + 17) % WIDTH
        y = (index * 47.91 + now * (62 + depth * 105)) % (HEIGHT + 25) - 12
        length = 3 + drops * 4 + rain * depth * 4
        draw.line(lights, (167, 201, 211, round(25 + depth * rain * 76)),
                  (x, y), (x - length * .16, y + length), .65)
    for index in range(round(rain * 10)):
        phase = (now * .65 + index * .31) % 1
        x, y = 43 + (index * 113) % 669, 252 + (index * 17) % 25
        draw.ellipse(lights, (156, 195, 196, round((1 - phase) * rain * 100)),
                     (x - phase * 9, y, 3 + phase * 18, 1 + phase * 3), .6)
    canvas.blit(lights, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
    place_stage(surface, rect, canvas, backdrop=plate)


def _draw_procedural_garden(surface, rect, mix, now, playing=False, rhythm_mix=None,
                flower_hover=None, listening_focus=None):
    """Draw a bounded, deterministic preview; master volume never harms growth.

    While playing, ``now`` is seconds since the actual audio loop was started.
    ``rhythm_mix`` supplies the audible character while a new recipe is being
    rendered. Live controls still preview growth; sound gestures stay on beat.
    """
    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return
    rain, bass, bells = [max(0, min(1, level)) if enabled else 0
                         for level, enabled in zip(mix.levels, mix.enabled)]
    density, pitch, sparkle = mix.character
    scene = scene_for(mix)
    time = float(now)
    rhythm_mix = mix if rhythm_mix is None else rhythm_mix
    bass_gain, _ = rhythm_levels(mix, playing and listening_focus in (None, 1))
    pulse = bass_pulse(time)
    # Preview gently breathes; audible bass movement follows its exact envelope.
    movement = (pulse if bass_gain > 0 else 0.5) if playing else 0.5 + 0.25 * math.sin(time * 0.8)
    root_light = bass_gain * pulse
    dawn = min(rain / 0.48, bass / 0.44, bells / 0.54, sparkle / 0.65, 1)
    dawn = max(0, (dawn - 0.62) / 0.38)
    world_width, world_height, _, _ = stage_geometry(rect)
    ratio = min(rect.width / world_width, rect.height / world_height)
    canvas, lights = garden_buffers(ratio)
    lights.fill((0, 0, 0, 0))

    # A low, warm horizon only appears when all three ingredients meet.
    top = blend((17, 43, 43), (37, 60, 62), dawn)
    bottom = blend((44, 78, 70), (181, 145, 106), dawn)
    if scene == "storm-roots":
        top, bottom = (18, 33, 45), (49, 80, 81)
    elif scene == "crystal-rain":
        top, bottom = (22, 43, 58), (66, 115, 130)
    elif scene == "starlit-canopy":
        top, bottom = (22, 31, 59), (58, 81, 111)
    elif scene == "amber-reeds":
        top, bottom = (45, 53, 50), (181, 139, 78)
    for y in range(0, HEIGHT, 4):
        draw.rect(canvas, blend(top, bottom, (y / HEIGHT) ** 1.8),
                         (0, y, WIDTH, 4))

    # Quiet landmarks remain visible even when the garden is resting.
    moon_color = blend((195, 212, 180), (244, 215, 162), dawn)
    draw.circle(canvas, moon_color, (518, 56), 17)
    draw.circle(canvas, blend(top, bottom, (49 / HEIGHT) ** 1.8), (526, 49), 16)
    for index in range(17):
        x = 31 + (index * 131) % 687
        y = 22 + (index * 43) % 100
        draw.circle(canvas, blend(top, (144, 179, 161), 0.48), (x, y), 1)
    if scene == "storm-roots":
        storm_clouds(canvas, time)
    elif scene == "starlit-canopy":
        star_canopy(canvas, lights, time)

    distant = [(0, 171), (0, 144), (67, 119), (139, 146), (208, 122),
               (287, 150), (365, 115), (446, 142), (535, 113), (637, 136),
               (709, 118), (WIDTH, 126), (WIDTH, 198)]
    draw.polygon(canvas, blend((37, 71, 65), (93, 111, 89), dawn), distant)
    hill = [(0, 193)]
    for x in range(0, WIDTH + 12, 12):
        y = 176 + 11 * math.sin(x / 109) + 5 * math.sin(x / 47)
        y += bass * 2.5 * (movement - 0.5) * math.sin(x / 58)
        hill.append((x, y))
    hill.extend(((WIDTH, HEIGHT), (0, HEIGHT)))
    draw.polygon(canvas, blend((33, 70, 58), (68, 97, 64), dawn), hill)

    # Near soil breathes with the one-second bass pulse used by the sound.
    ground = []
    for x in range(0, WIDTH + 8, 8):
        y = 232 + 12 * math.sin(x / 130 + 0.8) + 4 * math.sin(x / 37)
        y += bass * (movement - 0.5) * 9 * math.sin(x / 95 + 0.7)
        ground.append((x, y))
    draw.polygon(canvas, (22, 49, 42), ground + [(WIDTH, HEIGHT), (0, HEIGHT)])
    draw.lines(canvas, blend((48, 83, 63), (103, 143, 94), rain), False, ground, 3)

    # Roots become legible as low notes fill out the underground part of the view.
    if bass > 0.025:
        root_base = blend((24, 50, 42), blend((127, 139, 91), (126, 152, 135), pitch), bass)
        root_color = blend(root_base, (180, 206, 151), root_light * 0.8)
        if scene == "storm-roots":
            root_color = blend((85, 131, 144), (189, 215, 220), root_light)
        for index in range(7):
            x = 62 + index * 101
            y = 235 + 9 * math.sin(x / 130 + 0.8)
            reach = 26 + bass * 25
            lean = (movement - 0.5) * math.sin(index * 2.4) * bass * 10
            draw.lines(canvas, root_color, False,
                              curve((x, y), (x + 9 + lean, y + reach * 0.6),
                                    (x - 12 + lean, y + reach)), 2)
            if scene == "storm-roots":
                points = curve((x, y), (x + 9 + lean, y + reach * 0.6),
                               (x - 12 + lean, y + reach))
                draw.lines(lights, (130, 195, 224, round(9 + root_light * 60)), False, points, 8)
                glow(lights, (x + lean, y + reach * 0.65), (134, 202, 235), 31,
                     0.15 + root_light * 1.3)
            elif playing and root_light > 0:
                # A small light travels down the root as each low pulse swells.
                points = curve((x, y), (x + 9 + lean, y + reach * 0.6),
                               (x - 12 + lean, y + reach))
                point = points[min(12, round((time % 1) * 12))]
                glow(lights, point, (177, 209, 147), 13, root_light)
            for side in (-1, 1):
                draw.lines(canvas, root_color, False,
                                  curve((x + 4 + lean, y + reach * 0.4),
                                        (x + side * 14, y + reach * 0.52),
                                        (x + side * 24, y + reach * 0.63), 6), 1)

    # Stones and their rain-fed puddles give a tangible scale to the small garden.
    for index, (x, y, width) in enumerate(((116, 250, 34), (324, 264, 24),
                                          (540, 243, 31), (681, 267, 21))):
        if rain > 0.05:
            draw.ellipse(canvas, blend((25, 53, 45), (80, 141, 127), rain),
                                (x - 10, y + 4, width + 22 + rain * 16, 7))
            draw.arc(canvas, (99, 158, 139),
                            (x - 5, y + 4, width + 12, 6), 0.1, 2.7, 1)
        draw.ellipse(canvas, (66, 87, 74), (x, y - 4, width, 11))
        draw.arc(canvas, (102, 119, 96), (x + 1, y - 4, width - 4, 8),
                        0.3, 2.6, 1)

    # A broad moss carpet responds to rain strength, not to elapsed waiting time.
    if rain > 0.01:
        for index in range(46):
            x = 11 + (index * 137) % 725
            y = 240 + (index * 29) % 58
            width = 6 + rain * (5 + (index % 4) * 2)
            color = blend((34, 65, 48), (100, 153, 94), rain * (0.6 + (index % 3) * 0.14))
            draw.ellipse(canvas, color, (x, y, width, 3 + rain * 4))
            if rain > 0.5 and index % 3 == 0:
                draw.line(canvas, (137, 181, 114), (x + 3, y + 1), (x + 5, y - 3), 1)

    # Pitch lifts the ferns; level changes their sway and root pulse.
    for index, x in enumerate((35, 88, 188, 250, 420, 483, 599, 713)):
        y = 232 + 12 * math.sin(x / 130 + 0.8) + 4 * math.sin(x / 37)
        height = 11 + rain * 19 + bass * (15 + pitch * 29)
        lean = (movement - 0.5) * math.sin(index * 1.7) * bass * (6 + pitch * 6)
        color = blend((50, 79, 57), (109, 160, 112), max(rain, bass) * 0.9)
        fern(canvas, x, y, height * (0.8 + index % 3 * 0.13), lean, color, rain)

    if bells > 0:
        # Small wildflowers remain scenery; the four foreground plants play.
        count = max(1, round(bells * (6 + sparkle * 13)))
        for index in range(count):
            x = 49 + (index * 109 + 29) % 658
            y = 218 + 10 * math.sin(x / 130 + 0.8) + (index % 3) * 6
            height = 14 + (index * 11) % 18 + bells * 10
            sway = (movement - 0.5) * math.sin(index * 1.7) * bass * 8
            head = (x + sway, y - height)
            color = blend((104, 137, 103), (165, 165, 117), bells * (index % 4) / 3)
            draw.line(canvas, (62, 112, 86), (x, y), head, 1)
            draw.circle(canvas, color, (round(head[0]), round(head[1])), 2)
        for index in range(round(bells * (4 + sparkle * 13))):
            phase = index * 2.399
            x = 45 + (index * 97) % 659 + 10 * math.sin(time * 0.57 + phase)
            y = 103 + (index * 41) % 115 + 7 * math.sin(time * 0.74 + phase)
            brightness = 0.42 + 0.58 * (0.5 + 0.5 * math.sin(time * 2.1 + phase))
            glow(lights, (x, y), (213, 229, 147), 11, brightness * bells)
            draw.circle(canvas, blend((85, 130, 99), (238, 241, 169), brightness),
                               (round(x), round(y)), 2 if index % 4 == 0 else 1)

    if scene == "crystal-rain":
        crystal_clusters(canvas, lights, time)
    elif scene == "amber-reeds":
        amber_reeds(canvas, lights, time, bass)

    # Keep the playable heads in front of every scene-specific foreground.
    melody_flowers(canvas, lights, mix, rhythm_mix, time, playing, flower_hover, listening_focus)

    canvas.blit(lights, (0, 0))
    if rain > 0.01:
        drops = round(rain * (24 + density * 72))
        for index in range(drops):
            depth = 0.42 + (index % 5) * 0.145
            x = (index * 79.37 + 17) % WIDTH
            y = ((index * 47.91 + time * (72 + depth * 110)) % (HEIGHT + 30)) - 15
            length = 3 + density * 4 + rain * depth * 5
            color = blend((47, 88, 78), (160, 200, 180), depth * rain * 0.68)
            draw.line(canvas, color, (x, y), (x - length * 0.27, y + length), 1)
        for index in range(min(7, round(rain * 8))):
            phase = (time * 0.73 + index * 0.31) % 1
            x = 58 + (index * 113) % 626
            y = 265 + (index * 13) % 35
            color = blend((28, 58, 48), (110, 164, 141), (1 - phase) * rain * 0.6)
            draw.ellipse(canvas, color,
                                (x - phase * 8, y, 3 + phase * 16, 2 + phase * 3), 1)

    place_stage(surface, rect, canvas)


def draw_discovery_effect(surface, rect, accent, elapsed):
    """Draw a finite 1.4-second halo and seed-star burst over a new discovery."""
    if not math.isfinite(elapsed) or not 0 <= elapsed < 1.4:
        return
    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return
    progress = elapsed / 1.4
    fade = math.sin(math.pi * progress) ** 0.65
    color = blend(tuple(pygame.Color(accent))[:3], (251, 236, 184), 0.58)
    world_width, world_height, _, _ = stage_geometry(rect)
    ratio = min(rect.width / world_width, rect.height / world_height)
    canvas = make_surface((WIDTH, HEIGHT), pygame.SRCALPHA, ratio)
    center = (WIDTH / 2, HEIGHT * 0.53)
    radius = 29 + progress * 290
    draw.ellipse(canvas, (*color, round(90 * fade)),
                        (center[0] - radius, center[1] - radius * 0.36,
                         radius * 2, radius * 0.72), 2)
    draw.ellipse(canvas, (*color, round(30 * fade)),
                        (center[0] - radius - 5, center[1] - radius * 0.36 - 3,
                         radius * 2 + 10, radius * 0.72 + 6), 3)
    for index in range(28):
        angle = index * math.tau / 28 + 0.16 * math.sin(index * 2.4)
        travel = (22 + progress * (125 + index % 5 * 24))
        x = center[0] + math.cos(angle) * travel * 1.35
        y = center[1] + math.sin(angle) * travel * 0.53 - progress * 23
        size = (2 + index % 3) * (0.4 + fade * 0.6)
        alpha = round((145 + index % 3 * 28) * fade)
        if index % 3 == 0:
            draw.polygon(canvas, (*color, alpha),
                                [(x, y - size * 1.7), (x + size * 0.6, y),
                                 (x, y + size * 1.7), (x - size * 0.6, y)])
        else:
            draw.circle(canvas, (*color, alpha), (round(x), round(y)),
                               max(1, round(size * 0.55)))
    draw.rect(canvas, (*color, round(125 * fade)),
                     (2, 2, WIDTH - 4, HEIGHT - 4), width=2, border_radius=17)
    place_stage(surface, rect, canvas, frame=False)
