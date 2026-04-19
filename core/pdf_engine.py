from __future__ import annotations

import io
import zipfile

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
