import io
from PIL import Image


def _make_jpeg():
    img = Image.new("RGB", (100, 100), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


def test_jpeg_to_pdf(client):
    jpeg_buf = _make_jpeg()
    files = [("files", ("test.jpg", jpeg_buf.read(), "image/jpeg"))]
    response = client.post("/api/jpeg-to-pdf", files=files)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_jpeg_to_pdf_empty(client):
    files = [("files", ("test.txt", b"not an image", "text/plain"))]
    response = client.post("/api/jpeg-to-pdf", files=files)
    assert response.status_code == 400


def test_image_convert_jpeg_to_png(client):
    jpeg_buf = _make_jpeg()
    files = [("file", ("test.jpg", jpeg_buf.read(), "image/jpeg"))]
    response = client.post("/api/image-convert", files=files, data={"mode": "jpeg-to-png"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


def test_image_convert_png_to_jpeg(client):
    img = Image.new("RGB", (100, 100), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    files = [("file", ("test.png", buf.read(), "image/png"))]
    response = client.post("/api/image-convert", files=files, data={"mode": "png-to-jpeg"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"


def test_image_convert_invalid_mode(client):
    jpeg_buf = _make_jpeg()
    files = [("file", ("test.jpg", jpeg_buf.read(), "image/jpeg"))]
    response = client.post("/api/image-convert", files=files, data={"mode": "invalid"})
    assert response.status_code == 400
