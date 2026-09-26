import io
import fitz
import pikepdf
import pytest
from PIL import Image


def _jpeg_bytes(img, quality=95):
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality)
    return buf.getvalue()


def _image_stream(pdf, img, colorspace):
    stream = pikepdf.Stream(pdf, _jpeg_bytes(img))
    stream["/Filter"] = pikepdf.Name("/DCTDecode")
    stream["/ColorSpace"] = pikepdf.Name(colorspace)
    stream["/Width"] = img.width
    stream["/Height"] = img.height
    stream["/Subtype"] = pikepdf.Name("/Image")
    return stream


@pytest.fixture
def nested_form_pdf():
    """Page content drawn through a Form XObject, as Word/Chrome emit."""
    pdf = pikepdf.new()
    page = pdf.add_blank_page()
    image = _image_stream(pdf, Image.new("RGB", (1600, 1600), "red"), "/DeviceRGB")
    form = pikepdf.Stream(pdf, b"q 612 0 0 792 0 0 cm /Im0 Do Q")
    form["/Type"] = pikepdf.Name("/XObject")
    form["/Subtype"] = pikepdf.Name("/Form")
    form["/BBox"] = pikepdf.Array([0, 0, 612, 792])
    form["/Resources"] = pikepdf.Dictionary({
        "/XObject": pikepdf.Dictionary({"/Im0": pdf.make_indirect(image)})
    })
    page["/Resources"] = pikepdf.Dictionary({
        "/XObject": pikepdf.Dictionary({"/Fm0": pdf.make_indirect(form)})
    })
    page["/Contents"] = pdf.make_indirect(pikepdf.Stream(pdf, b"/Fm0 Do"))
    out = io.BytesIO()
    pdf.save(out)
    out.seek(0)
    return out


@pytest.fixture
def grayscale_pdf():
    pdf = pikepdf.new()
    page = pdf.add_blank_page()
    image = _image_stream(pdf, Image.new("L", (1700, 2200), "gray"), "/DeviceGray")
    page["/Resources"] = pikepdf.Dictionary({
        "/XObject": pikepdf.Dictionary({"/Im0": pdf.make_indirect(image)})
    })
    # Resources alone are not enough: a PDF that never paints its image is a
    # blank page, and Ghostscript rightly prunes it.
    page["/Contents"] = pdf.make_indirect(
        pikepdf.Stream(pdf, b"q 612 0 0 792 0 0 cm /Im0 Do Q")
    )
    out = io.BytesIO()
    pdf.save(out)
    out.seek(0)
    return out


@pytest.fixture
def text_pdf():
    """Multi-page plain text — the shape Ghostscript dominates."""
    doc = fitz.open()
    for i in range(6):
        page = doc.new_page()
        y = 72
        for line in range(46):
            page.insert_text(
                (60, y),
                f"Paragraph {line}: consolidated statement of operations for entity "
                f"{i + 1} reports revenue of ${line * 1024}.50 and net income of "
                f"${line * 291}.25.",
                fontsize=9,
            )
            y += 15
    out = io.BytesIO()
    doc.save(out)
    doc.close()
    out.seek(0)
    return out


def _total_image_bytes(pdf_bytes):
    pdf = pikepdf.open(io.BytesIO(pdf_bytes))
    total = 0
    for page in pdf.pages:
        for _, ref in page.get_images().items():
            total += len(pdf.get_object(ref.objgen).read_raw_bytes())
    return total


def _colorspaces(pdf_bytes):
    pdf = pikepdf.open(io.BytesIO(pdf_bytes))
    found = []
    for page in pdf.pages:
        for _, ref in page.get_images().items():
            found.append(str(pdf.get_object(ref.objgen).get("/ColorSpace")))
    return found


