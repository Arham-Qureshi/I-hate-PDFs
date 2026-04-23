from __future__ import annotations

import io

from flask import Blueprint, jsonify, render_template, request

from core.summarizer import summarize_pdf

summarize_bp = Blueprint("summarize", __name__)
_MAX_INLINE_UPLOAD_BYTES = 4 * 1024 * 1024


@summarize_bp.route("/", methods=["GET"])
def index():
    return render_template("summarize/index.html")


@summarize_bp.route("/", methods=["POST"])
def process():
    file = request.files.get("file")

    if not file or not file.filename or not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Please upload a valid PDF file."}), 400

    payload = file.read()
    if len(payload) == 0:
        return jsonify({"error": "Uploaded file is empty."}), 400
    if len(payload) > _MAX_INLINE_UPLOAD_BYTES:
        return jsonify({"error": "File too large for deployment runtime. Use a PDF under 4 MB."}), 413

    buffer = io.BytesIO(payload)
    sentences = request.form.get("sentences", 3, type=int)
    sentences = max(1, min(sentences, 10))

    algorithm = request.form.get("algorithm", "lsa")
    if algorithm not in ("lsa", "luhn", "text-rank"):
        algorithm = "lsa"

    try:
        result = summarize_pdf(
            buffer,
            sentences_per_page=sentences,
            algorithm=algorithm,
            mode="llama",
        )
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": f"Summarization failed: {str(exc)}"}), 500
    finally:
        buffer.close()
