from __future__ import annotations

import io
from pathlib import Path

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for

from core.image_engine import convert_image_format

image_convert_bp = Blueprint("image_convert", __name__)

_MODES = {
    "jpeg-to-png": {
        "source_exts": (".jpg", ".jpeg"),
        "target_format": "PNG",
        "download_ext": ".png",
        "mimetype": "image/png",
    },
    "png-to-jpeg": {
        "source_exts": (".png",),
        "target_format": "JPEG",
        "download_ext": ".jpg",
        "mimetype": "image/jpeg",
    },
}


@image_convert_bp.route("/", methods=["GET"])
def index():
    return render_template("image_convert/index.html")


@image_convert_bp.route("/", methods=["POST"])
def process():
    mode = request.form.get("mode", "jpeg-to-png")
    config = _MODES.get(mode)
    if not config:
        flash("Invalid conversion mode.", "error")
        return redirect(url_for("image_convert.index"))

    uploads = request.files.getlist("file")
    upload = next((f for f in uploads if f and f.filename), None)

    if not upload:
        flash("Please upload an image file.", "error")
        return redirect(url_for("image_convert.index"))

    safe_name = upload.filename.lower()
    if not safe_name.endswith(config["source_exts"]):
        expected = " / ".join(config["source_exts"])
        flash(f"Invalid file type. Expected: {expected}", "error")
        return redirect(url_for("image_convert.index"))

    buffer = io.BytesIO(upload.read())
    if buffer.getbuffer().nbytes == 0:
        buffer.close()
        flash("Uploaded file is empty.", "error")
        return redirect(url_for("image_convert.index"))

    try:
        converted = convert_image_format(buffer, config["target_format"])
        base_name = Path(upload.filename).stem or "converted"
        return send_file(
            converted,
            mimetype=config["mimetype"],
            as_attachment=True,
            download_name=f"{base_name}{config['download_ext']}",
        )
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("image_convert.index"))
    except Exception as exc:
        flash(f"Conversion failed: {str(exc)}", "error")
        return redirect(url_for("image_convert.index"))
    finally:
        buffer.close()
