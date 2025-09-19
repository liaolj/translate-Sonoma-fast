import os
import time
from pathlib import Path
from typing import Iterable, List

import requests
import streamlit as st


BASE_INPUT_ROOT = Path("test")


def list_input_directories(base_dir: Path) -> List[Path]:
    """Return directories inside ``base_dir`` sorted alphabetically.

    The function silently returns an empty list when the directory does not
    exist, which keeps the UI responsive even on a fresh checkout where the
    ``test`` folder has not been created yet.
    """

    if not base_dir.exists() or not base_dir.is_dir():
        return []
    return sorted([path for path in base_dir.iterdir() if path.is_dir()])


def to_input_dir_options(directories: Iterable[Path]) -> List[str]:
    """Convert a collection of Path objects to string options for the UI."""

    return [str(path) for path in directories]


def render_translation_controls(input_dir: str, file_types: str) -> None:
    """Render scan/translate buttons and handle their callbacks."""

    if st.button("扫描文件", disabled=not input_dir):
        params = {"dir_path": input_dir, "file_types": file_types}
        response = requests.get("http://localhost:8000/scan_dir", params=params)
        response.raise_for_status()
        data = response.json()
        st.write(f"找到 {data['total']} 个文件: {data['files']}")

    if st.button("开始翻译", disabled=not input_dir):
        payload = {
            "input_dir": input_dir,
            "output_dir": "output",
            "target_lang": "zh",
            "file_types": file_types,
            "model": None,
        }
        response = requests.post("http://localhost:8000/translate", json=payload)
        response.raise_for_status()
        progress_placeholder = st.empty()
        status_placeholder = st.empty()
        total_files = 0
        poll_count = 0
        max_polls = 300
        completed = False
        while poll_count < max_polls:
            status_response = requests.get("http://localhost:8000/status")
            if status_response.ok:
                data = status_response.json()
                if "total_files" in data and total_files == 0:
                    total_files = data["total_files"]
                status_placeholder.write(data.get("message", ""))
                if total_files > 1 and data.get("progress") is not None:
                    progress_placeholder.progress(min(data["progress"] / 100, 1.0))
                if "error" in data:
                    st.error(f"错误: {data['error']}")
                    completed = True
                    break
                if data.get("progress") == 100 and data.get("status") == "completed":
                    st.success("翻译完成！")
                    if "translated_files" in data:
                        st.write("翻译文件: ", data["translated_files"])
                    if data.get("errors"):
                        st.warning("警告: ", data["errors"])
                    completed = True
                    break
            time.sleep(1)
            poll_count += 1
        if not completed:
            st.error("翻译超时或失败")


def main() -> None:
    st.title("翻译GUI")

    subdirs = list_input_directories(BASE_INPUT_ROOT)
    input_dir_options = to_input_dir_options(subdirs)

    input_dir: str = ""
    if input_dir_options:
        input_dir = st.selectbox("输入目录", options=input_dir_options)
    else:
        st.warning(
            "未在 test 目录下找到可用的子目录，请先创建待翻译文件夹。"
        )
        input_dir = st.text_input("输入目录", value=str(BASE_INPUT_ROOT))

    file_types = st.text_input("文件类型 (逗号分隔)", value="")

    render_translation_controls(input_dir.strip(), file_types.strip())

    st.sidebar.info("后端需运行: uvicorn web.app:app --reload")


if __name__ == "__main__":
    main()