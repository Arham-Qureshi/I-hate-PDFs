import io
import re
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response, JSONResponse

from core.pdf_engine import split_pdf, split_pdf_to_zip, get_page_count, render_page_thumbnails
from dependencies import verify_api_key, check_rate_limit

router = APIRouter(prefix="/api")


def _parse_ranges(range_str: str) -> list[tuple[int, int]]:
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


@router.post("/split")
async def split(
    file: UploadFile = File(...),
    ranges: str = Form(...),
    _: str = Depends(verify_api_key),
    __: bool = Depends(check_rate_limit),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return JSONResponse(
            content={"error": "Please upload a valid PDF file."},
            status_code=400,
        )

    if not ranges:
        return JSONResponse(
            content={"error": "Please specify page ranges (e.g. 1-3, 4-6)."},
            status_code=400,
        )

    data = await file.read()
    buffer = io.BytesIO(data)

    try:
        is_force = ranges.lower() == "force"

        if is_force:
            total = get_page_count(buffer)
            parsed_ranges = [(i, i) for i in range(1, total + 1)]
        else:
            parsed_ranges = _parse_ranges(ranges)

        if len(parsed_ranges) == 1:
            parts = split_pdf(buffer, parsed_ranges)
            content = parts[0].read()
            start, end = parsed_ranges[0]
            filename = f"split_pages_{start}-{end}.pdf"
            return Response(
                content=content,
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        base = Path(file.filename).stem if file.filename else "split"
        zip_buf = split_pdf_to_zip(buffer, parsed_ranges, base_name=base)
        content = zip_buf.read()
        return Response(
            content=content,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{base}_split.zip"'},
        )
    except ValueError as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse(
            content={"error": f"Split failed: {str(e)}"},
            status_code=500,
        )
    finally:
        buffer.close()


@router.post("/split/info")
async def split_info(
    file: UploadFile = File(...),
    _: str = Depends(verify_api_key),
    __: bool = Depends(check_rate_limit),
):
    data = await file.read()
    buffer = io.BytesIO(data)
    try:
        count = get_page_count(buffer)
        return {"page_count": count}
    finally:
        buffer.close()


@router.post("/split/thumbnails")
async def split_thumbnails(
    file: UploadFile = File(...),
    _: str = Depends(verify_api_key),
    __: bool = Depends(check_rate_limit),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return JSONResponse(
            content={"error": "Please upload a valid PDF file."},
            status_code=400,
        )

    data = await file.read()
    buffer = io.BytesIO(data)
    try:
        thumbnails = render_page_thumbnails(buffer)
        return {"pages": thumbnails}
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to render thumbnails: {str(e)}"},
            status_code=500,
        )
    finally:
        buffer.close()
