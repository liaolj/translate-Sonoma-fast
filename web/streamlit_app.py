import streamlit as st
import requests
import json
import time
import os

st.title("翻译GUI")

subdirs = [d for d in os.listdir('test') if os.path.isdir(os.path.join('test', d))]
input_dir_options = [f"test/{d}" for d in subdirs]
input_dir = st.selectbox("输入目录", options=input_dir_options)

file_types = st.text_input("文件类型 (逗号分隔)", value="")

if st.button("扫描文件"):
    params = {"dir_path": input_dir, "file_types": file_types}
    response = requests.get("http://localhost:8000/scan_dir", params=params)
    response.raise_for_status()
    data = response.json()
    st.write(f"找到 {data['total']} 个文件: {data['files']}")

if st.button("开始翻译"):
    payload = {"input_dir": input_dir, "output_dir": "output", "target_lang": "zh", "file_types": file_types, "model": None}
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

st.sidebar.info("后端需运行: uvicorn web.app:app --reload")

if __name__ == "__main__":
    pass