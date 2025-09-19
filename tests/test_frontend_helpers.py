from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from web.frontend_helpers import list_input_directories, progress_to_fraction


def test_list_input_directories_returns_base_when_missing(tmp_path: Path):
    missing_dir = tmp_path / "not_there"
    assert list_input_directories(str(missing_dir)) == [str(missing_dir)]


def test_list_input_directories_returns_subdirectories(tmp_path: Path):
    base = tmp_path / "test"
    (base / "a").mkdir(parents=True)
    (base / "b").mkdir()

    options = list_input_directories(str(base))

    assert options == [str(base / "a"), str(base / "b")]


@pytest.mark.parametrize(
    "progress, expected",
    [
        (None, None),
        (0, 0.0),
        (50, 0.5),
        (100, 1.0),
        (150, 1.0),
        (-10, 0.0),
    ],
)
def test_progress_to_fraction(progress, expected):
    assert progress_to_fraction(progress) == expected

