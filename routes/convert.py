from __future__ import annotations
import io
from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for
from core.pdf_engine import pdf_to_docx

convert_bp = Blueprint("convert", __name__)
@convert_bp.route("/", methods=["GET"])
def index():
    return render_template("convert/index.html")

@convert_bp.route("/", methods=["POST"])
def process():
    file = request.files.get("file")

    if not file or not file.filename or not file.filename.lower().endswith(".pdf"):
        flash("Please upload a valid PDF file.", "error")
        return redirect(url_for("convert.index"))

    buffer = io.BytesIO(file.read())

    try:
        docx_buf = pdf_to_docx(buffer)
        base_name = file.filename.rsplit(".", 1)[0] if file.filename else "converted"
        return send_file(docx_buf, mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document", as_attachment=True, download_name=f"{base_name}.docx")
    except Exception as e:
        flash(f"Conversion failed: {str(e)}", "error")
        return redirect(url_for("convert.index"))
    finally:
        buffer.close()
