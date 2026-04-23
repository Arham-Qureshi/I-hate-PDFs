from __future__ import annotations

import io
from pathlib import Path

from flask import Blueprint, jsonify, render_template, request, send_file

from core.pdf_engine import jpeg_images_to_pdf

jpeg_to_pdf_bp = Blueprint("jpeg_to_pdf", __name__)

_ALLOWED_EXTENSIONS = (".jpg", ".jpeg")
_ALLOWED_MIME_TYPES = {"image/jpeg", "image/pjpeg"}
_MAX_FILES_PER_REQUEST = 30


def _is_allowed_jpeg(filename: str, mimetype: str) -> bool:
    safe_name = (filename or "").lower()
    if not safe_name.endswith(_ALLOWED_EXTENSIONS):
        return False

    safe_mime = (mimetype or "").lower()
    return not safe_mime or safe_mime in _ALLOWED_MIME_TYPES


@jpeg_to_pdf_bp.route("/", methods=["GET"])
def index():
    return render_template("jpeg_to_pdf/index.html")


@jpeg_to_pdf_bp.route("/", methods=["POST"])
def process():
    uploads = [file for file in request.files.getlist("files") if file and file.filename]
    if not uploads:
        return jsonify({"error": "Please upload at least one JPEG image."}), 400

    if len(uploads) > _MAX_FILES_PER_REQUEST:
        return jsonify({"error": f"Please upload up to {_MAX_FILES_PER_REQUEST} images at a time."}), 400

    invalid_name = next(
        (file.filename for file in uploads if not _is_allowed_jpeg(file.filename, file.mimetype)),
        None,
    )
    if invalid_name:
        return jsonify({"error": f"Only .jpg/.jpeg files are supported. Problem file: {invalid_name}"}), 400

    buffers: list[io.BytesIO] = []
    try:
        for upload in uploads:
            payload = upload.read()
            if payload:
                buffers.append(io.BytesIO(payload))

        if not buffers:
            return jsonify({"error": "Uploaded files were empty."}), 400

        pdf_buf = jpeg_images_to_pdf(buffers)
        base_name = Path(uploads[0].filename or "images").stem
        return send_file(
            pdf_buf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{base_name}_images.pdf",
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Conversion failed: {str(exc)}"}), 500
    finally:
        for buffer in buffers:
            buffer.close()
