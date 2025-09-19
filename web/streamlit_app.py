from __future__ import annotations

import os
import time
from typing import List

import requests
import streamlit as st


DEFAULT_INPUT_BASE = os.environ.get("TRANSLATE_INPUT_BASE", "test")
DEFAULT_BACKEND_URL = os.environ.get("TRANSLATE_BACKEND_URL", "http://localhost:8000")


def _sorted_subdirectories(base_dir: str) -> List[str]:
    """Yield absolute paths of sub-directories directly under *base_dir*."""

    try:
        entries = os.listdir(base_dir)
    except FileNotFoundError:
        return []

    subdirs: List[str] = []
    for entry in entries:
        full_path = os.path.join(base_dir, entry)
        if os.path.isdir(full_path):
            subdirs.append(full_path)
    return sorted(subdirs)


def get_input_directory_options(base_dir: str) -> List[str]:
    """Return the available input directories for the dropdown."""

    return list(_sorted_subdirectories(base_dir))


def normalise_file_types(raw_value: str) -> str:
    """Collapse the free text input into a normalised comma separated string."""

    parts = [segment.strip() for segment in raw_value.split(",") if segment.strip()]
    return ",".join(parts)


def scan_directory(backend_url: str, input_dir: str, file_types: str) -> dict:
    params = {"dir_path": input_dir, "file_types": file_types}
    response = requests.get(f"{backend_url}/scan_dir", params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def start_translation(backend_url: str, payload: dict) -> None:
    response = requests.post(f"{backend_url}/translate", json=payload, timeout=10)
    response.raise_for_status()


def poll_translation_status(backend_url: str, progress_placeholder, status_placeholder) -> None:
    total_files = 0
    poll_count = 0
    max_polls = 300

    while poll_count < max_polls:
        try:
            status_response = requests.get(f"{backend_url}/status", timeout=10)
        except requests.RequestException as exc:
            status_placeholder.error(f"状态获取失败: {exc}")
            break

        if status_response.ok:
            data = status_response.json()
            if "total_files" in data and total_files == 0:
                total_files = data["total_files"]
            status_placeholder.write(data.get("message", ""))
            if total_files > 0 and data.get("progress") is not None:
                progress_value = max(0.0, min(data["progress"] / 100, 1.0))
                progress_placeholder.progress(progress_value)
            if "error" in data:
                st.error(f"错误: {data['error']}")
                break
            if data.get("progress") == 100 and data.get("status") == "completed":
                st.success("翻译完成！")
                if "translated_files" in data:
                    st.write("翻译文件: ", data["translated_files"])
                if data.get("errors"):
                    st.warning("警告: ", data["errors"])
                break
        time.sleep(1)
        poll_count += 1
    else:
        st.error("翻译超时或失败")


def render_input_directory_selector(base_dir: str) -> str:
    input_dir_options = get_input_directory_options(base_dir)
    if input_dir_options:
        return st.selectbox("输入目录", options=input_dir_options)

    st.warning(f"未在“{base_dir}”下找到子目录，请确认路径是否正确。")
    return st.text_input("输入目录", value=base_dir)


def main(base_input_dir: str | None = None, backend_url: str | None = None) -> None:
    base_input_dir = base_input_dir or DEFAULT_INPUT_BASE
    backend_url = backend_url or DEFAULT_BACKEND_URL

    st.title("翻译GUI")

    input_dir = render_input_directory_selector(base_input_dir)

    raw_file_types = st.text_input("文件类型 (逗号分隔)", value="")
    file_types = normalise_file_types(raw_file_types)

    if st.button("扫描文件"):
        if not os.path.isdir(input_dir):
            st.error("输入目录不存在，无法扫描。")
        else:
            try:
                data = scan_directory(backend_url, input_dir, file_types)
            except requests.RequestException as exc:
                st.error(f"扫描失败: {exc}")
            else:
                st.write(f"找到 {data['total']} 个文件: {data['files']}")

    if st.button("开始翻译"):
        if not os.path.isdir(input_dir):
            st.error("输入目录不存在，无法翻译。")
        else:
            payload = {
                "input_dir": input_dir,
                "output_dir": "output",
                "target_lang": "zh",
                "file_types": file_types,
                "model": None,
            }
            try:
                start_translation(backend_url, payload)
            except requests.RequestException as exc:
                st.error(f"翻译请求失败: {exc}")
            else:
                progress_placeholder = st.empty()
                status_placeholder = st.empty()
                poll_translation_status(backend_url, progress_placeholder, status_placeholder)

    st.sidebar.info("后端需运行: uvicorn web.app:app --reload")


if __name__ == "__main__":
    main()
