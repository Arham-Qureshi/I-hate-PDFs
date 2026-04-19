import io
import zipfile
import os
from PIL import Image

def compress_docx(buffer: io.BytesIO, quality: int = 60, max_width: int = 1500) -> io.BytesIO:
    """Compress DOCX by shrinking embedded images."""
    buffer.seek(0)
    in_zip = zipfile.ZipFile(buffer)
    out_buffer = io.BytesIO()
    
    with zipfile.ZipFile(out_buffer, "w", zipfile.ZIP_DEFLATED) as out_zip:
        for item in in_zip.infolist():
            content = in_zip.read(item.filename)

            # checking for images 
            if item.filename.startswith("word/media/") and item.filename.lower().endswith((".jpg", ".jpeg", ".png")):
                try:
                    img = Image.open(io.BytesIO(content))
                    
                    # Convert to RGB (for img)
                    if img.mode in ("RGBA", "P"):
                        pass
                    if img.width > max_width:
                        ratio = max_width / float(img.width)
                        new_height = int(float(img.height) * ratio)
                        img = img.resize((max_width, new_height), Image.LANCZOS)
                    
                    img_buffer = io.BytesIO()
                    fmt = "JPEG" if item.filename.lower().endswith((".jpg", ".jpeg")) else "PNG"
                    
                    if fmt == "JPEG":
                        img.save(img_buffer, format=fmt, quality=quality, optimize=True)
                    else:
                        img.save(img_buffer, format=fmt, optimize=True)
                        
                    content = img_buffer.getvalue()
                except Exception as e:
                    print(f"Failed to compress image {item.filename}: {e}")
                    
            out_zip.writestr(item, content)
            
    out_buffer.seek(0)
    return out_buffer
