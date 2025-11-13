from typing import Any
from typing import Iterator

from fastapi import UploadFile


def sanitize_log_value(value: Any) -> str:
    """Ensure values logged are single-line strings to keep logs tidy."""
    return str(value).replace('\n', '').replace('\r', '')


def iter_file_lines(upload_file: UploadFile) -> Iterator[str]:
    """Yield decoded lines from an UploadFile, line-by-line, without extra buffering.

    Preserves the previous behavior that iterated upload_file.file directly (bytes per line).
    """
    for raw in upload_file.file:
        yield raw.decode('utf-8', errors='replace')
