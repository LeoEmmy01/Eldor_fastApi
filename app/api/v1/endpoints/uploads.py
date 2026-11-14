import re
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse

from app.core.security import get_current_user
from app.models.user import User
from app.storage.local_storage import FileTooLargeError, LocalStorage

router = APIRouter()
storage = LocalStorage()

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}
_STORED_NAME = re.compile(r"^[a-f0-9]{32}\.(jpg|png|gif|webp)$")


def _detect_image_extension(header: bytes) -> Optional[str]:
    """Identify the real image type from its leading bytes (the client's
    Content-Type header and filename can't be trusted)."""
    if header.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if header[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return ".webp"
    return None


@router.post("/upload", summary="Upload a room photograph")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    header = await file.read(12)
    await file.seek(0)

    extension = _detect_image_extension(header)
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPEG, PNG, GIF, or WebP images are allowed.",
        )

    try:
        stored_path = await storage.save_file(
            file,
            folder=f"uploads/{current_user.id}",  # per-user folder enables ownership checks
            extension=extension,
            max_bytes=MAX_UPLOAD_BYTES,
        )
    except FileTooLargeError:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    stored_name = Path(stored_path).name
    return {
        "filename": stored_name,
        "url": str(request.app.url_path_for("get_uploaded_file", filename=stored_name)),
    }


@router.get("/files/{filename}", summary="Download one of your uploaded images")
async def get_uploaded_file(
    filename: str,
    kind: Literal["uploads", "generations"] = "uploads",
    current_user: User = Depends(get_current_user),
):
    # Only server-generated names are valid, so traversal strings never reach the disk
    if not _STORED_NAME.fullmatch(filename):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        path = Path(await storage.get_file(f"{kind}/{current_user.id}/{filename}"))
    except ValueError:
        raise HTTPException(status_code=404, detail="File not found")

    # Lookup is scoped to the caller's own folder, so other users' files read as 404
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path,
        media_type=_MEDIA_TYPES[path.suffix],
        headers={"X-Content-Type-Options": "nosniff"},
    )