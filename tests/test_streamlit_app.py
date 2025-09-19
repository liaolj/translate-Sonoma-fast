import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from web.streamlit_app import list_input_directories, to_input_dir_options


def test_list_input_directories_returns_empty_when_missing(tmp_path: Path) -> None:
    missing_dir = tmp_path / "missing"
    assert list_input_directories(missing_dir) == []


def test_list_input_directories_filters_files(tmp_path: Path) -> None:
    (tmp_path / "folder_a").mkdir()
    (tmp_path / "folder_b").mkdir()
    (tmp_path / "file.txt").write_text("data", encoding="utf-8")

    directories = list_input_directories(tmp_path)

    assert directories == [tmp_path / "folder_a", tmp_path / "folder_b"]


def test_to_input_dir_options_returns_string_paths(tmp_path: Path) -> None:
    dirs = [tmp_path / "a", tmp_path / "b"]
    for d in dirs:
        d.mkdir()

    options = to_input_dir_options(list_input_directories(tmp_path))

    assert options == [str(tmp_path / "a"), str(tmp_path / "b")]
