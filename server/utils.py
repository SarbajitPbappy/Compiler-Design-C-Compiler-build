from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from contextlib import contextmanager


@contextmanager
def session_workspace(prefix: str = "cpp"):
    session_id = f"{prefix}-{uuid.uuid4().hex[:12]}"
    base_dir = tempfile.mkdtemp(prefix=session_id + "-")
    try:
        yield base_dir
    finally:
        try:
            shutil.rmtree(base_dir, ignore_errors=True)
        except Exception:
            pass


def write_text_file(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
