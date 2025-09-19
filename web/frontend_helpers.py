"""Utility helpers for the Streamlit front-end."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional


def list_input_directories(base_path: str = "test") -> List[str]:
    """Return available input directories under ``base_path``.

    Streamlit renders a ``selectbox`` for users to pick an input directory. If
    the ``test`` folder does not contain sub-directories the original
    implementation would result in an empty options list and Streamlit raises a
    ``StreamlitAPIException``.  The helper guarantees that at least the base
    folder itself is returned so the UI always has something to show.
    """

    base = Path(base_path)
    if not base.exists():
        return [base_path]

    subdirs: Iterable[Path] = (p for p in base.iterdir() if p.is_dir())
    options = [str(base / subdir.name) for subdir in sorted(subdirs)]
    return options or [base_path]


def progress_to_fraction(progress: Optional[float]) -> Optional[float]:
    """Convert a percentage value from the API to a Streamlit progress fraction."""

    if progress is None:
        return None
    return max(0.0, min(progress / 100.0, 1.0))

