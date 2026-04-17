from __future__ import annotations

import io

from flask import Blueprint, render_template, request, current_app, jsonify

from core.summarizer import summarize_pdf

summarize_bp = Blueprint("summarize", __name__)


@summarize_bp.route("/", methods=["GET"])
def index():
    return render_template("summarize/index.html")


@summarize_bp.route("/", methods=["POST"])
def process():
    file = request.files.get("file")

    if not file or not file.filename or not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Please upload a valid PDF file."}), 400

    buffer = io.BytesIO(file.read())
    sentences = request.form.get("sentences", 3, type=int)
    sentences = max(1, min(sentences, 10))

    algorithm = request.form.get("algorithm", "lsa")
    if algorithm not in ("lsa", "luhn", "text-rank"):
        algorithm = "lsa"

    task_mgr = current_app.config["TASK_MANAGER"]

    task_id = task_mgr.submit(
        summarize_pdf,
        buffer,
        sentences_per_page=sentences,
        algorithm=algorithm,
        result_filename=f"{file.filename}_summary.json",
        result_mimetype="application/json",
    )

    return jsonify({"task_id": task_id})
