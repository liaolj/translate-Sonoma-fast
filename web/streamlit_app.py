import os
import time
from contextlib import suppress
from typing import List

import requests
import streamlit as st


def get_input_root() -> str:
    return os.getenv("STREAMLIT_INPUT_ROOT", "test")


def get_output_root() -> str:
    return os.getenv("STREAMLIT_OUTPUT_ROOT", "output")


def get_status_poll_interval() -> float:
    return float(os.getenv("STREAMLIT_STATUS_INTERVAL", "1.0"))


def get_input_directories(base_dir: str | None = None) -> List[str]:
    """Return a list of sub-directories inside the given base directory."""

    base_dir = base_dir or get_input_root()

    if not os.path.exists(base_dir):
        return []

    return [
        os.path.join(base_dir, d)
        for d in sorted(os.listdir(base_dir))
        if os.path.isdir(os.path.join(base_dir, d))
    ]


def render_app() -> None:
    st.title("翻译GUI")

    input_root = get_input_root()
    output_root = get_output_root()
    poll_interval = get_status_poll_interval()

    input_dir_options = get_input_directories(input_root)

    if not input_dir_options:
        st.warning(
            "未找到任何输入目录，请在 test 文件夹下添加子目录或设置 STREAMLIT_INPUT_ROOT。"
        )
        st.stop()

    input_dir = st.selectbox("输入目录", options=input_dir_options)

    file_types = st.text_input("文件类型 (逗号分隔)", value="")

    if st.button("扫描文件"):
        params = {"dir_path": input_dir, "file_types": file_types}
        response = requests.get("http://localhost:8000/scan_dir", params=params)
        response.raise_for_status()
        data = response.json()
        st.write(f"找到 {data['total']} 个文件: {data['files']}")

    if st.button("开始翻译"):
        payload = {
            "input_dir": input_dir,
            "output_dir": output_root,
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
            with suppress(requests.HTTPError):
                status_response.raise_for_status()
            if status_response.ok:
                data = status_response.json()
                if "total_files" in data and total_files == 0:
                    total_files = data["total_files"]
                status_placeholder.write(data.get("message", ""))
                if total_files > 0 and data.get("progress") is not None:
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
            time.sleep(poll_interval)
            poll_count += 1
        if not completed:
            st.error("翻译超时或失败")

    st.sidebar.info("后端需运行: uvicorn web.app:app --reload")


if __name__ == "__main__":
    render_app()
