def test_pdf_to_docx(client, sample_pdf):
    sample_pdf.seek(0)
    files = [("file", ("test.pdf", sample_pdf.read(), "application/pdf"))]
    response = client.post("/api/convert/pdf-to-docx", files=files)
    assert response.status_code == 200
    assert "wordprocessingml" in response.headers["content-type"]


def test_docx_to_pdf(client, sample_docx):
    sample_docx.seek(0)
    files = [("file", ("test.docx", sample_docx.read(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))]
    response = client.post("/api/convert/docx-to-pdf", files=files)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_pdf_to_docx_wrong_type(client):
    files = [("file", ("test.txt", b"not a pdf", "text/plain"))]
    response = client.post("/api/convert/pdf-to-docx", files=files)
    assert response.status_code == 400


def test_docx_to_pdf_wrong_type(client):
    files = [("file", ("test.txt", b"not a docx", "text/plain"))]
    response = client.post("/api/convert/docx-to-pdf", files=files)
    assert response.status_code == 400
