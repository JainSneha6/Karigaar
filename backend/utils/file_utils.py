# utils/file_utils.py
import os
import tempfile
from typing import Optional


def write_bytes_to_tempfile(data: bytes, suffix: str = "") -> str:
    """
    Write `data` bytes to a temporary file and return the path.
    Caller is responsible for removing the file when done.
    """
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
    except Exception:
        # if writing fails ensure file is removed
        try:
            os.remove(path)
        except Exception:
            pass
        raise
    return path


def safe_remove(path: Optional[str]) -> None:
    """Remove a file if it exists; ignore errors."""
    if not path:
        return
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
