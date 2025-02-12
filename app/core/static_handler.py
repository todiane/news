#/app/core/static_handler.p
from pathlib import Path
from typing import Dict, Optional
from fastapi import HTTPException, Request
from fastapi.responses import FileResponse
from .static_security import StaticSecurity
import logging

logger = logging.getLogger(__name__)

class StaticHandler:
    def __init__(self, static_dir: str = "static"):
        self.static_dir = Path(static_dir)
        self.security = StaticSecurity()

    async def get_static_file(self, request: Request, file_path: str) -> FileResponse:
        """Handle static file requests with proper security and caching."""
        try:
            # Validate path
            if not self.security.validate_static_path(file_path):
                raise HTTPException(status_code=404, detail="File not found")

            full_path = self.static_dir / file_path
            if not full_path.exists():
                raise HTTPException(status_code=404, detail="File not found")

            # Get MIME type and cache headers
            mime_type = self.security.get_mime_type(file_path)
            file_type = self._get_file_type(file_path)
            cache_headers = self.security.get_cache_headers(file_type)

            return FileResponse(
                path=full_path,
                media_type=mime_type,
                headers=cache_headers
            )

        except Exception as e:
            logger.error(f"Error serving static file {file_path}: {str(e)}")
            raise HTTPException(status_code=404, detail="File not found")

    def _get_file_type(self, file_path: str) -> str:
        """Determine file type from path."""
        suffix = Path(file_path).suffix.lower()
        for file_type, extensions in self.security.ALLOWED_EXTENSIONS.items():
            if suffix in extensions:
                return file_type
        return "unknown"

    async def handle_static_error(self, request: Request, exc: Exception) -> Dict:
        """Handle static file errors."""
        logger.error(f"Static file error for {request.url.path}: {str(exc)}")
        return {
            "detail": "Static file not found",
            "path": request.url.path
        }

static_handler = StaticHandler()
