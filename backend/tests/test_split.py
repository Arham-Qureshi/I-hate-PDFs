import base64
import io
from PIL import Image


def test_split_info(client, sample_pdf):
    sample_pdf.seek(0)
    files = [("file", ("test.pdf", sample_pdf.read(), "application/pdf"))]
    response = client.post("/api/split/info", files=files)
    assert response.status_code == 200
    assert "page_count" in response.json()
    assert response.json()["page_count"] == 1


def test_split_single_page(client, sample_pdf):
    sample_pdf.seek(0)
    files = [("file", ("test.pdf", sample_pdf.read(), "application/pdf"))]
    response = client.post("/api/split", files=files, data={"ranges": "1"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_split_invalid_range(client, sample_pdf):
    sample_pdf.seek(0)
    files = [("file", ("test.pdf", sample_pdf.read(), "application/pdf"))]
    response = client.post("/api/split", files=files, data={"ranges": "abc"})
    assert response.status_code == 400


def test_split_empty_ranges(client, sample_pdf):
    sample_pdf.seek(0)
    files = [("file", ("test.pdf", sample_pdf.read(), "application/pdf"))]
    response = client.post("/api/split", files=files, data={"ranges": ""})
    assert response.status_code in (400, 422)


def test_split_thumbnails(client, sample_pdf):
    sample_pdf.seek(0)
    files = [("file", ("test.pdf", sample_pdf.read(), "application/pdf"))]
    res = client.post("/api/split/thumbnails", files=files)
    assert res.status_code == 200
    data = res.json()
    assert "pages" in data
    assert len(data["pages"]) == 1
    assert data["pages"][0]["page"] == 1
    img_bytes = base64.b64decode(data["pages"][0]["image"])
    img = Image.open(io.BytesIO(img_bytes))
    assert img.format == "JPEG"


def test_split_thumbnails_non_pdf(client):
    res = client.post(
        "/api/split/thumbnails",
        files={"file": ("test.txt", b"not a pdf", "text/plain")},
    )
    assert res.status_code == 400
