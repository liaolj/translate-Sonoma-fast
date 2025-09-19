from __future__ import annotations

import os
from typing import Any, Dict
from streamlit.testing.v1 import AppTest


class DummyResponse:
    def __init__(self, payload: Dict[str, Any], status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def json(self) -> Dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    @property
    def ok(self) -> bool:
        return self.status_code < 400


def test_app_warns_when_no_input_dirs(monkeypatch, tmp_path):
    monkeypatch.setenv("STREAMLIT_INPUT_ROOT", str(tmp_path / "inputs"))
    apptest = AppTest.from_file("web/streamlit_app.py")
    apptest.run()
    warnings = [message.value for message in apptest.warning]
    assert any("未找到任何输入目录" in message for message in warnings)


def test_scan_and_translate_flow(monkeypatch, tmp_path):
    input_root = tmp_path / "inputs"
    output_root = tmp_path / "outputs"
    (input_root / "demo").mkdir(parents=True)

    monkeypatch.setenv("STREAMLIT_INPUT_ROOT", str(input_root))
    monkeypatch.setenv("STREAMLIT_OUTPUT_ROOT", str(output_root))
    monkeypatch.setenv("STREAMLIT_STATUS_INTERVAL", "0")

    call_log: Dict[str, Any] = {"scan_params": None, "translate_payload": None, "status_calls": 0}

    def fake_get(url: str, params: Dict[str, Any] | None = None):
        if url.endswith("/scan_dir"):
            call_log["scan_params"] = params
            return DummyResponse({"files": ["demo/file.txt"], "total": 1})
        if url.endswith("/status"):
            call_log["status_calls"] += 1
            return DummyResponse(
                {
                    "progress": 100,
                    "status": "completed",
                    "message": "翻译完成",
                    "translated_files": [str(output_root / "demo" / "file_translated.txt")],
                }
            )
        raise AssertionError(f"Unexpected GET {url}")

    def fake_post(url: str, json: Dict[str, Any] | None = None):
        if url.endswith("/translate"):
            call_log["translate_payload"] = json
            return DummyResponse({"status": "started"})
        raise AssertionError(f"Unexpected POST {url}")

    monkeypatch.setattr("requests.get", fake_get)
    monkeypatch.setattr("requests.post", fake_post)

    apptest = AppTest.from_file("web/streamlit_app.py")
    apptest.run()

    # 执行扫描
    apptest.button[0].click().run()

    assert call_log["scan_params"] == {"dir_path": os.path.join(str(input_root), "demo"), "file_types": ""}
    assert any("找到 1 个文件" in message.value for message in apptest.markdown)

    # 执行翻译
    apptest.button[1].click().run()

    assert call_log["translate_payload"] == {
        "input_dir": os.path.join(str(input_root), "demo"),
        "output_dir": str(output_root),
        "target_lang": "zh",
        "file_types": "",
        "model": None,
    }
    assert call_log["status_calls"] >= 1
    assert any("翻译完成！" in message.value for message in apptest.success)

