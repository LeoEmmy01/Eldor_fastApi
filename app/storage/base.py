from abc import ABC, abstractmethod
from fastapi import UploadFile

class BaseStorage(ABC):
    
    @abstractmethod
    async def save_file(self, file: UploadFile, folder: str) -> str:
        """Saves an uploaded file and returns its reference/path or URL."""
        pass
    
    @abstractmethod
    async def get_file(self, file_path: str) -> str:
        """Retrieves a file's content given its reference/path or URL."""
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Deletes a file given its reference/path or URL."""
        pass