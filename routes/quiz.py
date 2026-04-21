import io

from flask import Blueprint, render_template, request, current_app, jsonify

from core.quiz_generator import generate_quiz

quiz_bp = Blueprint("quiz", __name__)


@quiz_bp.route("/", methods=["GET"])
def index():
    return render_template("quiz/index.html")


@quiz_bp.route("/", methods=["POST"])
def process():
    file = request.files.get("file")

    if not file or not file.filename or not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Please upload a valid PDF file."}), 400

    buffer = io.BytesIO(file.read())
    num_questions = request.form.get("questions", 5, type=int)
    num_questions = max(5, min(num_questions, 15))

    task_mgr = current_app.config["TASK_MANAGER"]

    task_id = task_mgr.submit(
        generate_quiz,
        buffer=buffer,
        num_questions=num_questions,
        result_filename=f"quiz_{file.filename}.json",
        result_mimetype="application/json",
    )

    return jsonify({"task_id": task_id})
