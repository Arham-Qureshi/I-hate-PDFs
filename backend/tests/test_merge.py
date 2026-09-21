import io


def test_merge_pdfs(client, sample_pdf):
    files = []
    for _ in range(2):
        sample_pdf.seek(0)
        files.append(("files", ("test.pdf", sample_pdf.read(), "application/pdf")))

    response = client.post("/api/merge", files=files)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 0


def test_merge_single_file_rejected(client, sample_pdf):
    sample_pdf.seek(0)
    files = [("files", ("test.pdf", sample_pdf.read(), "application/pdf"))]
    response = client.post("/api/merge", files=files)
    assert response.status_code == 400


def test_merge_non_pdf_rejected(client):
    files = [("files", ("test.txt", b"not a pdf", "text/plain"))]
    response = client.post("/api/merge", files=files)
    assert response.status_code == 400
