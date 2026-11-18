from pathlib import Path
from urllib.parse import urlparse
import requests


def get_size(url_or_path: str) -> int | None:
    # Local file
    path = Path(url_or_path)
    if path.is_file():
        return path.stat().st_size

    # HTTP/HTTPS URL
    parsed = urlparse(url_or_path)
    if parsed.scheme in ("http", "https"):
        try:
            response = requests.head(url_or_path, allow_redirects=True, timeout=10)
            response.raise_for_status()

            content_length = response.headers.get("Content-Length")
            return int(content_length) if content_length is not None else None
        except Exception:
            # HEAD request failed or no size available
            return None

    return None