from __future__ import annotations

import io
import zipfile
import subprocess
import tempfile
import os
import shutil
import base64

import fitz
from PIL import Image


def merge_pdfs(buffers: list[io.BytesIO]) -> io.BytesIO:
    if len(buffers) < 2:
        raise ValueError("At least 2 PDF files are required to merge.")

    merged = fitz.open()
    try:
        for buf in buffers:
            buf.seek(0)
            src = fitz.open(stream=buf.read(), filetype="pdf")
            merged.insert_pdf(src)
            src.close()

        out = io.BytesIO()
        merged.save(out)
        out.seek(0)
        return out
    finally:
        merged.close()


def split_pdf(buffer: io.BytesIO, ranges: list[tuple[int, int]]) -> list[io.BytesIO]:
    buffer.seek(0)
    doc = fitz.open(stream=buffer.read(), filetype="pdf")
    total = doc.page_count
    parts: list[io.BytesIO] = []

    try:
        for start, end in ranges:
            if start < 1 or end > total or start > end:
                raise ValueError(f"Invalid range ({start}, {end}) for a {total}-page PDF.")
            part = fitz.open()
            part.insert_pdf(doc, from_page=start - 1, to_page=end - 1)
            out = io.BytesIO()
            part.save(out)
            out.seek(0)
            parts.append(out)
            part.close()
        return parts
    finally:
        doc.close()


def select_pdf_pages(buffer: io.BytesIO, pages: list[int]) -> io.BytesIO:
    buffer.seek(0)
    doc = fitz.open(stream=buffer.read(), filetype="pdf")
    total = doc.page_count
    out = fitz.open()
    try:
        for p in pages:
            if p < 1 or p > total:
                raise ValueError(f"Page {p} out of range (1-{total})")
            out.insert_pdf(doc, from_page=p - 1, to_page=p - 1)
        buf = io.BytesIO()
        out.save(buf)
        buf.seek(0)
        return buf
    finally:
        doc.close()
        out.close()


def split_pdf_to_zip(buffer: io.BytesIO, ranges: list[tuple[int, int]], base_name: str = "split") -> io.BytesIO:
    # zip em up
    parts = split_pdf(buffer, ranges)
    zip_buf = io.BytesIO()

    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, part in enumerate(parts, 1):
            zf.writestr(f"{base_name}_part_{i}.pdf", part.read())
            part.close()

    zip_buf.seek(0)
    return zip_buf


def extract_text(buffer: io.BytesIO, page_num: int | None = None) -> str:
    buffer.seek(0)
    doc = fitz.open(stream=buffer.read(), filetype="pdf")

    try:
        if page_num is not None:
            if page_num < 1 or page_num > doc.page_count:
                raise ValueError(f"Page {page_num} out of range (1-{doc.page_count}).")
            return doc[page_num - 1].get_text()
        else:
            return "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()


def get_page_count(buffer: io.BytesIO) -> int:
    buffer.seek(0)
    doc = fitz.open(stream=buffer.read(), filetype="pdf")
    count = doc.page_count
    doc.close()
    return count


def pdf_to_docx(buffer: io.BytesIO) -> io.BytesIO:
    # pdf2docx needs real files, unfortunately
    import tempfile
    import os

    buffer.seek(0)
    pdf_bytes = buffer.read()

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, "input.pdf")
        docx_path = os.path.join(tmpdir, "output.docx")

        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)

        from pdf2docx import Converter
        cv = Converter(pdf_path)
        cv.convert(docx_path)
        cv.close()

        with open(docx_path, "rb") as f:
            out = io.BytesIO(f.read())

    out.seek(0)
    return out


