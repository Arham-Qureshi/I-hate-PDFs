import io
from pathlib import Path
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response, JSONResponse

from core.pdf_engine import jpeg_images_to_pdf
from dependencies import verify_api_key, check_rate_limit

router = APIRouter(prefix="/api")

_ALLOWED_EXTENSIONS = (".jpg", ".jpeg")
_MAX_FILES_PER_REQUEST = 30


@router.post("/jpeg-to-pdf")
async def jpeg_to_pdf(
    files: list[UploadFile] = File(...),
    _: str = Depends(verify_api_key),
    __: bool = Depends(check_rate_limit),
):
    uploads = [f for f in files if f and f.filename]
    if not uploads:
        return JSONResponse(
            content={"error": "Please upload at least one JPEG image."},
            status_code=400,
        )

    if len(uploads) > _MAX_FILES_PER_REQUEST:
        return JSONResponse(
            content={"error": f"Please upload up to {_MAX_FILES_PER_REQUEST} images at a time."},
            status_code=400,
        )

    invalid_name = next(
        (f.filename for f in uploads if not f.filename or not f.filename.lower().endswith(_ALLOWED_EXTENSIONS)),
        None,
    )
    if invalid_name:
        return JSONResponse(
            content={"error": f"Only .jpg/.jpeg files are supported. Problem file: {invalid_name}"},
            status_code=400,
        )

    buffers: list[io.BytesIO] = []
    try:
        for upload in uploads:
            data = await upload.read()
            if data:
                buffers.append(io.BytesIO(data))

        if not buffers:
            return JSONResponse(
                content={"error": "Uploaded files were empty."},
                status_code=400,
            )

        pdf_buf = jpeg_images_to_pdf(buffers)
        content = pdf_buf.read()
        base_name = Path(uploads[0].filename or "images").stem
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{base_name}_images.pdf"'},
        )
    except ValueError as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse(
            content={"error": f"Conversion failed: {str(e)}"},
            status_code=500,
        )
    finally:
        for buf in buffers:
            buf.close()
