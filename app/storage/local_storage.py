import uuid
import re
import shutil
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

from app.storage.base import BaseStorage
from app.core.config import settings

_SAFE_EXTENSION = re.compile(r"^\.[a-z0-9]{1,5}$")
_CHUNK_SIZE = 1024 * 1024  # 1 MB


class FileTooLargeError(Exception):
    pass


class LocalStorage(BaseStorage):
    def __init__(self):
        self.base_dir = Path(settings.LOCAL_STORAGE_PATH).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_safe(self, relative_path) -> Path:
        """Resolve a path and guarantee it stays inside the storage directory."""
        candidate = (self.base_dir / relative_path).resolve()
        if candidate == self.base_dir or not candidate.is_relative_to(self.base_dir):
            raise ValueError("Path escapes the storage directory.")
        return candidate

    async def save_file(
        self,
        file: UploadFile,
        folder: str,
        extension: str = "",
        max_bytes: Optional[int] = None,
    ) -> str:
        """Save an upload under a server-generated name. Returns the path relative to
        the storage root (e.g. 'uploads/<user_id>/<uuid>.jpg'), not an absolute path."""
        target_folder = self._resolve_safe(folder)
        target_folder.mkdir(parents=True, exist_ok=True)

        extension = extension.lower()
        if extension and not _SAFE_EXTENSION.match(extension):
            extension = ""

        # Client-supplied file.filename is never used
        filename = f"{uuid.uuid4().hex}{extension}"
        dest = self._resolve_safe(Path(folder) / filename)

        written = 0
        try:
            with open(dest, "xb") as buffer:  # "x" = never overwrite an existing file
                while chunk := file.file.read(_CHUNK_SIZE):
                    written += len(chunk)
                    if max_bytes is not None and written > max_bytes:
                        raise FileTooLargeError()
                    buffer.write(chunk)
        except Exception:
            dest.unlink(missing_ok=True)  # don't leave partial files behind
            raise

        return dest.relative_to(self.base_dir).as_posix()

    async def get_file(self, file_path: str) -> str:
        """Return the absolute path of a stored file. Raises ValueError if the path
        points outside the storage directory."""
        return str(self._resolve_safe(file_path))

    async def delete_file(self, file_path: str) -> bool:
        path = self._resolve_safe(file_path)
        if path.is_file():
            path.unlink()
            return True
        return False