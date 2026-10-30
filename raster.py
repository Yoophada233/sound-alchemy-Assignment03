"""Draw logical coordinates directly into native-resolution Pygame surfaces."""

import ctypes
import os
import weakref

import pygame


_DENSITIES = weakref.WeakKeyDictionary()


def density(surface):
    return _DENSITIES.get(surface, 1.0)


def make_surface(size, flags=0, ratio=1.0):
    surface = pygame.Surface(tuple(max(1, round(value * ratio)) for value in size), flags)
    _DENSITIES[surface] = ratio
    return surface


def point(surface, position):
    ratio = density(surface)
    return round(position[0] * ratio), round(position[1] * ratio)


def rect(surface, area):
    ratio = density(surface)
    x, y, width, height = area
    left, top = round(x * ratio), round(y * ratio)
    return pygame.Rect(left, top, round((x + width) * ratio) - left,
                       round((y + height) * ratio) - top)


def viewport(size, logical=(1280, 960)):
    ratio = max(0.001, min(size[0] / logical[0], size[1] / logical[1]))
    area = pygame.Rect(0, 0, max(1, round(logical[0] * ratio)),
                       max(1, round(logical[1] * ratio)))
    area.center = (size[0] // 2, size[1] // 2)
    return area, ratio


def initial_window_size(logical):
    """Respect Windows UI scale without making a large-DPI window leave the screen."""
    if os.name != "nt" or pygame.display.get_driver() != "windows":
        return logical
    try:
        ratio = max(1, ctypes.windll.user32.GetDpiForSystem() / 96)
    except (AttributeError, OSError):
        ratio = 1
    width, height = pygame.display.get_desktop_sizes()[0]
    ratio = min(ratio, max(1, width - 64) / logical[0], max(1, height - 96) / logical[1])
    return tuple(max(1, round(value * ratio)) for value in logical)


def _width(surface, value):
    return max(1, round(value * density(surface))) if value > 0 else 0


class NativeDraw:
    """The small subset of pygame.draw used by the interface and garden."""

    def rect(self, surface, color, area, width=0, **corners):
        ratio = density(surface)
        corners = {key: max(0, round(value * ratio)) if value >= 0 else value
                   for key, value in corners.items()}
        return pygame.draw.rect(surface, color, rect(surface, area), _width(surface, width), **corners)

    def line(self, surface, color, start, end, width=1):
        return pygame.draw.line(surface, color, point(surface, start), point(surface, end),
                                _width(surface, width))

    def lines(self, surface, color, closed, positions, width=1):
        ratio = density(surface)
        return pygame.draw.lines(surface, color, closed,
                                 [(round(x * ratio), round(y * ratio)) for x, y in positions],
                                 _width(surface, width))

    def polygon(self, surface, color, positions, width=0):
        ratio = density(surface)
        return pygame.draw.polygon(surface, color,
                                   [(round(x * ratio), round(y * ratio)) for x, y in positions],
                                   _width(surface, width))

    def circle(self, surface, color, center, radius, width=0):
        return pygame.draw.circle(surface, color, point(surface, center),
                                  max(0, round(radius * density(surface))), _width(surface, width))

    def ellipse(self, surface, color, area, width=0):
        return pygame.draw.ellipse(surface, color, rect(surface, area), _width(surface, width))

    def arc(self, surface, color, area, start, end, width=1):
        return pygame.draw.arc(surface, color, rect(surface, area), start, end, _width(surface, width))


draw = NativeDraw()
