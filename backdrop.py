"""A dark, quiet botanical surround, rendered once at the window's density."""

import math

import pygame

from foliage import frame, paint_surround
from artwork import source


def _fern(surface, start, tip, bend, color, scale):
    """Draw a curved stem and paired, pointed leaflets."""
    def stem(t):
        return (start[0] + (tip[0] - start[0]) * t + bend * math.sin(math.pi * t),
                start[1] + (tip[1] - start[1]) * t)

    points = [stem(i / 36) for i in range(37)]
    width = max(1, round(scale))
    pygame.draw.lines(surface, color, False, points, width)
    for index in range(2, 15):
        t = index / 16
        x, y = stem(t)
        before = stem(t - .015)
        after = stem(t + .015)
        dx, dy = after[0] - before[0], after[1] - before[1]
        length = math.hypot(dx, dy)
        if length == 0:
            continue
        dx, dy = dx / length, dy / length
        reach = (8 + 23 * math.sin(math.pi * t)) * scale
        for side in (-1, 1):
            leaf_tip = (x - dy * reach * side + dx * reach * .42,
                        y + dx * reach * side + dy * reach * .42)
            edge = (x - dy * reach * side * .50 - dx * reach * .13,
                    y + dx * reach * side * .50 - dy * reach * .13)
            inner = (x - dy * reach * side * .43 + dx * reach * .43,
                     y + dx * reach * side * .43 + dy * reach * .43)
            pygame.draw.lines(surface, color, False,
                              [(x, y), edge, leaf_tip, inner, (x, y)], width)


def _leaf(surface, base, tip, breadth, color, scale):
    """Draw one airy leaf outline and its central vein."""
    dx, dy = tip[0] - base[0], tip[1] - base[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return
    nx, ny = -dy / length, dx / length
    edges = []
    for side in (-1, 1):
        edge = []
        for index in range(25):
            t = index / 24
            bow = math.sin(math.pi * t) ** .85 * breadth * side
            edge.append((base[0] + dx * t + nx * bow,
                         base[1] + dy * t + ny * bow))
        edges.append(edge)
    width = max(1, round(scale))
    for edge in edges:
        pygame.draw.lines(surface, color, False, edge, width)
    pygame.draw.line(surface, color, base, tip, width)
    for index in range(1, 6):
        t = index / 7
        for side in (-1, 1):
            next_t = min(.97, t + .13)
            bow = math.sin(math.pi * next_t) ** .85 * breadth * side * .82
            pygame.draw.line(surface, color,
                             (base[0] + dx * t, base[1] + dy * t),
                             (base[0] + dx * next_t + nx * bow,
                              base[1] + dy * next_t + ny * bow), width)


def mist(size, area=None):
    """Anchor the soft colour field to the page, including any window gutters."""
    width, height = size
    if width <= 0 or height <= 0:
        raise ValueError("The background needs a positive width and height.")
    area = pygame.Rect((0, 0), size) if area is None else area
    haze = pygame.Surface((80, 60))
    top, bottom, light = (9, 23, 31), (8, 19, 25), (25, 47, 52)
    for y in range(60):
        v = (y / 59 * height - area.top) / area.height
        v = max(0, min(1, v))
        base = [top[i] * (1 - v) + bottom[i] * v for i in range(3)]
        for x in range(80):
            u = (x / 79 * width - area.left) / area.width
            glow = .74 * math.exp(-((u - .49) / .48) ** 2
                                  - ((v - .24) / .70) ** 2)
            color = [round(base[i] * (1 - glow) + light[i] * glow)
                     for i in range(3)]
            haze.set_at((x, y), color)
    return pygame.transform.smoothscale(haze, size)


def create_surround(size, area):
    return paint_surround(mist(size, area), area)


def create_background(size):
    """Cache the native-size backdrop; missing foliage keeps the line drawings."""
    width, height = size
    background = mist(size)
    details = pygame.Surface(size, pygame.SRCALPHA)
    sx, sy = width / 1280, height / 900
    scale = min(sx, sy)

    def point(x, y):
        return x * sx, y * sy

    # Faint ripples suggest sound travelling through the greenhouse mist.
    for cx, cy, radii in ((1304, 4, (80, 120, 163)),
                          (-80, 864, (160, 207, 254))):
        for radius in radii:
            rect = pygame.Rect(round((cx - radius) * sx),
                               round((cy - radius) * sy),
                               max(1, round(radius * 2 * sx)),
                               max(1, round(radius * 2 * sy)))
            pygame.draw.ellipse(details, (146, 146, 98, 12), rect,
                                max(1, round(scale)))

    # Botanical edges leave the title, controls and central reading area clear.
    fern_color = (119, 145, 115, 37)
    for start, tip, bend, fern_scale in (
            ((-8, 388), (21, 120), 14, 1.05),
            ((420, 104), (585, -33), 8, .87),
            ((1277, 665), (1257, 393), -13, 1.05),
            ((185, 947), (45, 804), -5, .82)):
        _fern(details, point(*start), point(*tip), bend * sx,
              fern_color, fern_scale * scale)

    leaf_color = (155, 150, 106, 28)
    for base, tip, breadth in (
            ((1210, 106), (1292, -34), 31),
            ((1248, 920), (1162, 838), 22),
            ((1263, 917), (1305, 766), 26),
            ((-13, 766), (26, 644), 24)):
        _leaf(details, point(*base), point(*tip), breadth * scale,
              leaf_color, scale)
    if source("foliage") is not None:
        details.set_alpha(45)
    background.blit(details, (0, 0))
    background.blit(frame(size), (0, 0))
    return background
