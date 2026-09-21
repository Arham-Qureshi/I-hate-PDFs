def test_compress_pdf(client, sample_pdf):
    sample_pdf.seek(0)
    files = [("file", ("test.pdf", sample_pdf.read(), "application/pdf"))]
    response = client.post("/api/compress/pdf", files=files, data={"strength": "medium"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_compress_docx(client, sample_docx):
    sample_docx.seek(0)
    files = [("file", ("test.docx", sample_docx.read(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))]
    response = client.post("/api/compress/docx", files=files)
    assert response.status_code == 200
    assert "wordprocessingml" in response.headers["content-type"]
