import io
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response, JSONResponse

from core.pdf_engine import merge_pdfs
from dependencies import verify_api_key, check_rate_limit

router = APIRouter(prefix="/api")


@router.post("/merge")
async def merge(
    files: list[UploadFile] = File(...),
    _: str = Depends(verify_api_key),
    __: bool = Depends(check_rate_limit),
):
    if len(files) < 2:
        return JSONResponse(
            content={"error": "At least 2 PDF files are required to merge."},
            status_code=400,
        )

    buffers: list[io.BytesIO] = []
    try:
        for f in files:
            if not f.filename or not f.filename.lower().endswith(".pdf"):
                return JSONResponse(
                    content={"error": f"Invalid file: {f.filename}"},
                    status_code=400,
                )
            data = await f.read()
            buffers.append(io.BytesIO(data))

        merged = merge_pdfs(buffers)
        content = merged.read()
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="merged.pdf"'},
        )
    except ValueError as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse(
            content={"error": f"Merge failed: {str(e)}"},
            status_code=500,
        )
    finally:
        for buf in buffers:
            buf.close()
