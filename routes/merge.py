from __future__ import annotations
import io
from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for
from core.pdf_engine import merge_pdfs

merge_bp = Blueprint("merge", __name__)
@merge_bp.route("/", methods=["GET"])
def index():
    return render_template("merge/index.html")

@merge_bp.route("/", methods=["POST"])
def process():
    files = request.files.getlist("files")

    if len(files) < 2:
        flash("Please upload at least 2 PDF files to merge.", "error")
        return redirect(url_for("merge.index"))

    buffers: list[io.BytesIO] = []
    for f in files:
        if not f.filename or not f.filename.lower().endswith(".pdf"):
            flash(f"'{f.filename}' is not a PDF file.", "error")
            return redirect(url_for("merge.index"))
        buf = io.BytesIO(f.read())
        buffers.append(buf)

    try:
        merged = merge_pdfs(buffers)
        return send_file(merged, mimetype="application/pdf", as_attachment=True, download_name="merged.pdf")
    except Exception as e:
        flash(f"Merge failed: {str(e)}", "error")
        return redirect(url_for("merge.index"))
    finally:
        for buf in buffers:
            buf.close()