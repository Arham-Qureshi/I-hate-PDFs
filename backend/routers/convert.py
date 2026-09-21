import io
from pathlib import Path
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response, JSONResponse

from core.pdf_engine import pdf_to_docx, docx_to_pdf
from dependencies import verify_api_key, check_rate_limit

router = APIRouter(prefix="/api")


@router.post("/convert/pdf-to-docx")
async def convert_pdf_to_docx(
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
        docx_buf = pdf_to_docx(buffer)
        content = docx_buf.read()
        base_name = Path(file.filename).stem if file.filename else "converted"
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{base_name}.docx"'},
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"Conversion failed: {str(e)}"},
            status_code=500,
        )
    finally:
        buffer.close()


@router.post("/convert/docx-to-pdf")
async def convert_docx_to_pdf(
    file: UploadFile = File(...),
    _: str = Depends(verify_api_key),
    __: bool = Depends(check_rate_limit),
):
    if not file.filename or not file.filename.lower().endswith(".docx"):
        return JSONResponse(
            content={"error": "Please upload a valid DOCX file."},
            status_code=400,
        )

    data = await file.read()
    buffer = io.BytesIO(data)

    try:
        pdf_buf = docx_to_pdf(buffer)
        content = pdf_buf.read()
        base_name = Path(file.filename).stem if file.filename else "converted"
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{base_name}.pdf"'},
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"Conversion failed: {str(e)}"},
            status_code=500,
        )
    finally:
        buffer.close()
