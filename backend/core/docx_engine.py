import io
import re as _re
import zipfile
import os
from PIL import Image

_MAX_UNCOMPRESSED_BYTES = 256 * 1024 * 1024
_MAX_EXPANSION = 50
_READ_CHUNK = 1 << 20


class _BudgetExceeded(Exception):
    """Raised the moment decompressed output passes the request budget."""


class _Budget:
    """Cumulative cap on ACTUAL decompressed bytes for one request.

    The cap is charged on bytes read, never on the sizes the archive declares.
    A ZIP central directory may understate file_size while its stream still
    decompresses far larger, so a declared-size check does not bound memory.
    """

    def __init__(self, limit: int):
        self.limit = limit
        self.used = 0

    def charge(self, amount: int) -> None:
        self.used += amount
        if self.used > self.limit:
            raise _BudgetExceeded(f"uncompressed data exceeds {self.limit} bytes")


def _uncompressed_budget(upload_len: int) -> int:
    return min(_MAX_UNCOMPRESSED_BYTES, upload_len * _MAX_EXPANSION)


def _read(zin: zipfile.ZipFile, name: str, budget: _Budget) -> bytes:
    """Read one member in chunks, aborting as soon as the budget is passed."""
    with zin.open(name) as fh:
        out = bytearray()
        while True:
            chunk = fh.read(_READ_CHUNK)
            if not chunk:
                break
            budget.charge(len(chunk))
            out += chunk
        return bytes(out)


def _is_valid_docx(data: bytes) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            return "word/document.xml" in z.namelist()
    except zipfile.BadZipFile:
        return False


def compress_docx(buffer: io.BytesIO, level: str = "quality") -> io.BytesIO:
    buffer.seek(0)
    original = buffer.read()

    try:
        zin = zipfile.ZipFile(io.BytesIO(original))
    except zipfile.BadZipFile:
        return io.BytesIO(original)

    try:
        budget = _Budget(_uncompressed_budget(len(original)))
        used = _used_characters(zin, budget)
        fonts = _font_parts(zin, budget)
        plan = _plan_images(zin, level, budget)
        renames = {old.rsplit("/", 1)[-1]: new.rsplit("/", 1)[-1] for old, (new, _) in plan.items() if old != new}

        out = io.BytesIO()
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zout:
            for item in zin.infolist():
                name = item.filename
                if name in plan:
                    new_name, blob = plan[name]
                    zout.writestr(new_name, blob)
                elif name in fonts:
                    zout.writestr(name, _shrink_font(_read(zin, name, budget), fonts[name], used))
                elif name.endswith(".rels"):
                    zout.writestr(name, _rewrite_rels(_read(zin, name, budget), renames))
                else:
                    zout.writestr(name, _read(zin, name, budget))
        result = out.getvalue()
    except Exception:
        return io.BytesIO(original)
    finally:
        zin.close()

    if len(result) >= len(original) or not _is_valid_docx(result):
        return io.BytesIO(original)
    return io.BytesIO(result)


_JPEG_QUALITY = {"quality": 80, "size": 60}
_MAX_IMAGE_WIDTH = 1500
_IMAGE_EXT = (".png", ".jpg", ".jpeg")


def _jpeg_bytes(img: Image.Image, level: str) -> bytes:
    work = img
    if work.mode in ("RGBA", "LA", "P"):
        work = work.convert("RGBA")
        background = Image.new("RGB", work.size, (255, 255, 255))
        background.paste(work, mask=work.split()[-1])
        work = background
    elif work.mode != "RGB":
        work = work.convert("RGB")
    if level == "size" and work.width > _MAX_IMAGE_WIDTH:
        work.thumbnail((_MAX_IMAGE_WIDTH, _MAX_IMAGE_WIDTH), Image.LANCZOS)
    buf = io.BytesIO()
    work.save(buf, "JPEG", quality=_JPEG_QUALITY[level], optimize=True)
    return buf.getvalue()


def _png8_bytes(img: Image.Image) -> bytes:
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        # FASTOCTREE is the only quantize method that preserves an alpha channel.
        palette = img.convert("RGBA").quantize(colors=256, method=Image.FASTOCTREE)
    else:
        palette = img.convert("RGB").quantize(colors=256)
    buf = io.BytesIO()
    palette.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def _plan_images(zin: zipfile.ZipFile, level: str, budget: _Budget) -> dict[str, tuple[str, bytes]]:
    """Pick the smallest encoding per image; map original name -> (name, bytes)."""
    taken = set(zin.namelist())
    plan: dict[str, tuple[str, bytes]] = {}
    for name in zin.namelist():
        if not name.startswith("word/media/"):
            continue
        if not name.lower().endswith(_IMAGE_EXT):
            continue
        raw = _read(zin, name, budget)
        try:
            img = Image.open(io.BytesIO(raw))
            img.load()
        except Exception:
            continue

        best_name, best_bytes, best_size = name, raw, len(raw)
        for blob in (_png8_bytes(img), _jpeg_bytes(img, level)):
            if len(blob) >= best_size:
                continue
            candidate = name
            if blob[:2] == b"\xff\xd8" and name.lower().endswith(".png"):
                candidate = name[:-4] + ".jpeg"
                if candidate in taken:
                    continue
            best_name, best_bytes, best_size = candidate, blob, len(blob)

        if best_name != name or best_bytes != raw:
            plan[name] = (best_name, best_bytes)
    return plan


