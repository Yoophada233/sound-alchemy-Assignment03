"""A small living landscape drawn directly from the three sound controls."""

import math

import pygame


WIDTH = 748
HEIGHT = 310


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
    """A few translucent discs keep the light gentle and the cost bounded."""
    x, y = position
    for fraction, alpha in ((1, 10), (0.65, 17), (0.34, 30)):
        pygame.draw.circle(surface, (*color, round(alpha * strength)),
                           (round(x), round(y)), max(1, round(radius * fraction)))


def fern(surface, x, y, height, lean, color, wet):
    tip = (x + lean, y - height)
    pygame.draw.lines(surface, color, False,
                      curve((x, y), (x + lean * 0.15, y - height * 0.62), tip), 2)
    for index in range(1, 6):
        t = index / 7
        stem_x = x + lean * t * t
        stem_y = y - height * t
        length = height * (0.25 - t * 0.13)
        for side in (-1, 1):
            leaf_tip = (stem_x + side * length, stem_y - length * 0.52)
            pygame.draw.lines(surface, color, False,
                              curve((stem_x, stem_y),
                                    (stem_x + side * length * 0.78, stem_y - length * 0.08),
                                    leaf_tip, 5), 2)
    if wet > 0.6:
        pygame.draw.circle(surface, (159, 208, 183), (round(tip[0]), round(tip[1] + 3)), 1)


def flower(surface, lights, x, y, height, sway, openness, color, phase):
    head = (x + sway, y - height)
    pygame.draw.lines(surface, (87, 151, 126), False,
                      curve((x, y), (x + sway * 0.05, y - height * 0.55), head), 2)
    for side, fraction in ((-1, 0.32), (1, 0.52)):
        stem_x = x + sway * fraction * fraction
        stem_y = y - height * fraction
        pygame.draw.polygon(surface, (73, 137, 114),
                            [(stem_x, stem_y), (stem_x + side * 12, stem_y - 9),
                             (stem_x + side * 9, stem_y - 1)])
    radius = 3 + openness * 4
    glow(lights, head, color, 19 + openness * 9, openness)
    for petal in range(5):
        angle = petal * math.tau / 5 - math.pi / 2 + math.sin(phase) * 0.04
        center = (round(head[0] + math.cos(angle) * radius * 0.7),
                  round(head[1] + math.sin(angle) * radius * 0.7))
        pygame.draw.circle(surface, color, center, max(2, round(radius * 0.57)))
    pygame.draw.circle(surface, (255, 237, 176), (round(head[0]), round(head[1])), 2)


