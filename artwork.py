"""Small, cached art assets; the controls and living effects stay in Python.

The painted files are local and optional. Missing or damaged art falls back to
the procedural garden, so a broken image never prevents listening or composing.
"""

from functools import lru_cache
from pathlib import Path

import pygame


ASSETS = Path(__file__).resolve().parent / "assets" / "glass"
SPECIMENS = ("rainy-moss", "moonlit-roots", "firefly-grove", "dawn-chorus",
             "storm-roots", "crystal-rain", "starlit-canopy", "amber-reeds")


@lru_cache(maxsize=5)
def source(name):
    try:
        return pygame.image.load(str(ASSETS / (name + ".png")))
    except (OSError, pygame.error):
        return None


@lru_cache(maxsize=18)
def cutout(name, index):
    """Read a sprite's occupied bounds, keeping the source sheet untouched."""
    sheet = source(name)
    if sheet is None:
        return None
    width, height = sheet.get_size()
    if name == "flowers":
        # The generated open flower is broader than the bud. Their actual
        # separation is at 64% of the sheet, rather than an equal-cell split.
        split = round(width * .64)
        area = (0, 0, split, height) if index == 0 else (split, 0, width - split, height)
    elif name in ("accents", "foliage"):
        split = round(width * (.55 if name == "accents" and index >= 2 else .5))
        x0, x1 = (0, split) if index % 2 == 0 else (split, width)
        y0, y1 = round(index // 2 * height / 2), round((index // 2 + 1) * height / 2)
        if name == "foliage" and index % 2 == 0:
            # The ivy ends below the midpoint; its transparent gutter is at 54%.
            middle = round(height * .54)
            y0, y1 = (0, middle) if index == 0 else (middle, height)
        area = (x0, y0, x1 - x0, y1 - y0)
    else:
        x0, x1 = round(index % 4 * width / 4), round((index % 4 + 1) * width / 4)
        y0, y1 = round(index // 4 * height / 2), round((index // 4 + 1) * height / 2)
        area = (x0, y0, x1 - x0, y1 - y0)
    cell = sheet.subsurface(area)
    bounds = cell.get_bounding_rect(min_alpha=16)
    return cell.subsurface(bounds).copy() if bounds.width and bounds.height else None


@lru_cache(maxsize=72)
def sprite(name, index, size, dim=False):
    original = cutout(name, index)
    if original is None:
        return None
    ratio = min(size[0] / original.get_width(), size[1] / original.get_height())
    dimensions = tuple(max(1, round(value * ratio)) for value in original.get_size())
    image = pygame.transform.smoothscale(original, dimensions)
    if dim:
        # A quiet, coloured silhouette still invites exploration before finding.
        image.fill((92, 120, 128, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return image


def paint_sprite(surface, rect, name, index, dim=False):
    """Fit art inside a physical-pixel rectangle and respect the caller's clip."""
    area = pygame.Rect(rect)
    if area.width <= 0 or area.height <= 0:
        return False
    image = sprite(name, index, area.size, dim)
    if image is None:
        return False
    destination = image.get_rect(center=area.center)
    surface.blit(image, destination)
    return True


@lru_cache(maxsize=3)
def landscape(size, mood):
    original = source("landscape")
    if original is None:
        return None
    # RGB avoids alpha holes and gives the live reflections a stable base.
    result = pygame.Surface(size)
    result.blit(pygame.transform.smoothscale(original, size), (0, 0))
    tint = {"storm-roots": (142, 174, 195), "crystal-rain": (181, 225, 255),
            "starlit-canopy": (183, 183, 238), "amber-reeds": (255, 214, 158),
            "dawn-chorus": (255, 218, 187)}.get(mood)
    if tint:
        result.fill(tint, special_flags=pygame.BLEND_RGB_MULT)
    return result


def clear_caches():
    """Release resolution-dependent images after resizing the window."""
    sprite.cache_clear()
    landscape.cache_clear()
    material.cache_clear()


@lru_cache(maxsize=64)
def material(size, fill, radius):
    """A restrained satin gradient, cached at the actual destination density."""
    result = pygame.Surface(size, pygame.SRCALPHA)
    color = pygame.Color(fill)
    for y in range(size[1]):
        light = 5 * (1 - y / max(1, size[1] - 1))
        shade = tuple(min(255, round(c + light)) for c in color[:3])
        pygame.draw.line(result, shade, (0, y), (size[0], y))
    mask = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
    result.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return result
