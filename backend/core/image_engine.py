from __future__ import annotations

import io

from PIL import Image, UnidentifiedImageError

_TARGET_FORMATS = {"PNG", "JPEG"}


def _to_jpeg_ready(image: Image.Image) -> Image.Image:
    has_alpha = image.mode in {"RGBA", "LA"} or (image.mode == "P" and "transparency" in image.info)
    if has_alpha:
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        rgba.close()
        return background

    if image.mode != "RGB":
        return image.convert("RGB")

    return image.copy()


def convert_image_format(buffer: io.BytesIO, target_format: str, jpeg_quality: int = 92) -> io.BytesIO:
    normalized_target = (target_format or "").upper()
    if normalized_target not in _TARGET_FORMATS:
        raise ValueError("Unsupported target format. Use PNG or JPEG.")

    buffer.seek(0)
    try:
        with Image.open(buffer) as source:
            if normalized_target == "PNG":
                if source.mode not in {"RGB", "RGBA", "L", "LA", "P"}:
                    converted = source.convert("RGBA")
                else:
                    converted = source.copy()
                save_kwargs = {"format": "PNG", "optimize": True}
            else:
                converted = _to_jpeg_ready(source)
                save_kwargs = {
                    "format": "JPEG",
                    "quality": jpeg_quality,
                    "optimize": True,
                    "progressive": True,
                }
    except UnidentifiedImageError as exc:
        raise ValueError("Uploaded file is not a readable image.") from exc

    try:
        out = io.BytesIO()
        converted.save(out, **save_kwargs)
        out.seek(0)
        return out
    finally:
        converted.close()
