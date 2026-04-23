from __future__ import annotations
import io
from flask import Blueprint, jsonify, render_template, request, send_file
from core.pdf_engine import compress_pdf
from core.docx_engine import compress_docx

compress_bp = Blueprint("compress", __name__, url_prefix="/compress")
_MAX_INLINE_UPLOAD_BYTES = 4 * 1024 * 1024

@compress_bp.route("/pdf", methods=["GET"])
def pdf_index():
    return render_template("compress/pdf.html")

@compress_bp.route("/pdf", methods=["POST"])
def process_pdf():
    file = request.files.get("file")
    strength = request.form.get("strength", "ebook")

    if not file or not file.filename:
        return jsonify({"error": "No file uploaded"}), 400

    payload = file.read()
    if len(payload) == 0:
        return jsonify({"error": "Uploaded file is empty."}), 400
    if len(payload) > _MAX_INLINE_UPLOAD_BYTES:
        return jsonify({"error": "File too large for deployment runtime. Use a PDF under 4 MB."}), 413

    buffer = io.BytesIO(payload)
    
    import fitz
    doc = fitz.open(stream=buffer, filetype="pdf")
    if doc.page_count > 12:
        doc.close()
        return jsonify({"error": "Limit exceeded: Only PDFs under 12 pages are allowed."}), 400
    doc.close()
    buffer.seek(0)

    try:
        compressed_buf = compress_pdf(buffer, strength)
        base_name = file.filename.rsplit(".", 1)[0]
        return send_file(
            compressed_buf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{base_name}_compressed.pdf"
        )
    except Exception as e:
        return jsonify({"error": f"Compression failed: {str(e)}"}), 500

@compress_bp.route("/docx", methods=["GET"])
def docx_index():
    return render_template("compress/docx.html")

@compress_bp.route("/docx", methods=["POST"])
def process_docx():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "No file uploaded"}), 400

    payload = file.read()
    if len(payload) == 0:
        return jsonify({"error": "Uploaded file is empty."}), 400
    if len(payload) > _MAX_INLINE_UPLOAD_BYTES:
        return jsonify({"error": "File too large for deployment runtime. Use a DOCX under 4 MB."}), 413

    buffer = io.BytesIO(payload)
    
    try:
        from docx import Document
        doc = Document(buffer)
        # wordcounts
        pages = 0
        try:
            pages = doc.core_properties.pages
        except:
            pass
            
        if pages > 12:
            return jsonify({"error": "Limit exceeded: Only DOCX under 12 pages are allowed."}), 400
    except Exception:
        #let the engine try
        pass
        
    buffer.seek(0)

    try:
        compressed_buf = compress_docx(buffer)
        base_name = file.filename.rsplit(".", 1)[0]
        return send_file(
            compressed_buf,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            as_attachment=True,
            download_name=f"{base_name}_compressed.docx"
        )
    except Exception as e:
        return jsonify({"error": f"Compression failed: {str(e)}"}), 500