def test_compress_pdf(client, sample_pdf):
    sample_pdf.seek(0)
    files = [("file", ("test.pdf", sample_pdf.read(), "application/pdf"))]
    response = client.post("/api/compress/pdf", files=files, data={"level": "quality"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_compress_docx(client, sample_docx):
    sample_docx.seek(0)
    files = [("file", ("test.docx", sample_docx.read(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))]
    response = client.post("/api/compress/docx", files=files)
    assert response.status_code == 200
    assert "wordprocessingml" in response.headers["content-type"]


def test_compress_reencodes_image_nested_in_form_xobject(client, nested_form_pdf):
    """Regression: page-level-only walk never saw images inside Form XObjects."""
    nested_form_pdf.seek(0)
    before = _total_image_bytes(nested_form_pdf.read())
    nested_form_pdf.seek(0)
    files = [("file", ("nested.pdf", nested_form_pdf.read(), "application/pdf"))]
    response = client.post("/api/compress/pdf", files=files, data={"level": "size"})

    assert response.status_code == 200
    assert _total_image_bytes(response.content) < before


def test_compress_handles_grayscale_image(client, grayscale_pdf):
    """Regression: mode 'L' failed the RGB-only guard and was dropped."""
    grayscale_pdf.seek(0)
    before = _total_image_bytes(grayscale_pdf.read())
    grayscale_pdf.seek(0)
    files = [("file", ("gray.pdf", grayscale_pdf.read(), "application/pdf"))]
    response = client.post("/api/compress/pdf", files=files, data={"level": "size"})

    assert response.status_code == 200
    assert _total_image_bytes(response.content) < before
    assert _colorspaces(response.content) == ["/DeviceGray"]


def test_compress_levels_produce_different_output(client, grayscale_pdf):
    """Regression: both levels fell through to the same structural rewrite."""
    outputs = {}
    for level in ("quality", "size"):
        grayscale_pdf.seek(0)
        files = [("file", ("gray.pdf", grayscale_pdf.read(), "application/pdf"))]
        response = client.post("/api/compress/pdf", files=files, data={"level": level})
        assert response.status_code == 200
        outputs[level] = response.content

    assert outputs["size"] != outputs["quality"]


def test_compress_never_returns_larger_than_input(client, nested_form_pdf):
    nested_form_pdf.seek(0)
    original = nested_form_pdf.read()
    files = [("file", ("nested.pdf", original, "application/pdf"))]
    response = client.post("/api/compress/pdf", files=files, data={"level": "quality"})

    assert response.status_code == 200
    assert len(response.content) <= len(original)


def test_compress_rejects_invalid_level(client, sample_pdf):
    sample_pdf.seek(0)
    files = [("file", ("test.pdf", sample_pdf.read(), "application/pdf"))]
    response = client.post("/api/compress/pdf", files=files, data={"level": "bogus"})
    assert response.status_code == 400


def test_compress_ghostscript_shrinks_text_pdf(client, text_pdf):
    """Regression: the image-only pass leaves text PDFs essentially untouched."""
    text_pdf.seek(0)
    original = text_pdf.read()
    files = [("file", ("text.pdf", original, "application/pdf"))]
    response = client.post("/api/compress/pdf", files=files, data={"level": "quality"})

    assert response.status_code == 200
    assert pikepdf.open(io.BytesIO(response.content)).pages
    assert len(response.content) < len(original) // 2


def test_compress_falls_back_to_image_pass_without_ghostscript(
    client, grayscale_pdf, monkeypatch
):
    """Vercel ships no `gs`; the re-encode pass must still compress."""
    from core import pdf_engine

    monkeypatch.setattr(pdf_engine, "_compress_with_ghostscript", lambda data, level: None)

    grayscale_pdf.seek(0)
    before = _total_image_bytes(grayscale_pdf.read())
    grayscale_pdf.seek(0)
    files = [("file", ("gray.pdf", grayscale_pdf.read(), "application/pdf"))]
    response = client.post("/api/compress/pdf", files=files, data={"level": "size"})

    assert response.status_code == 200
    assert _total_image_bytes(response.content) < before
    assert _colorspaces(response.content) == ["/DeviceGray"]
