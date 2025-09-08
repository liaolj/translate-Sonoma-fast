from fastapi import FastAPI, HTTPException, WebSocket, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
import os
from utils import load_env, filter_files_by_types
from parallel_translator import translate_parallel
from pathlib import Path
from collections import deque

app = FastAPI()

progress_queue = deque()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

class TranslateRequest(BaseModel):
    input_dir: str = 'test'
    output_dir: str = 'output'
    target_lang: str = 'zh'
    file_types: str = ''
    model: str | None = None

def secure_path(path: str, allowed_base: str):
    real_path = os.path.realpath(path)
    base_real = os.path.realpath(allowed_base)
    if not real_path.startswith(base_real):
        raise HTTPException(status_code=400, detail="Invalid path")
    return path

def secure_path_dependency(base_dir: str):
    def dependency(path: str):
        return secure_path(path, base_dir)
    return dependency

def validate_translate_request(request: TranslateRequest):
    secure_path(request.input_dir, 'test')
    secure_path(request.output_dir, 'output')
    return request

@app.get("/scan_dir")
@limiter.limit("5/minute")
def scan_dir(request: Request, dir_path: str = "test", file_types: str = ""):
    dir_path = secure_path(dir_path, 'test')
    file_types_list = [t.strip() for t in file_types.split(',') if t.strip()]
    files = []
    for root, dirs, filenames in os.walk(dir_path):
        for filename in filenames:
            fullpath = os.path.join(root, filename)
            relpath = os.path.relpath(fullpath, dir_path)
            files.append(relpath)
    filtered_files = filter_files_by_types(files, file_types_list)
    return {"files": filtered_files, "total": len(filtered_files)}

@app.post("/translate")
async def translate(background_tasks: BackgroundTasks, request: TranslateRequest = Depends(validate_translate_request)):
    config = load_env()
    api_key, num_threads, default_model, mock_mode = config
    model = request.model or default_model
    file_types_list = [t.strip() for t in request.file_types.split(',') if t.strip()]
    paths = []
    for root, dirs, filenames in os.walk(request.input_dir):
        for filename in filenames:
            fullpath = os.path.join(root, filename)
            paths.append(fullpath)
    paths = filter_files_by_types(paths, file_types_list)
    total_files = len(paths)
    progress_queue.clear()
    progress_queue.append({"progress": 0, "total_files": total_files, "message": f"找到 {total_files} 个文件，开始翻译"})
    background_tasks.add_task(run_translation, paths, api_key, request.target_lang, num_threads, model, request.file_types, mock_mode, request.input_dir, request.output_dir)
    return {"status": "started"}

def run_translation(paths, api_key, target_lang, num_threads, model, file_types, mock_mode, input_dir, output_dir):
    translated_files = []
    errors = []
    total_files = len(paths)
    try:
        results = translate_parallel(paths, api_key, target_lang, num_threads, model, file_types, mock_mode, progress_queue=progress_queue)
        for i, (path, translated_content) in enumerate(results.items(), 1):
            try:
                relpath = Path(path).relative_to(input_dir)
                subdir = Path(input_dir).relative_to('test')
                output_filename = f"{relpath.stem}_translated{relpath.suffix}"
                output_path = Path(output_dir) / subdir / relpath.parent / output_filename
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(translated_content)
                progress = (i / total_files) * 100
                percent = progress
                progress_queue.append({"progress": progress, "message": f'进度: {i}/{total_files} 文件完成 ({percent:.1f}%)'})
                translated_files.append(str(output_path))
            except Exception as e:
                progress = (i / total_files) * 100
                percent = progress
                progress_queue.append({"progress": progress, "error": f"保存 {path} 失败: {str(e)} ({percent:.1f}%)"})
                errors.append(f"Error processing {path}: {str(e)}")
        progress_queue.append({"progress": 100, "status": "completed", "message": "翻译完成", "translated_files": translated_files, "errors": errors})
    except Exception as e:
        progress_queue.append({"progress": None, "status": "error", "error": str(e)})
        errors.append(str(e))


@app.get("/status")
def get_status():
    if progress_queue:
        last = progress_queue[-1]
        return last
    else:
        return {"progress": 0}

@app.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            if progress_queue:
                data = progress_queue.popleft()
                await websocket.send_json(data)
            else:
                await websocket.receive_text()
    except Exception:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)