"""Quiet foreground plants, composed once at the window's native pixel size."""

import pygame

from artwork import cutout


def plant(surface, index, area, flip=False, shade=1.0):
    """Fit a local transparent plant; a missing atlas simply leaves empty space."""
    original = cutout("foliage", index)
    if original is None:
        return
    area = pygame.Rect(area)
    ratio = min(area.width / original.get_width(), area.height / original.get_height())
    size = tuple(max(1, round(value * ratio)) for value in original.get_size())
    image = pygame.transform.smoothscale(original, size)
    if flip:
        image = pygame.transform.flip(image, True, False)
    if shade != 1:
        value = round(255 * shade)
        image.fill((value, value, value, 255), special_flags=pygame.BLEND_RGBA_MULT)
    target = image.get_rect(center=area.center)
    # Cast a soft shadow behind the leaf faces, without adding per-frame work.
    shadow = image.copy()
    shadow.fill((0, 0, 0, 115), special_flags=pygame.BLEND_RGBA_MULT)
    soft_size = tuple(max(1, value // 8) for value in size)
    shadow = pygame.transform.smoothscale(pygame.transform.smoothscale(shadow, soft_size), size)
    offset = max(2, round(size[1] * .012))
    surface.blit(shadow, target.move(offset, offset))
    surface.blit(image, target)


def frame(size):
    """Plants stay in page margins and the open space beside the title."""
    result = pygame.Surface(size, pygame.SRCALPHA)
    sx, sy = size[0] / 1280, size[1] / 960

    def place(index, area, flip=False, shade=1.0):
        x, y, width, height = area
        plant(result, index, (round(x * sx), round(y * sy),
                              round(width * sx), round(height * sy)), flip, shade)

    place(1, (355, -79, 249, 169), shade=.82)
    place(0, (-125, -50, 161, 340), shade=.85)
    place(0, (-126, 252, 169, 350), flip=True, shade=.75)
    place(1, (1234, -45, 161, 249), shade=.80)
    place(0, (1241, 217, 158, 347), flip=True, shade=.83)
    place(2, (-92, 742, 170, 244), shade=.85)
    place(3, (1204, 777, 185, 245), shade=.87)
    return result


def paint_surround(result, area):
    """Extend the same garden into wide/tall window gutters behind the page."""
    scale = min(area.width / 1280, area.height / 960)
    width, height = result.get_size()
    if area.left > 0:
        # Tuck the stems behind the page edge, keeping the outer leaves visible.
        for right in (False, True):
            edge = area.right if right else area.left
            plant_width = round(280 * scale)
            x = edge - 80 * scale if right else edge - plant_width + 80 * scale
            # Branch ends disappear behind the page instead of floating in a
            # gutter. Keep the leaves small enough to frame, not dwarf, the UI.
            plant(result, 1, (x, height * (.09 if right else .02),
                             plant_width, 300 * scale), flip=right, shade=.62)
            plant(result, 3, (x, height * (.43 if right else .40),
                             plant_width, 285 * scale), flip=right, shade=.52)
            plant_width = round(min(area.left + 60 * scale, 280 * scale))
            x = edge - 55 * scale if right else edge - plant_width + 55 * scale
            plant(result, 3 if right else 2,
                  (x - (25 * scale if not right else 0), height * .71,
                   plant_width + 25 * scale, height * .40), flip=right, shade=.72)
    if area.top > 0:
        plant(result, 1, (width * .25, area.top - 190 * scale, 400 * scale, 230 * scale), shade=.60)
        plant(result, 3, (width * .68, area.bottom - 25 * scale, 310 * scale, 220 * scale), shade=.65)
    return result
