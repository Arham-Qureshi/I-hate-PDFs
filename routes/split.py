from __future__ import annotations
import io
import re
from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for, jsonify
from core.pdf_engine import split_pdf, split_pdf_to_zip, get_page_count

split_bp = Blueprint("split", __name__)
def _parse_ranges(range_str: str) -> list[tuple[int, int]]:
    # handles "1-3, 5, 8-10" like a goodgirl
    ranges = []
    parts = [p.strip() for p in range_str.split(",") if p.strip()]
    for part in parts:
        match = re.match(r"^(\d+)\s*-\s*(\d+)$", part)
        if match:
            start, end = int(match.group(1)), int(match.group(2))
            ranges.append((start, end))
        elif part.isdigit():
            n = int(part)
            ranges.append((n, n))
        else:
            raise ValueError(f"Invalid range format: '{part}'")
    return ranges

@split_bp.route("/", methods=["GET"])
def index():
    return render_template("split/index.html")


@split_bp.route("/", methods=["POST"])
def process():
    file = request.files.get("file")
    range_str = request.form.get("ranges", "").strip()

    if not file or not file.filename or not file.filename.lower().endswith(".pdf"):
        flash("Please upload a valid PDF file.", "error")
        return redirect(url_for("split.index"))

    if not range_str:
        flash("Please specify page ranges (e.g. 1-3, 4-6).", "error")
        return redirect(url_for("split.index"))

    buffer = io.BytesIO(file.read())

    try:
        ranges = _parse_ranges(range_str)

        if len(ranges) == 1:
            parts = split_pdf(buffer, ranges)
            return send_file(parts[0], mimetype="application/pdf", as_attachment=True, download_name=f"split_pages_{ranges[0][0]}-{ranges[0][1]}.pdf")

        base = file.filename.rsplit(".", 1)[0] if file.filename else "split"
        zip_buf = split_pdf_to_zip(buffer, ranges, base_name=base)
        return send_file(zip_buf, mimetype="application/zip", as_attachment=True, download_name=f"{base}_split.zip")
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("split.index"))
    except Exception as e:
        flash(f"Split failed: {str(e)}", "error")
        return redirect(url_for("split.index"))
    finally:
        buffer.close()


@split_bp.route("/info", methods=["POST"])
def info():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file"}), 400

    buffer = io.BytesIO(file.read())
    try:
        count = get_page_count(buffer)
        return jsonify({"page_count": count})
    finally:
        buffer.close()