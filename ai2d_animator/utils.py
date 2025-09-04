from __future__ import annotations

from PIL import Image


def resize_cover(image: Image.Image, target_width: int, target_height: int) -> Image.Image:
    """Resize image to cover target size, cropping excess.

    Similar to CSS background-size: cover.
    """
    src_w, src_h = image.size
    scale = max(target_width / src_w, target_height / src_h)
    new_w = max(1, int(src_w * scale))
    new_h = max(1, int(src_h * scale))
    resized = image.resize((new_w, new_h), Image.LANCZOS)
    left = max(0, (new_w - target_width) // 2)
    top = max(0, (new_h - target_height) // 2)
    right = left + target_width
    bottom = top + target_height
    return resized.crop((left, top, right, bottom))

