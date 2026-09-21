import io
import fitz
import pytest
from fastapi.testclient import TestClient
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_pdf():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Hello, this is test content for merging and splitting.")
    out = io.BytesIO()
    doc.save(out)
    doc.close()
    out.seek(0)
    return out


@pytest.fixture
def sample_docx():
    from docx import Document
    doc = Document()
    doc.add_paragraph("Test paragraph for DOCX conversion.")
    out = io.BytesIO()
    doc.save(out)
    out.seek(0)
    return out