def jpeg_images_to_pdf(buffers: list[io.BytesIO]) -> io.BytesIO:
    if not buffers:
        raise ValueError("At least one JPEG image is required.")

    from PIL import Image, UnidentifiedImageError

    pages: list[Image.Image] = []
    try:
        for idx, buffer in enumerate(buffers, start=1):
            buffer.seek(0)
            try:
                with Image.open(buffer) as image:
                    if image.format != "JPEG":
                        raise ValueError(f"File {idx} is not a JPEG image.")
                    pages.append(image.convert("RGB"))
            except UnidentifiedImageError as exc:
                raise ValueError(f"File {idx} is not a readable image.") from exc

        out = io.BytesIO()
        first_page, *rest_pages = pages
        first_page.save(out, format="PDF", save_all=True, append_images=rest_pages)
        out.seek(0)
        return out
    finally:
        for page in pages:
            page.close()


def get_pdf_metadata(buffer: io.BytesIO) -> dict:
    buffer.seek(0)
    doc = fitz.open(stream=buffer.read(), filetype="pdf")
    meta = {
        "page_count": doc.page_count,
        "title": doc.metadata.get("title", ""),
        "author": doc.metadata.get("author", ""),
        "subject": doc.metadata.get("subject", ""),
        "creator": doc.metadata.get("creator", ""),
        "producer": doc.metadata.get("producer", ""),
    }
    doc.close()
    return meta


_MIN_IMAGE_DIM = 200
_MAX_FORM_DEPTH = 8
_MAX_SMALLEST_DIM = 800
_QUALITY_JPEG = 80
_SMALLEST_JPEG = 30


def _collect_pdf_images(pdf, resources, depth=0, seen=None, found=None):
    """Map each reachable image objgen to every (xobjs, name) that references it.

    Recurses into Form XObjects because a page's visible content is often drawn
    entirely through one. Shared images yield several references so all of them
    can be updated after a single re-encode.
    """
    import pikepdf

    if seen is None:
        seen = set()
    if found is None:
        found = {}
    if resources is None or depth > _MAX_FORM_DEPTH:
        return found

    xobjects = resources.get("/XObject")
    if not isinstance(xobjects, pikepdf.Dictionary):
        return found

    for name in list(xobjects.keys()):
        ref = xobjects[name]
        if not hasattr(ref, "objgen") or ref.objgen in seen:
            continue
        seen.add(ref.objgen)
        obj = pdf.get_object(ref.objgen)
        subtype = obj.get("/Subtype")

        if subtype == pikepdf.Name("/Form"):
            _collect_pdf_images(pdf, obj.get("/Resources"), depth + 1, seen, found)
        elif subtype == pikepdf.Name("/Image"):
            found.setdefault(ref.objgen, (obj, []))[1].append((xobjects, name))

    return found


def _recompress_image(pdf, image, level):
    """Re-encode one image as JPEG, or return None to leave it untouched."""
    import pikepdf
    from PIL import Image

    # Transparency carries a mask we would drop, which corrupts rendering.
    if "/SMask" in image or "/Mask" in image or image.get("/ImageMask"):
        return None

    raw = image.read_raw_bytes()
    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except Exception:
        return None

    if min(img.size) < _MIN_IMAGE_DIM:
        return None

    aggressive = level == "size"
    quality = _SMALLEST_JPEG if aggressive else _QUALITY_JPEG
    keep_gray = False

    if img.mode in ("L", "LA", "1", "I;16"):
        img = img.convert("L")
        keep_gray = True
    elif img.mode in ("RGB", "RGBA", "P", "CMYK"):
        if img.mode == "CMYK" and not aggressive:
            return None
        if img.mode in ("RGBA", "P"):
            # JPEG has no alpha; compositing avoids black fringes.
            img = img.convert("RGBA")
            canvas = Image.new("RGBA", img.size, (255, 255, 255, 255))
            img = Image.alpha_composite(canvas, img)
        img = img.convert("RGB")
    else:
        return None

    if aggressive and max(img.size) > _MAX_SMALLEST_DIM:
        img.thumbnail((_MAX_SMALLEST_DIM, _MAX_SMALLEST_DIM), Image.LANCZOS)

    encoded = io.BytesIO()
    img.save(encoded, format="JPEG", quality=quality, optimize=True)
    compressed = encoded.getvalue()

    if not aggressive and len(compressed) >= len(raw):
        return None

    stream = pikepdf.Stream(pdf, compressed)
    stream["/Filter"] = pikepdf.Name("/DCTDecode")
    stream["/ColorSpace"] = pikepdf.Name("/DeviceGray" if keep_gray else "/DeviceRGB")
    stream["/Width"] = img.width
    stream["/Height"] = img.height
    stream["/Subtype"] = pikepdf.Name("/Image")
    return stream


