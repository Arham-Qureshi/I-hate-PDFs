import io
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response, JSONResponse

from core.image_engine import convert_image_format
from dependencies import verify_api_key, check_rate_limit

router = APIRouter(prefix="/api")

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


@router.post("/image-convert")
async def image_convert(
    mode: str = Form("jpeg-to-png"),
    file: UploadFile = File(...),
    _: str = Depends(verify_api_key),
    __: bool = Depends(check_rate_limit),
):
    config = _MODES.get(mode)
    if not config:
        return JSONResponse(
            content={"error": "Invalid conversion mode."},
            status_code=400,
        )

    if not file.filename:
        return JSONResponse(
            content={"error": "Please upload an image file."},
            status_code=400,
        )

    safe_name = file.filename.lower()
    if not safe_name.endswith(config["source_exts"]):
        expected = " / ".join(config["source_exts"])
        return JSONResponse(
            content={"error": f"Invalid file type. Expected: {expected}"},
            status_code=400,
        )

    data = await file.read()
    if not data:
        return JSONResponse(
            content={"error": "Uploaded file is empty."},
            status_code=400,
        )

    buffer = io.BytesIO(data)
    try:
        converted = convert_image_format(buffer, config["target_format"])
        content = converted.read()
        base_name = Path(file.filename).stem or "converted"
        return Response(
            content=content,
            media_type=config["mimetype"],
            headers={"Content-Disposition": f'attachment; filename="{base_name}{config["download_ext"]}"'},
        )
    except ValueError as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse(
            content={"error": f"Conversion failed: {str(e)}"},
            status_code=500,
        )
    finally:
        buffer.close()
