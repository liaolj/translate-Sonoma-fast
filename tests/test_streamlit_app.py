import os
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from web.streamlit_app import get_input_directory_options, normalise_file_types


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    monkeypatch.delenv("TRANSLATE_INPUT_BASE", raising=False)
    monkeypatch.delenv("TRANSLATE_BACKEND_URL", raising=False)


def test_get_input_directory_options_sorted(tmp_path: Path):
    (tmp_path / "b").mkdir()
    (tmp_path / "a").mkdir()

    options = get_input_directory_options(str(tmp_path))

    assert options == [os.path.join(str(tmp_path), "a"), os.path.join(str(tmp_path), "b")]


def test_get_input_directory_options_missing_dir(tmp_path: Path):
    missing = tmp_path / "missing"

    options = get_input_directory_options(str(missing))

    assert options == []


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("", ""),
        ("txt", "txt"),
        ("txt, md", "txt,md"),
        (" txt , ,md ,", "txt,md"),
    ],
)
def test_normalise_file_types(raw: str, expected: str):
    assert normalise_file_types(raw) == expected


def test_missing_input_directory_shows_warning(tmp_path: Path, monkeypatch):
    missing_dir = tmp_path / "not_there"
    monkeypatch.setenv("TRANSLATE_INPUT_BASE", str(missing_dir))

    app = AppTest.from_file("web/streamlit_app.py")
    app.run()

    assert any("未在“" in warning.value for warning in app.warning)


def test_selectbox_populated_with_directories(tmp_path: Path, monkeypatch):
    (tmp_path / "foo").mkdir()
    (tmp_path / "bar").mkdir()
    monkeypatch.setenv("TRANSLATE_INPUT_BASE", str(tmp_path))

    app = AppTest.from_file("web/streamlit_app.py")
    app.run()

    expected = [os.path.join(str(tmp_path), "bar"), os.path.join(str(tmp_path), "foo")]
    assert app.selectbox[0].options == expected