_GHOSTSCRIPT_SETTINGS = {"quality": "/ebook", "size": "/screen"}


def _compress_with_ghostscript(data: bytes, level: str) -> bytes | None:
    """Ghostscript PDFSETTINGS pass — the strong one on text-heavy PDFs.

    Returns None when gs is absent (Vercel), the run fails or times out, or the
    output is not a readable PDF, so the caller knows to fall back.
    """
    import pikepdf

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.pdf")
        output_path = os.path.join(tmpdir, "output.pdf")
        with open(input_path, "wb") as f:
            f.write(data)

        try:
            subprocess.run(
                [
                    "gs",
                    "-sDEVICE=pdfwrite",
                    "-dCompatibilityLevel=1.4",
                    f"-dPDFSETTINGS={_GHOSTSCRIPT_SETTINGS[level]}",
                    "-dNOPAUSE",
                    "-dQUIET",
                    "-dBATCH",
                    f"-sOutputFile={output_path}",
                    input_path,
                ],
                timeout=120,
                capture_output=True,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return None

        if not os.path.exists(output_path):
            return None
        with open(output_path, "rb") as f:
            compressed = f.read()

    try:
        pdf = pikepdf.open(io.BytesIO(compressed))
        pdf.close()
    except Exception:
        return None
    return compressed


def _recompress_images(data: bytes, level: str) -> bytes | None:
    """Re-encode embedded images with Pillow. Returns None when it cannot win.

    Ghostscript only downsamples images sitting well above the PDFSETTINGS
    resolution, so table scans and moderate-size images are left to this pass.
    """
    import pikepdf

    pdf = pikepdf.open(io.BytesIO(data))
    for page in pdf.pages:
        try:
            resources = page["/Resources"]
        except (KeyError, TypeError):
            resources = None
        for image, references in _collect_pdf_images(pdf, resources).values():
            try:
                replacement = _recompress_image(pdf, image, level)
                if replacement is None:
                    continue
                indirect = pdf.make_indirect(replacement)
                for xobjects, name in references:
                    xobjects[name] = indirect
            except Exception:
                continue

    out = io.BytesIO()
    pdf.save(out, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
    pdf.close()

    # The structural pass alone can inflate slightly.
    if len(out.getvalue()) >= len(data):
        return None
    return out.getvalue()


def compress_pdf(buffer: io.BytesIO, level: str = "quality") -> io.BytesIO:
    buffer.seek(0)
    original = buffer.read()

    # Ghostscript first; the image pass only when gs is unavailable or did not help.
    result = _compress_with_ghostscript(original, level)
    if result and len(result) < len(original):
        return io.BytesIO(result)

    result = _recompress_images(original, level)
    if result and len(result) < len(original):
        return io.BytesIO(result)

    return io.BytesIO(original)


def docx_to_pdf(buffer: io.BytesIO) -> io.BytesIO:
    from docx import Document
    from docx.shared import Pt, Emu
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from fpdf import FPDF

    buffer.seek(0)
    doc = Document(buffer)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()


    default_font_size = 11
    line_height = 6

    def _sanitize_text(text: str) -> str:
        replacements = {
            '\u2018': "'", '\u2019': "'",
            '\u201c': '"', '\u201d': '"',
            '\u2013': "-", '\u2014': "--",
            '\u2026': "...",
            '\u00a0': " ",
            '\u2022': "-",
            '\u2122': "TM",
            '\u00a9': "(c)",
            '\u00ae': "(r)",
            '\x09': "    ",
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        return text.encode('latin-1', errors='ignore').decode('latin-1')

    def _set_font(bold=False, italic=False, underline=False, size=None):
        style = ""
        if bold:
            style += "B"
        if italic:
            style += "I"
        if underline:
            style += "U"
        pdf.set_font("Helvetica", style=style, size=size or default_font_size)

    def _get_align(paragraph):
        al = paragraph.alignment
        if al == WD_ALIGN_PARAGRAPH.CENTER:
            return "C"
        if al == WD_ALIGN_PARAGRAPH.RIGHT:
            return "R"
        if al == WD_ALIGN_PARAGRAPH.JUSTIFY:
            return "J"
        return "L"

    def _render_paragraph(para):
        if not para.text.strip() and not para.runs:
            pdf.ln(line_height)
            return

        align = _get_align(para)

        style_name = (para.style.name or "").lower()
        heading_size = None
        if style_name.startswith("heading"):
            try:
                level = int(style_name.split()[-1])
                heading_size = max(22 - (level * 2), 12)
            except (ValueError, IndexError):
                heading_size = 16

        for run in para.runs:
            text = run.text
            if not text:
                continue
            
            text = _sanitize_text(text)

            bold = run.bold or False
            italic = run.italic or False
            underline = run.underline or False

            size = heading_size or default_font_size
            if run.font.size:
                size = run.font.size.pt

            _set_font(bold=bold or (heading_size is not None), italic=italic, underline=underline, size=size)

            pdf.write(line_height, text)

        pdf.ln(line_height)

        if heading_size:
            pdf.ln(2)

    def _render_table(table):
        pdf.ln(2)
        col_count = len(table.columns)
        usable = pdf.w - pdf.l_margin - pdf.r_margin
        col_w = usable / col_count

        for row in table.rows:
            row_height = line_height + 2
            for cell in row.cells:
                _set_font(underline=False, size=default_font_size - 1)
                text = _sanitize_text(cell.text.strip())
                if len(text) > 80:
                    text = text[:77] + "..."
                pdf.cell(col_w, row_height, text, border=1)
            pdf.ln(row_height)
        pdf.ln(2)

    def _render_image(rel):
        try:
            image_blob = rel.target_part.blob
            img_buf = io.BytesIO(image_blob)

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(img_buf.getvalue())
                tmp_path = tmp.name

            usable = pdf.w - pdf.l_margin - pdf.r_margin
            pdf.image(tmp_path, w=min(usable, 120))
            pdf.ln(4)
            os.unlink(tmp_path)
        except Exception:
            pass  

    for element in doc.element.body:
        tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag

        if tag == "p":
            drawings = element.findall(f".//{qn('wp:inline')}")
            blips = element.findall(f".//{qn('a:blip')}")

            if blips:
                for blip in blips:
                    embed = blip.get(qn("r:embed"))
                    if embed and embed in doc.part.rels:
                        _render_image(doc.part.rels[embed])


            from docx.text.paragraph import Paragraph
            para = Paragraph(element, doc)
            _render_paragraph(para)

        elif tag == "tbl":
            from docx.table import Table as DocxTable
            tbl = DocxTable(element, doc)
            _render_table(tbl)

    out = io.BytesIO(pdf.output())
    out.seek(0)
    return out


def render_page_thumbnails(buffer: io.BytesIO, dpi: int = 72) -> list[dict]:
    buffer.seek(0)
    doc = fitz.open(stream=buffer.read(), filetype="pdf")
    thumbnails = []
    try:
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=dpi)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=80)
            b64 = base64.b64encode(buf.getvalue()).decode()
            thumbnails.append({"page": i + 1, "image": b64})
            buf.close()
        return thumbnails
    finally:
        doc.close()
