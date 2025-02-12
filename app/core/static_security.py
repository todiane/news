# /app/core/static_security.py

from typing import Dict, List
from pathlib import Path

class StaticSecurity:
    ALLOWED_EXTENSIONS = {
        'css': ['.css', '.min.css'],
        'js': ['.js', '.min.js'],
        'images': ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp'],
        'fonts': ['.woff', '.woff2', '.ttf', '.eot'],
        'icons': ['.ico'],
    }

    MIME_TYPES = {
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.webp': 'image/webp',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
        '.ttf': 'font/ttf',
        '.eot': 'application/vnd.ms-fontobject',
        '.ico': 'image/x-icon',
    }

    @classmethod
    def is_allowed_file(cls, filename: str) -> bool:
        """Check if file extension is allowed."""
        suffix = Path(filename).suffix.lower()
        return any(suffix in exts for exts in cls.ALLOWED_EXTENSIONS.values())

    @classmethod
    def get_mime_type(cls, filename: str) -> str:
        """Get MIME type for file."""
        suffix = Path(filename).suffix.lower()
        return cls.MIME_TYPES.get(suffix, 'application/octet-stream')

    @classmethod
    def get_cache_headers(cls, file_type: str) -> Dict[str, str]:
        """Get cache headers based on file type."""
        cache_settings = {
            'css': 'public, max-age=31536000',  # 1 year
            'js': 'public, max-age=31536000',
            'images': 'public, max-age=86400',   # 1 day
            'fonts': 'public, max-age=31536000',
            'icons': 'public, max-age=86400',
        }
        return {"Cache-Control": cache_settings.get(file_type, 'no-store')}

    @classmethod
    def validate_static_path(cls, path: str) -> bool:
        """Validate static file path for security."""
        path_obj = Path(path)
        try:
            # Prevent path traversal
            path_obj.resolve().relative_to(Path("static"))
            return True
        except (ValueError, RuntimeError):
            return False