def draw_garden(surface, rect, mix, now, playing=False):
    """Draw a bounded, deterministic preview; master volume never harms growth.

    ``now`` is elapsed seconds. Audio playback is optional: the same controls
    preview their garden while the speaker is stopped, without starting sound.
    """
    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return
    rain, bass, bells = [max(0, min(1, level)) if enabled else 0
                         for level, enabled in zip(mix.levels, mix.enabled)]
    density, pitch, sparkle = mix.character
    time = float(now)
    pulse = 0.5 - 0.5 * math.cos(math.tau * time)
    dawn = min(rain / 0.48, bass / 0.44, bells / 0.54, sparkle / 0.65, 1)
    dawn = max(0, (dawn - 0.62) / 0.38)
    canvas = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    lights = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    # A low, warm horizon only appears when all three ingredients meet.
    top = blend((17, 43, 43), (37, 60, 62), dawn)
    bottom = blend((44, 78, 70), (181, 145, 106), dawn)
    for y in range(0, HEIGHT, 4):
        pygame.draw.rect(canvas, blend(top, bottom, (y / HEIGHT) ** 1.8),
                         (0, y, WIDTH, 4))

    # Quiet landmarks remain visible even when the garden is resting.
    moon_color = blend((195, 212, 180), (244, 215, 162), dawn)
    pygame.draw.circle(canvas, moon_color, (611, 56), 17)
    pygame.draw.circle(canvas, blend(top, bottom, (49 / HEIGHT) ** 1.8), (619, 49), 16)
    for index in range(17):
        x = 31 + (index * 131) % 687
        y = 22 + (index * 43) % 100
        pygame.draw.circle(canvas, blend(top, (144, 179, 161), 0.48), (x, y), 1)

    distant = [(0, 171), (0, 144), (67, 119), (139, 146), (208, 122),
               (287, 150), (365, 115), (446, 142), (535, 113), (637, 136),
               (709, 118), (WIDTH, 126), (WIDTH, 198)]
    pygame.draw.polygon(canvas, blend((37, 71, 65), (93, 111, 89), dawn), distant)
    hill = [(0, 193)]
    for x in range(0, WIDTH + 12, 12):
        y = 176 + 11 * math.sin(x / 109) + 5 * math.sin(x / 47)
        y += bass * 2.5 * math.sin(x / 58 + math.tau * time)
        hill.append((x, y))
    hill.extend(((WIDTH, HEIGHT), (0, HEIGHT)))
    pygame.draw.polygon(canvas, blend((33, 70, 58), (68, 97, 64), dawn), hill)

    # Near soil breathes with the one-second bass pulse used by the sound.
    ground = []
    for x in range(0, WIDTH + 8, 8):
        y = 232 + 12 * math.sin(x / 130 + 0.8) + 4 * math.sin(x / 37)
        y += bass * (pulse - 0.5) * 9 * math.sin(x / 95 + 0.7)
        ground.append((x, y))
    pygame.draw.polygon(canvas, (22, 49, 42), ground + [(WIDTH, HEIGHT), (0, HEIGHT)])
    pygame.draw.lines(canvas, blend((48, 83, 63), (103, 143, 94), rain), False, ground, 3)

    # Roots become legible as low notes fill out the underground part of the view.
    if bass > 0.025:
        root_color = blend((24, 50, 42), blend((127, 139, 91), (126, 152, 135), pitch), bass)
        for index in range(7):
            x = 62 + index * 101
            y = 235 + 9 * math.sin(x / 130 + 0.8)
            reach = 26 + bass * 25
            lean = math.sin(index * 2.4 + time * math.tau) * bass * 5
            pygame.draw.lines(canvas, root_color, False,
                              curve((x, y), (x + 9 + lean, y + reach * 0.6),
                                    (x - 12 + lean, y + reach)), 2)
            for side in (-1, 1):
                pygame.draw.lines(canvas, root_color, False,
                                  curve((x + 4 + lean, y + reach * 0.4),
                                        (x + side * 14, y + reach * 0.52),
                                        (x + side * 24, y + reach * 0.63), 6), 1)

    # Stones and their rain-fed puddles give a tangible scale to the small garden.
    for index, (x, y, width) in enumerate(((116, 250, 34), (324, 264, 24),
                                          (540, 243, 31), (681, 267, 21))):
        if rain > 0.05:
            pygame.draw.ellipse(canvas, blend((25, 53, 45), (80, 141, 127), rain),
                                (x - 10, y + 4, width + 22 + rain * 16, 7))
            pygame.draw.arc(canvas, (99, 158, 139),
                            (x - 5, y + 4, width + 12, 6), 0.1, 2.7, 1)
        pygame.draw.ellipse(canvas, (66, 87, 74), (x, y - 4, width, 11))
        pygame.draw.arc(canvas, (102, 119, 96), (x + 1, y - 4, width - 4, 8),
                        0.3, 2.6, 1)

    # A broad moss carpet responds to rain strength, not to elapsed waiting time.
    if rain > 0.01:
        for index in range(46):
            x = 11 + (index * 137) % 725
            y = 240 + (index * 29) % 58
            width = 6 + rain * (5 + (index % 4) * 2)
            color = blend((34, 65, 48), (100, 153, 94), rain * (0.6 + (index % 3) * 0.14))
            pygame.draw.ellipse(canvas, color, (x, y, width, 3 + rain * 4))
            if rain > 0.5 and index % 3 == 0:
                pygame.draw.line(canvas, (137, 181, 114), (x + 3, y + 1), (x + 5, y - 3), 1)

    # Pitch lifts the ferns; level changes their sway and root pulse.
    for index, x in enumerate((35, 88, 188, 250, 420, 483, 599, 713)):
        y = 232 + 12 * math.sin(x / 130 + 0.8) + 4 * math.sin(x / 37)
        height = 11 + rain * 19 + bass * (15 + pitch * 29)
        lean = math.sin(time * math.tau + index * 1.7) * bass * (3 + pitch * 3)
        color = blend((50, 79, 57), (109, 160, 112), max(rain, bass) * 0.9)
        fern(canvas, x, y, height * (0.8 + index % 3 * 0.13), lean, color, rain)

    if bells > 0.02:
        # Fixed positions make a particular recipe look like the same garden.
        count = round(bells * (6 + sparkle * 13))
        for index in range(count):
            x = 49 + (index * 109 + 29) % 658
            y = 233 + 10 * math.sin(x / 130 + 0.8) + (index % 3) * 10
            height = 23 + (index * 11) % 23 + bells * 19
            phase = time * 1.1 + index * 2.2
            sway = math.sin(time * math.tau + index * 1.7) * bass * 4
            color = blend((202, 217, 160), (241, 178, 134), (index % 4) / 3)
            openness = 0.38 + bells * 0.62
            flower(canvas, lights, x, y, height, sway, openness, color, phase)
        for index in range(round(bells * (4 + sparkle * 13))):
            phase = index * 2.399
            x = 45 + (index * 97) % 659 + 10 * math.sin(time * 0.57 + phase)
            y = 103 + (index * 41) % 115 + 7 * math.sin(time * 0.74 + phase)
            brightness = 0.42 + 0.58 * (0.5 + 0.5 * math.sin(time * 2.1 + phase))
            glow(lights, (x, y), (213, 229, 147), 11, brightness * bells)
            pygame.draw.circle(canvas, blend((85, 130, 99), (238, 241, 169), brightness),
                               (round(x), round(y)), 2 if index % 4 == 0 else 1)

    canvas.blit(lights, (0, 0))
    if rain > 0.01:
        drops = round(rain * (24 + density * 72))
        for index in range(drops):
            depth = 0.42 + (index % 5) * 0.145
            x = (index * 79.37 + 17) % WIDTH
            y = ((index * 47.91 + time * (72 + depth * 110)) % (HEIGHT + 30)) - 15
            length = 3 + density * 4 + rain * depth * 5
            color = blend((47, 88, 78), (160, 200, 180), depth * rain * 0.68)
            pygame.draw.line(canvas, color, (x, y), (x - length * 0.27, y + length), 1)
        for index in range(min(7, round(rain * 8))):
            phase = (time * 0.73 + index * 0.31) % 1
            x = 58 + (index * 113) % 626
            y = 265 + (index * 13) % 35
            color = blend((28, 58, 48), (110, 164, 141), (1 - phase) * rain * 0.6)
            pygame.draw.ellipse(canvas, color,
                                (x - phase * 8, y, 3 + phase * 16, 2 + phase * 3), 1)

    # Keep every moving mark inside the rounded miniature window.
    mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, WIDTH, HEIGHT), border_radius=18)
    canvas.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    if rect.size != (WIDTH, HEIGHT):
        canvas = pygame.transform.smoothscale(canvas, rect.size)
    surface.blit(canvas, rect.topleft)
