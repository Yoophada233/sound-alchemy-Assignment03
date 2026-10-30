"""Eight glass botanical specimens and their journey onto the shelf.

Local sprites have procedural fallbacks in a 100-unit drawing space. The same
specimen fits a small card or an enlarged study without changing its identity.
"""

import math

import pygame
from artwork import SPECIMENS, paint_sprite


INK = (44, 75, 61)
FADED_INK = (157, 173, 153)
FADED_WASH = (218, 226, 207)
PAPER = (245, 244, 225)
FLIGHT_SECONDS = 1.35


def blend(first, second, amount):
    return tuple(round(a + (b - a) * amount) for a, b in zip(first, second))


class Pen:
    """Map simple botanical geometry to a clipped destination rectangle."""

    def __init__(self, surface, rect, accent, found):
        self.surface = surface
        self.rect = pygame.Rect(rect)
        self.scale = min(self.rect.width, self.rect.height) / 100
        self.origin = (self.rect.centerx - 50 * self.scale,
                       self.rect.centery - 50 * self.scale)
        accent = tuple(pygame.Color(accent))[:3] if isinstance(accent, str) else tuple(accent)[:3]
        self.ink = INK if found else FADED_INK
        self.color = accent if found else FADED_INK
        self.wash = blend(accent, PAPER, 0.65) if found else FADED_WASH
        self.light = blend(accent, PAPER, 0.83) if found else FADED_WASH
        self.dark = blend(accent, INK, 0.48) if found else FADED_INK

    def point(self, point):
        return (round(self.origin[0] + point[0] * self.scale),
                round(self.origin[1] + point[1] * self.scale))

    def line(self, points, color=None, width=1, closed=False):
        points = [self.point(point) for point in points]
        color = self.ink if color is None else color
        if width * self.scale < 1.5:
            pygame.draw.aalines(self.surface, color, closed, points)
        else:
            pygame.draw.lines(self.surface, color, closed, points,
                              max(1, round(width * self.scale)))

    def shape(self, points, color, outline=False):
        pygame.draw.polygon(self.surface, color, [self.point(point) for point in points])
        if outline:
            self.line(points, closed=True)

    def circle(self, center, radius, color, outline=False):
        radius = max(1, round(radius * self.scale))
        pygame.draw.circle(self.surface, color, self.point(center), radius)
        if outline:
            pygame.draw.circle(self.surface, self.ink, self.point(center), radius, 1)

    def oval(self, rect, color, outline=False):
        x, y = self.point(rect[:2])
        box = (x, y, max(1, round(rect[2] * self.scale)),
               max(1, round(rect[3] * self.scale)))
        pygame.draw.ellipse(self.surface, color, box)
        if outline:
            pygame.draw.ellipse(self.surface, self.ink, box, 1)

    def curve(self, start, control, end, color=None, width=1):
        points = []
        for index in range(11):
            t = index / 10
            points.append(((1 - t) ** 2 * start[0] + 2 * (1 - t) * t * control[0] + t ** 2 * end[0],
                           (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * control[1] + t ** 2 * end[1]))
        self.line(points, color, width)

    def leaf(self, base, tip, width=6, color=None):
        dx, dy = tip[0] - base[0], tip[1] - base[1]
        length = math.hypot(dx, dy)
        if not length:
            return
        normal = (-dy / length * width, dx / length * width)
        middle = ((base[0] + tip[0]) / 2, (base[1] + tip[1]) / 2)
        points = [base, (middle[0] + normal[0], middle[1] + normal[1]),
                  tip, (middle[0] - normal[0], middle[1] - normal[1])]
        self.shape(points, self.wash if color is None else color)
        self.line((base, tip), self.dark)

    def drop(self, x, y, size, color=None):
        # A pointed top and a rounded, six-sided lower body read at icon size.
        self.shape([(x, y - size), (x - size * 0.65, y),
                    (x - size * 0.67, y + size * 0.44),
                    (x - size * 0.32, y + size * 0.76),
                    (x + size * 0.32, y + size * 0.76),
                    (x + size * 0.67, y + size * 0.44),
                    (x + size * 0.65, y)],
                   self.wash if color is None else color, outline=True)

    def star(self, x, y, radius=3):
        self.shape([(x, y - radius), (x + radius * 0.35, y - radius * 0.3),
                    (x + radius, y), (x + radius * 0.3, y + radius * 0.3),
                    (x, y + radius), (x - radius * 0.3, y + radius * 0.3),
                    (x - radius, y), (x - radius * 0.3, y - radius * 0.3)], self.color)


def moss(pen):
    pen.oval((13, 67, 70, 18), pen.light)
    pen.drop(67, 29, 17)
    pen.curve((63, 30), (61, 36), (66, 38), pen.light, 2)
    pen.line(((14, 80), (30, 77), (43, 79), (57, 75), (78, 80)), pen.dark)
    for x, y, lean in ((24, 75, -5), (34, 73, 3), (46, 76, -2), (57, 73, 5), (69, 77, 5)):
        pen.curve((x, y + 3), (x + lean * 0.3, y - 11), (x + lean, y - 23), pen.dark)
        for height in (5, 12, 19):
            width = 6 - height * 0.14
            center = x + lean * height / 23
            pen.line(((center - width, y - height - 3), (center, y - height),
                      (center + width, y - height - 4)), pen.color)
    pen.circle((21, 49), 2, pen.color)
    pen.drop(39, 29, 4, pen.light)


def moon_roots(pen):
    # One filled crescent, rather than painting an opaque hole over the page.
    crescent = []
    for index in range(19):
        angle = math.radians(46 + index * 268 / 18)
        crescent.append((37 + math.cos(angle) * 19, 28 + math.sin(angle) * 19))
    for index in range(1, 15):
        t = index / 14
        crescent.append((50 - 22 * math.sin(math.pi * t), 14 + 28 * t))
    pen.shape(crescent, pen.wash)
    pen.line(((13, 53), (30, 51), (50, 54), (70, 50), (86, 52)), pen.dark)
    pen.shape(((19, 57), (79, 56), (66, 82), (47, 89), (31, 79)), pen.light)
    for base, bend, tip in (((46, 53), (48, 70), (43, 89)),
                            ((48, 60), (29, 67), (22, 79)),
                            ((47, 67), (65, 68), (74, 82)),
                            ((46, 76), (33, 75), (33, 86))):
        pen.curve(base, bend, tip, pen.dark)
    pen.line(((30, 69), (29, 77), (25, 84)), pen.color)
    pen.line(((62, 71), (61, 80), (65, 88)), pen.color)
    pen.star(72, 22, 4)
    pen.circle((83, 38), 1.5, pen.color)


def firefly(pen):
    pen.circle((53, 43), 27, pen.light)
    pen.curve((20, 89), (19, 65), (31, 52), pen.dark)
    pen.leaf((22, 72), (10, 60), 4)
    pen.leaf((23, 67), (38, 59), 4)
    # Open wings give the lantern insect a recognisable silhouette.
    pen.shape(((49, 41), (34, 23), (28, 28), (32, 42), (48, 51)), pen.wash, True)
    pen.shape(((57, 40), (69, 20), (76, 24), (73, 39), (58, 51)), pen.wash, True)
    pen.oval((46, 40, 14, 28), pen.color, True)
    pen.oval((48, 53, 10, 12), pen.light)
    pen.circle((53, 37), 5, pen.dark)
    pen.line(((50, 34), (45, 27)), pen.dark)
    pen.line(((56, 34), (60, 26)), pen.dark)
    pen.line(((46, 49), (39, 53), (36, 58)), pen.dark)
    pen.line(((59, 49), (65, 53), (69, 55)), pen.dark)
    pen.star(81, 61, 4)
    pen.star(37, 78, 2.5)


def dawn(pen):
    pen.circle((34, 36), 19, pen.light)
    pen.line(((11, 48), (56, 48)), pen.color)
    for angle in (-150, -110, -70, -30):
        theta = math.radians(angle)
        pen.line(((34 + 23 * math.cos(theta), 36 + 23 * math.sin(theta)),
                  (34 + 28 * math.cos(theta), 36 + 28 * math.sin(theta))), pen.color)
    pen.curve((50, 89), (47, 61), (65, 31), pen.dark, 1.5)
    pen.leaf((51, 74), (29, 60), 5)
    pen.leaf((53, 66), (77, 55), 5, pen.color)
    pen.curve((57, 49), (48, 47), (44, 36), pen.dark)
    for x, y, radius in ((65, 31, 10), (44, 35, 6)):
        for petal in range(5):
            angle = petal * math.tau / 5 - math.pi / 2
            pen.circle((x + math.cos(angle) * radius * 0.7,
                        y + math.sin(angle) * radius * 0.7), radius * 0.5, pen.wash)
        pen.circle((x, y), radius * 0.3, pen.color)
    pen.line(((36, 89), (56, 87), (70, 88)), pen.dark)


def storm(pen):
    pen.shape(((13, 36), (15, 27), (25, 23), (30, 17), (40, 17),
               (49, 10), (60, 14), (65, 24), (77, 24), (86, 32),
               (85, 39), (16, 39)), pen.wash, True)
    pen.line(((24, 29), (35, 26), (45, 28)), pen.light, 2)
    for x, y in ((25, 45), (39, 49), (64, 46), (77, 49)):
        pen.line(((x, y), (x - 4, y + 8)), pen.color)
    pen.line(((13, 61), (35, 60), (57, 63), (84, 60)), pen.dark)
    pen.curve((48, 61), (49, 75), (45, 92), pen.dark, 1.5)
    for a, b, c in (((49, 67), (29, 69), (18, 80)),
                     ((47, 75), (64, 70), (80, 82)),
                     ((46, 84), (32, 83), (27, 92))):
        pen.curve(a, b, c, pen.dark)
    pen.line(((31, 72), (30, 83), (21, 89)), pen.color)
    pen.line(((65, 76), (66, 87), (74, 91)), pen.color)


def crystals(pen):
    pen.oval((11, 77, 78, 12), pen.light)
    for x, top, width, lean in ((30, 42, 11, -5), (51, 16, 14, 3), (72, 48, 10, 5)):
        tip = (x + lean, top)
        left = (x - width, top + 15)
        right = (x + width, top + 16)
        bottom = (x + 2, 80)
        pen.shape((tip, left, (x - width + 2, 76), bottom, right), pen.wash, True)
        pen.shape((tip, right, bottom), pen.color)
        pen.line((tip, (x - 2, top + 22), bottom), pen.light)
        pen.line((left, (x - 2, top + 22), right), pen.dark)
    pen.drop(22, 22, 6, pen.light)
    pen.drop(80, 26, 5, pen.light)
    pen.line(((23, 88), (62, 88)), pen.color)


def canopy(pen):
    pen.curve((14, 88), (12, 26), (70, 19), pen.dark, 1.5)
    for a, b, tip in (((18, 55), (7, 47), (7, 33)),
                       ((26, 38), (31, 23), (28, 14)),
                       ((40, 27), (46, 16), (49, 12))):
        pen.curve(a, b, tip, pen.dark)
    pen.leaf((18, 59), (33, 48), 4)
    pen.leaf((23, 42), (11, 31), 4)
    pen.leaf((37, 29), (49, 18), 4)
    pen.leaf((57, 22), (73, 15), 3)
    constellation = ((32, 71), (46, 46), (64, 55), (80, 36), (85, 65))
    pen.line(constellation, pen.wash)
    for x, y in constellation:
        pen.star(x, y, 3.5)
    pen.circle((60, 83), 1.5, pen.color)
    pen.circle((73, 76), 1, pen.color)


def reeds(pen):
    pen.oval((21, 79, 64, 9), pen.light)
    for x, y, lean in ((33, 26, -8), (51, 13, 3), (69, 36, 8)):
        tip = (x + lean, y)
        pen.curve((x, 89), (x - 3, 58), tip, pen.dark)
        pen.leaf((x, 70), (x - 18, 55), 3)
        pen.leaf((x, 62), (x + 14, 44), 3, pen.wash)
        for grain in range(5):
            center = (tip[0] - lean * grain * 0.045, tip[1] + grain * 4)
            pen.leaf(center, (center[0] - 7, center[1] - 6), 2.5, pen.color)
            pen.leaf((center[0], center[1] + 2),
                     (center[0] + 7, center[1] - 3), 2.5, pen.wash)
    pen.line(((21, 89), (77, 89)), pen.dark)


MOTIFS = {
    "rainy-moss": moss,
    "moonlit-roots": moon_roots,
    "firefly-grove": firefly,
    "dawn-chorus": dawn,
    "storm-roots": storm,
    "crystal-rain": crystals,
    "starlit-canopy": canopy,
    "amber-reeds": reeds,
}


def draw_specimen(surface, rect, scene_id, accent, found=True):
    """Draw a distinct botanical silhouette, coloured only after discovery.

    The destination's previous clip is respected and restored. Tiny or empty
    rectangles are harmless, and unknown scene IDs simply draw nothing.
    """
    rect = pygame.Rect(rect)
    motif = MOTIFS.get(scene_id)
    if rect.width < 2 or rect.height < 2 or motif is None:
        return
    previous_clip = surface.get_clip()
    surface.set_clip(previous_clip.clip(rect))
    try:
        if scene_id in SPECIMENS and paint_sprite(surface, rect, "specimens",
                                                  SPECIMENS.index(scene_id), dim=not found):
            return
        motif(Pen(surface, rect, accent, found))
    finally:
        surface.set_clip(previous_clip)


def flight_point(start, end, progress, pixel_ratio=1):
    """A high, gentle arc connects the living garden to its collected study."""
    control = ((start[0] + end[0]) * 0.5,
               min(start[1], end[1]) - min(150 * pixel_ratio, 45 * pixel_ratio + abs(end[0] - start[0]) * 0.17))
    t = max(0, min(1, progress))
    return ((1 - t) ** 2 * start[0] + 2 * (1 - t) * t * control[0] + t ** 2 * end[0],
            (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * control[1] + t ** 2 * end[1])


def draw_collection_flight(surface, start, end, scene_id, accent, elapsed, pixel_ratio=1):
    """Send one petal to the notebook and finish with a small stamped ring.

    The caller owns the clock and queue. This deterministic 1.35-second effect
    has no persistent particles and does not draw outside the current clip.
    """
    if not 0 <= elapsed <= FLIGHT_SECONDS:
        return
    accent = tuple(pygame.Color(accent))[:3] if isinstance(accent, str) else tuple(accent)[:3]
    progress = min(1, elapsed / 1.08)
    # Smooth arrival without delaying the clear start of the journey.
    progress = 1 - (1 - progress) ** 1.6
    if elapsed < 1.12:
        for mote in range(5, 0, -1):
            trail = max(0, progress - mote * 0.045)
            if trail <= 0:
                continue
            position = flight_point(start, end, trail, pixel_ratio)
            color = blend(accent, PAPER, 0.24 + mote * 0.11)
            pygame.draw.circle(surface, color, (round(position[0]), round(position[1])),
                               max(1, round((4 - mote // 2) * pixel_ratio)))
        x, y = flight_point(start, end, progress, pixel_ratio)
        previous = flight_point(start, end, max(0, progress - 0.012), pixel_ratio)
        angle = math.atan2(y - previous[1], x - previous[0])
        radius = (8 if scene_id == "crystal-rain" else 10) * pixel_ratio
        local = ((-radius, 0), (0, -4 * pixel_ratio), (radius, 0), (0, 4 * pixel_ratio))
        points = [(round(x + px * math.cos(angle) - py * math.sin(angle)),
                   round(y + px * math.sin(angle) + py * math.cos(angle))) for px, py in local]
        pygame.draw.polygon(surface, blend(accent, PAPER, 0.35), points)
        pygame.draw.aalines(surface, INK, True, points)
        pygame.draw.aaline(surface, INK, points[0], points[2])
    if elapsed >= 1.00:
        stamp = min(1, (elapsed - 1.00) / 0.35)
        center = (round(end[0]), round(end[1]))
        radius = round((10 + 13 * stamp) * pixel_ratio)
        color = blend(accent, PAPER, stamp * 0.82)
        pygame.draw.circle(surface, color, center, radius, max(1, round(pixel_ratio)))
        if stamp < 0.7:
            pygame.draw.circle(surface, color, center, max(1, round(radius - 4 * pixel_ratio)), max(1, round(pixel_ratio)))
        for number in range(4):
            angle = number * math.pi / 2 + 0.5
            point = (round(end[0] + math.cos(angle) * (radius + 5 * pixel_ratio)),
                     round(end[1] + math.sin(angle) * (radius + 5 * pixel_ratio)))
            pygame.draw.circle(surface, color, point, max(1, round(pixel_ratio)))
