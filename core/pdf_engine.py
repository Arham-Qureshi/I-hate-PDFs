from __future__ import annotations

import io
import zipfile
import subprocess
import tempfile
import os
import shutil

import fitz


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


def compress_pdf(buffer: io.BytesIO, strength: str = "ebook") -> io.BytesIO:
    settings = {
        "low": "/screen",
        "medium": "/ebook",
        "high": "/printer",
    }
    gs_setting = settings.get(strength, "/ebook")

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.pdf")
        output_path = os.path.join(tmpdir, "output.pdf")
        
        buffer.seek(0)
        with open(input_path, "wb") as f:
            f.write(buffer.read())
            
        cmd = [
            "gs",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS={gs_setting}",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-sOutputFile={output_path}",
            input_path
        ]
        
        subprocess.run(cmd, check=True)
        
        with open(output_path, "rb") as f:
            out = io.BytesIO(f.read())
            
    out.seek(0)
    return out


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

    def _set_font(bold=False, italic=False, size=None):
        style = ""
        if bold:
            style += "B"
        if italic:
            style += "I"
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

            bold = run.bold or False
            italic = run.italic or False
            underline = run.underline or False

            size = heading_size or default_font_size
            if run.font.size:
                size = run.font.size.pt

            _set_font(bold=bold or (heading_size is not None), italic=italic, size=size)

            if underline:
                pdf.set_font("Helvetica", pdf.font_style + "U", size)

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
                _set_font(size=default_font_size - 1)
                text = cell.text.strip()
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

    out = io.BytesIO()
    pdf.output(out)
    out.seek(0)
    return out
