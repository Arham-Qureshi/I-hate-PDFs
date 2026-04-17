from __future__ import annotations
import io
import time
from collections import defaultdict
from functools import wraps
from flask import Blueprint, current_app, jsonify, request, send_file

api_bp = Blueprint("api", __name__)

#rate limiter
_rate_buckets: dict[str, list[float]] = defaultdict(list)


def _get_client_id() -> str:
    return request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")


def _check_rate_limit() -> bool:
    limit = current_app.config.get("API_RATE_LIMIT", 30)
    client = _get_client_id()
    now = time.time()
    window = 60.0

    _rate_buckets[client] = [t for t in _rate_buckets[client] if now - t < window]

    if len(_rate_buckets[client]) >= limit:
        return False

    _rate_buckets[client].append(now)
    return True


def require_api_key(f):
    """bearer token gate"""
    @wraps(f)
    def decorated(*args, **kwargs):
        secret = current_app.config.get("API_SECRET_KEY", "")

        # no key configured = open access (dev mode)
        if not secret:
            return f(*args, **kwargs)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({
                "error": "Missing or malformed Authorization header.",
                "hint": "Use: Authorization: Bearer <your-api-key>"
            }), 401

        token = auth_header[7:].strip()
        if token != secret:
            return jsonify({"error": "Invalid API key."}), 403

        return f(*args, **kwargs)
    return decorated


def rate_limited(f):
    """rejects if bucket is full"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not _check_rate_limit():
            return jsonify({
                "error": "Rate limit exceeded.",
                "hint": f"Max {current_app.config.get('API_RATE_LIMIT', 30)} requests/min."
            }), 429
        return f(*args, **kwargs)
    return decorated


@api_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "i-hate-pdfs"})

@api_bp.route("/status/<task_id>", methods=["GET"])
@require_api_key
@rate_limited
def status(task_id: str):
    task_mgr = current_app.config["TASK_MANAGER"]
    info = task_mgr.get_status(task_id)

    if info is None:
        return jsonify({"error": "Task not found."}), 404

    return jsonify(info)

@api_bp.route("/download/<task_id>", methods=["GET"])
@require_api_key
@rate_limited
def download(task_id: str):
    task_mgr = current_app.config["TASK_MANAGER"]
    result_data = task_mgr.get_result(task_id)

    if result_data is None:
        return jsonify({"error": "No result available."}), 404

    result, filename, mimetype = result_data

    # summaries are dicts
    if isinstance(result, dict):
        return jsonify(result)

    return send_file(result, mimetype=mimetype, as_attachment=True, download_name=filename)

@api_bp.route("/summarize", methods=["POST"])
@require_api_key
@rate_limited
def summarize():
    from core.summarizer import summarize_pdf

    file = request.files.get("file")
    if not file or not file.filename or not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Upload a valid .pdf file."}), 400

    max_size = current_app.config.get("MAX_CONTENT_LENGTH", 50 * 1024 * 1024)
    data = file.read()
    if len(data) > max_size:
        return jsonify({"error": f"File too large. Max {max_size // (1024*1024)}MB."}), 413

    buffer = io.BytesIO(data)

    sentences = request.form.get("sentences", 3, type=int)
    sentences = max(1, min(sentences, 10))

    algorithm = request.form.get("algorithm", "lsa")
    if algorithm not in ("lsa", "luhn", "text-rank"):
        algorithm = "lsa"

    try:
        result = summarize_pdf(buffer, sentences_per_page=sentences, algorithm=algorithm)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Summarization failed: {str(e)}"}), 500


@api_bp.route("/merge", methods=["POST"])
@require_api_key
@rate_limited
def merge():
    import fitz

    files = request.files.getlist("files")
    if len(files) < 2:
        return jsonify({"error": "Need at least 2 PDF files."}), 400

    try:
        merged = fitz.open()
        for f in files:
            if not f.filename or not f.filename.lower().endswith(".pdf"):
                return jsonify({"error": f"Invalid file: {f.filename}"}), 400
            doc = fitz.open(stream=f.read(), filetype="pdf")
            merged.insert_pdf(doc)
            doc.close()

        out = io.BytesIO()
        merged.save(out)
        merged.close()
        out.seek(0)

        return send_file(out, mimetype="application/pdf", as_attachment=True, download_name="merged.pdf")
    except Exception as e:
        return jsonify({"error": f"Merge failed: {str(e)}"}), 500