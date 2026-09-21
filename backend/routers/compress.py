import io
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response, JSONResponse

from core.pdf_engine import compress_pdf
from core.docx_engine import compress_docx
from dependencies import verify_api_key, check_rate_limit

router = APIRouter(prefix="/api")

_MAX_INLINE_UPLOAD_BYTES = 4 * 1024 * 1024


@router.post("/compress/pdf")
async def compress_pdf_endpoint(
    file: UploadFile = File(...),
    strength: str = Form("medium"),
    _: str = Depends(verify_api_key),
    __: bool = Depends(check_rate_limit),
):
    if not file.filename:
        return JSONResponse(content={"error": "No file uploaded"}, status_code=400)

    data = await file.read()
    if len(data) == 0:
        return JSONResponse(content={"error": "Uploaded file is empty."}, status_code=400)
    if len(data) > _MAX_INLINE_UPLOAD_BYTES:
        return JSONResponse(
            content={"error": "File too large. Use a PDF under 4 MB."},
            status_code=413,
        )

    buffer = io.BytesIO(data)

    try:
        import fitz
        doc = fitz.open(stream=buffer, filetype="pdf")
        if doc.page_count > 12:
            doc.close()
            return JSONResponse(
                content={"error": "Limit exceeded: Only PDFs under 12 pages are allowed."},
                status_code=400,
            )
        doc.close()
        buffer.seek(0)

        compressed_buf = compress_pdf(buffer, strength)
        content = compressed_buf.read()
        base_name = Path(file.filename).stem
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{base_name}_compressed.pdf"'},
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"Compression failed: {str(e)}"},
            status_code=500,
        )


@router.post("/compress/docx")
async def compress_docx_endpoint(
    file: UploadFile = File(...),
    _: str = Depends(verify_api_key),
    __: bool = Depends(check_rate_limit),
):
    if not file.filename:
        return JSONResponse(content={"error": "No file uploaded"}, status_code=400)

    data = await file.read()
    if len(data) == 0:
        return JSONResponse(content={"error": "Uploaded file is empty."}, status_code=400)
    if len(data) > _MAX_INLINE_UPLOAD_BYTES:
        return JSONResponse(
            content={"error": "File too large. Use a DOCX under 4 MB."},
            status_code=413,
        )

    buffer = io.BytesIO(data)

    try:
        compressed_buf = compress_docx(buffer)
        content = compressed_buf.read()
        base_name = Path(file.filename).stem
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{base_name}_compressed.docx"'},
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"Compression failed: {str(e)}"},
            status_code=500,
        )