def _rewrite_rels(data: bytes, renames: dict[str, str]) -> bytes:
    if not renames:
        return data
    text = data.decode("utf-8", "ignore")
    for old, new in renames.items():
        text = text.replace(f'media/{old}"', f'media/{new}"')
    return text.encode("utf-8")


def _xor_font(data: bytes, guid: str) -> bytes:
    """Obfuscate/de-obfuscate the first 32 bytes. The operation is its own inverse."""
    key = bytes.fromhex(guid.strip("{}").replace("-", ""))
    out = bytearray(data)
    for i in range(min(32, len(out))):
        out[i] ^= key[15 - (i % 16)]
    return bytes(out)


def _subset_font_bytes(data: bytes, text: str) -> bytes | None:
    from fontTools.subset import Options, Subsetter
    from fontTools.ttLib import TTFont

    try:
        font = TTFont(io.BytesIO(data))
        options = Options()
        options.layout_features = ["*"]
        options.notdef_outline = True
        options.drop_tables = ["DSIG", "FFTM"]
        subsetter = Subsetter(options=options)
        subsetter.populate(text=text)
        subsetter.subset(font)
        out = io.BytesIO()
        font.save(out)
        font.close()
    except Exception:
        return None

    result = out.getvalue()
    return result if len(result) < len(data) else None


_TEXT_PARTS_RE = _re.compile(
    r"^word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml$"
)
_EMBED_RE = _re.compile(r"<w:embed\w+\s+[^>]*/>")


def _used_characters(zin: zipfile.ZipFile, budget: _Budget) -> str:
    """Every character the document can render, plus ASCII as a safety floor."""
    found: set[str] = set()
    for name in zin.namelist():
        if not _TEXT_PARTS_RE.match(name):
            continue
        xml = _read(zin, name, budget).decode("utf-8", "ignore")
        for tag in ("w:t", "w:delText", "w:instrText"):
            for value in _re.findall(rf"<{tag}[^>]*>([^<]*)</{tag}>", xml):
                found.update(value)
    found.update(chr(code) for code in range(32, 127))
    return "".join(sorted(found))


def _font_parts(zin: zipfile.ZipFile, budget: _Budget) -> dict[str, str | None]:
    """Embedded font part -> obfuscation GUID, or None for a plain font.

    `.odttf` with no discoverable GUID is omitted so it is left untouched.
    Attribute order inside <w:embed.../> varies between producers, so r:id and
    w:fontKey are matched independently of each other.
    """
    names = set(zin.namelist())
    if "word/fontTable.xml" not in names or "word/_rels/fontTable.xml.rels" not in names:
        return {}

    table = _read(zin, "word/fontTable.xml", budget).decode("utf-8", "ignore")
    rels = _read(zin, "word/_rels/fontTable.xml.rels", budget).decode("utf-8", "ignore")

    rid_to_target: dict[str, str] = {}
    for element in _re.findall(r"<Relationship\b[^>]*/>", rels):
        rid = _re.search(r'Id="([^"]+)"', element)
        target = _re.search(r'Target="([^"]+)"', element)
        if rid and target:
            rid_to_target[rid.group(1)] = target.group(1)

    fonts: dict[str, str | None] = {}
    for element in _EMBED_RE.findall(table):
        rid = _re.search(r'r:id="(rId\d+)"', element)
        if not rid:
            continue
        target = rid_to_target.get(rid.group(1))
        if not target:
            continue
        part = "word/" + target.lstrip("/")
        if part.endswith(".odttf"):
            key = _re.search(r'w:fontKey="\{?([0-9A-Fa-f-]+)\}?"', element)
            if key:
                fonts[part] = key.group(1)
        elif part.endswith((".ttf", ".otf")):
            fonts[part] = None
    return fonts


def _shrink_font(raw: bytes, guid: str | None, used: str) -> bytes:
    """Subset one font, falling back to the original bytes on any failure.

    The broad except is deliberate: fontTools must never be able to abort
    compression of the whole document.
    """
    try:
        plain = _xor_font(raw, guid) if guid else raw
        subset = _subset_font_bytes(plain, used)
        if subset is None:
            return raw
        out = _xor_font(subset, guid) if guid else subset
        return out if len(out) < len(raw) else raw
    except Exception:
        return raw
