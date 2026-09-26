import io
import struct
import tracemalloc
import zipfile

from core.docx_engine import compress_docx


def _parts(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return {name: z.read(name) for name in z.namelist()}


def test_compress_docx_accepts_level_and_never_grows(sample_docx):
    sample_docx.seek(0)
    original = sample_docx.read()

    out = compress_docx(io.BytesIO(original), level="quality").getvalue()

    assert "word/document.xml" in _parts(out)
    assert len(out) <= len(original)


import math
import random

from PIL import Image
from docx import Document


def _photo_image() -> Image.Image:
    """Noise-heavy content: the one shape where JPEG clearly wins."""
    random.seed(0)
    img = Image.new("RGB", (800, 600))
    px = img.load()
    for y in range(600):
        for x in range(800):
            px[x, y] = (
                int(120 + 120 * math.sin(x / 80) + random.randint(-12, 12)) % 256,
                int(120 + 120 * math.cos(y / 60) + random.randint(-12, 12)) % 256,
                (x * y) % 256,
            )
    return img


def _flat_image() -> Image.Image:
    """Few colours: palette PNG wins, no rename expected."""
    return Image.new("RGB", (800, 600), "red")


def _gradient_image() -> Image.Image:
    """Already tiny: nothing should change."""
    img = Image.new("RGB", (800, 600))
    for y in range(600):
        for x in range(800):
            img.putpixel((x, y), (x * 255 // 800, y * 255 // 600, 128))
    return img


def build_image_docx(image: Image.Image) -> bytes:
    doc = Document()
    doc.add_paragraph("Figure 1")
    buf = io.BytesIO()
    image.save(buf, "PNG")
    doc.add_picture(io.BytesIO(buf.getvalue()))
    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()


def _post(client, payload: bytes, level: str):
    files = [("file", ("test.docx", payload,
                       "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))]
    return client.post("/api/compress/docx", files=files, data={"level": level})


def test_photo_png_is_renamed_to_jpeg(client):
    original = build_image_docx(_photo_image())
    response = _post(client, original, "size")

    assert response.status_code == 200
    parts = _parts(response.content)
    media = sorted(n for n in parts if n.startswith("word/media/"))
    assert media == ["word/media/image1.jpeg"]
    rels = parts["word/_rels/document.xml.rels"].decode()
    assert 'Target="media/image1.jpeg"' in rels
    assert "media/image1.png" not in rels
    assert len(response.content) < len(original)


def test_flat_image_keeps_its_extension(client):
    original = build_image_docx(_flat_image())
    response = _post(client, original, "size")

    assert response.status_code == 200
    assert "word/media/image1.png" in _parts(response.content)


def test_gradient_image_is_left_untouched(client):
    original = build_image_docx(_gradient_image())
    before = _parts(original)["word/media/image1.png"]

    response = _post(client, original, "quality")

    assert response.status_code == 200
    assert _parts(response.content)["word/media/image1.png"] == before


def test_image_levels_produce_different_output():
    original = build_image_docx(_photo_image())

    def media_payload(data: bytes) -> bytes:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            return z.read("word/media/image1.jpeg")

    quality = compress_docx(io.BytesIO(original), level="quality").getvalue()
    size = compress_docx(io.BytesIO(original), level="size").getvalue()

    assert media_payload(quality) != media_payload(size)


from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

from core.docx_engine import _subset_font_bytes, _xor_font


def build_test_ttf(codepoints) -> bytes:
    """A self-contained TTF so tests never depend on system fonts."""
    glyphs = [".notdef"] + [f"g{cp}" for cp in codepoints]

    def rect():
        pen = TTGlyphPen(None)
        pen.moveTo((50, 0)); pen.lineTo((450, 0))
        pen.lineTo((450, 700)); pen.lineTo((50, 700)); pen.closePath()
        return pen.glyph()

    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(glyphs)
    fb.setupCharacterMap({cp: f"g{cp}" for cp in codepoints})
    fb.setupGlyf({g: rect() for g in glyphs})
    fb.setupHorizontalMetrics({g: (500, 50) for g in glyphs})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "PlanTest", "styleName": "Regular"})
    fb.setupOS2(sTypoAscender=800, sTypoDescender=-200,
                usWinAscent=800, usWinDescent=200)
    fb.setupPost()
    buf = io.BytesIO()
    fb.save(buf)
    return buf.getvalue()


def test_xor_font_is_symmetric_and_zero_key_is_identity():
    ttf = build_test_ttf(range(32, 400))
    guid = "01014A78-CABC-4EF0-12AC-5CD89AEFDE01"
    obfuscated = _xor_font(ttf, guid)

    assert obfuscated[:4] != ttf[:4]
    assert _xor_font(obfuscated, guid) == ttf
    assert _xor_font(ttf, "00000000-0000-0000-0000-000000000000") == ttf


def test_xor_font_matches_real_word_output():
    # First 32 bytes of word/fonts/font1.odttf from a Word-written document,
    # paired with its fontKey. A correct decode yields a TrueType offset table.
    ciphertext = bytes.fromhex(
        "01dfef9ad84fad12f04abcfa3e0c554c"
        "841aad2ad85aadd2f04ebcd63f0e4447"
    )
    decoded = _xor_font(ciphertext, "01014A78-CABC-4EF0-12AC-5CD89AEFDE01")

    assert decoded[:4] == b"\x00\x01\x00\x00"      # TrueType scaler type
    assert int.from_bytes(decoded[4:6], "big") == 19  # numTables
    assert decoded[12:16] == b"FFTM"               # first table record tag
    assert decoded[28:32] == b"GDEF"


def test_subset_font_bytes_shrinks_and_keeps_used_glyphs():
    ttf = build_test_ttf(range(32, 600))

    subset = _subset_font_bytes(ttf, "ABC")

    assert subset is not None
    assert len(subset) < len(ttf) // 4
    assert {65, 66, 67} <= set(TTFont(io.BytesIO(subset)).getBestCmap())


def test_subset_font_bytes_returns_none_for_garbage():
    assert _subset_font_bytes(b"not a font at all", "ABC") is None


import re as _re

ZERO_GUID = "{00000000-0000-0000-0000-000000000000}"
PLAIN_GUID = "{01014A78-CABC-4EF0-12AC-5CD89AEFDE01}"


def build_font_docx(ttf: bytes, text: str, obfuscated: bool, guid: str) -> bytes:
    """A minimal DOCX embedding one font, mirroring what Word writes."""
    font_name = "PlanTest"
    doc = Document()
    run = doc.add_paragraph().add_run(text)
    run.font.name = font_name
    base = io.BytesIO()
    doc.save(base)
    base.seek(0)

    with zipfile.ZipFile(base) as z:
        parts = {n: z.read(n) for n in z.namelist()}

    ext = "odttf" if obfuscated else "ttf"
    blob = bytearray(ttf)
    if obfuscated:
        for i in range(32):
            blob[i] ^= bytes.fromhex(guid.strip("{}").replace("-", ""))[15 - (i % 16)]
    parts[f"word/fonts/font1.{ext}"] = bytes(blob)

    ct = parts["[Content_Types].xml"].decode()
    if obfuscated:
        font_decl = ('<Default Extension="odttf" ContentType='
                     '"application/vnd.openxmlformats-officedocument.obfuscatedFont"/>')
    else:
        font_decl = '<Default Extension="ttf" ContentType="application/x-font-ttf"/>'
    table_decl = ('<Override PartName="/word/fontTable.xml" ContentType='
                  '"application/vnd.openxmlformats-officedocument.'
                  'wordprocessingml.fontTable+xml"/>')
    ct = _re.sub(r"(<Types[^>]*>)", lambda m: m.group(1) + font_decl + table_decl, ct, count=1)
    parts["[Content_Types].xml"] = ct.encode()

    parts["word/fontTable.xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:fonts xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
        ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<w:font w:name="{font_name}">'
        f'<w:embedRegular r:id="rId1" w:fontKey="{guid}" w:subsetted="0"/>'
        "</w:font></w:fonts>"
    ).encode()

    parts["word/_rels/fontTable.xml.rels"] = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/font"'
        f' Target="fonts/font1.{ext}"/>'
        "</Relationships>"
    ).encode()

    doc_rels = parts["word/_rels/document.xml.rels"].decode()
    doc_rels = doc_rels.replace("</Relationships>",
                                '<Relationship Id="rIdFontTable" '
                                'Type="http://schemas.openxmlformats.org/officeDocument/'
                                '2006/relationships/fontTable" Target="fontTable.xml"/>'
                                "</Relationships>")
    parts["word/_rels/document.xml.rels"] = doc_rels.encode()

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, blob in parts.items():
            z.writestr(name, blob)
    return out.getvalue()


def test_compress_subsets_plain_ttf(client):
    ttf = build_test_ttf(range(32, 600))
    original = build_font_docx(ttf, "ABC", obfuscated=False, guid=ZERO_GUID)

    response = _post(client, original, "quality")

    assert response.status_code == 200
    part = _parts(response.content)["word/fonts/font1.ttf"]
    assert len(part) < len(ttf) // 4
    assert {65, 66, 67} <= set(TTFont(io.BytesIO(part)).getBestCmap())


def test_compress_subsets_obfuscated_font(client):
    ttf = build_test_ttf(range(32, 600))
    original = build_font_docx(ttf, "ABC", obfuscated=True, guid=PLAIN_GUID)

    response = _post(client, original, "quality")

    assert response.status_code == 200
    part = _parts(response.content)["word/fonts/font1.odttf"]
    assert len(part) < len(ttf) // 4

    key = bytes.fromhex(PLAIN_GUID.strip("{}").replace("-", ""))
    raw = bytearray(part)
    for i in range(32):
        raw[i] ^= key[15 - (i % 16)]
    font = TTFont(io.BytesIO(bytes(raw)))
    assert {"cmap", "glyf", "head"} <= set(font.keys())
    assert {65, 66, 67} <= set(font.getBestCmap())


def test_compress_keeps_font_when_subsetting_fails(client, monkeypatch):
    import core.docx_engine as engine

    ttf = build_test_ttf(range(32, 600))
    original = build_font_docx(ttf, "ABC", obfuscated=False, guid=ZERO_GUID)

    def boom(*_args, **_kwargs):
        raise ImportError("fontTools missing")

    monkeypatch.setattr(engine, "_subset_font_bytes", boom)
    response = _post(client, original, "quality")

    assert response.status_code == 200
    parts = _parts(response.content)
    assert "word/document.xml" in parts
    assert parts["word/fonts/font1.ttf"] == ttf
    # Distinguishes per-font degradation from bailing out to the original file.
    assert response.content != original


def test_compress_docx_rejects_invalid_level(client, sample_docx):
    sample_docx.seek(0)
    files = [("file", ("test.docx", sample_docx.read(),
                       "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))]
    response = client.post("/api/compress/docx", files=files, data={"level": "bogus"})
    assert response.status_code == 400


def test_compress_docx_accepts_both_levels(client, sample_docx):
    for level in ("quality", "size"):
        sample_docx.seek(0)
        files = [("file", ("test.docx", sample_docx.read(),
                           "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))]
        response = client.post("/api/compress/docx", files=files, data={"level": level})
        assert response.status_code == 200


def test_upload_cap_comes_from_settings(client, sample_docx, monkeypatch):
    # FastAPI binds Depends(get_settings) at import time, so patching the
    # module attribute has no effect. Settings() is rebuilt per request and
    # real environment variables outrank .env, so this reaches the router.
    monkeypatch.setenv("MAX_CONTENT_LENGTH", "10")
    sample_docx.seek(0)
    files = [("file", ("test.docx", sample_docx.read(),
                       "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))]
    response = client.post("/api/compress/docx", files=files, data={"level": "quality"})
    assert response.status_code == 413


def test_default_upload_cap_is_50mb():
    from config import Settings
    assert Settings().MAX_CONTENT_LENGTH == 50 * 1024 * 1024


def _rgba_image() -> Image.Image:
    """Alpha channel — exercises the flatten-to-white JPEG path."""
    random.seed(1)
    img = Image.new("RGBA", (800, 600))
    px = img.load()
    for y in range(600):
        for x in range(800):
            px[x, y] = (random.randint(0, 255), random.randint(0, 255),
                        random.randint(0, 255), random.randint(0, 255))
    return img


def test_alpha_image_is_recompressed():
    original = build_image_docx(_rgba_image())

    out = compress_docx(io.BytesIO(original), level="quality").getvalue()

    assert len(out) < len(original)
    assert "word/document.xml" in _parts(out)


def _build_understated_bomb(actual_bytes: int) -> bytes:
    """A ZIP whose central directory lies about a member's size.

    Declares file_size = 1024 while the stream really decompresses to
    `actual_bytes`. This is the shape that defeats a declared-size pre-check:
    infolist() reports 1024, yet reading still allocates the full payload.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("word/document.xml", "<w:document/>")
        z.writestr("word/media/bomb.bin", b"\0" * actual_bytes)
    raw = bytearray(buf.getvalue())

    name = b"word/media/bomb.bin"
    cd = raw.rfind(name) - 46
    assert struct.unpack("<I", bytes(raw[cd:cd + 4]))[0] == 0x02014B50, "central dir signature"
    raw[cd + 24:cd + 28] = struct.pack("<I", 1024)  # uncompressed size field
    return bytes(raw)


def test_zip_bomb_is_refused_with_bounded_memory():
    bomb = _build_understated_bomb(64 * 1024 * 1024)

    tracemalloc.start()
    try:
        out = compress_docx(io.BytesIO(bomb), level="quality").getvalue()
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    assert out == bomb, "bomb must be refused, not processed"
    assert peak < 48 * 1024 * 1024, f"allocated {peak:,} bytes for a small upload"
