import io

from flask import Blueprint, jsonify, render_template, request

from core.quiz_generator import generate_quiz

quiz_bp = Blueprint("quiz", __name__)
_MAX_INLINE_UPLOAD_BYTES = 4 * 1024 * 1024


@quiz_bp.route("/", methods=["GET"])
def index():
    return render_template("quiz/index.html")


@quiz_bp.route("/", methods=["POST"])
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
    num_questions = request.form.get("questions", 5, type=int)
    num_questions = max(5, min(num_questions, 15))

    try:
        result = generate_quiz(
            buffer=buffer,
            num_questions=num_questions,
        )
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": f"Quiz generation failed: {str(exc)}"}), 500
    finally:
        buffer.close()
