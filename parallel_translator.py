import concurrent.futures
import time
from typing import List
from translator import translate_text, TranslationFailedError

def translate_parallel(file_paths: List[str], api_key: str, target_lang: str, num_threads: int, model: str = "gpt-3.5-turbo", file_types: List[str] | None = None, mock_mode: bool = False, total_files: int = 0, progress_queue=None) -> dict:
    """
    并行翻译多个文件，每个文件作为独立单元进行翻译。
    """
    import os
    
    from utils import mock_mode_global
    mock_mode = mock_mode or mock_mode_global
    total_files = len(file_paths) if total_files == 0 else total_files
    results = {}
    
    def translate_file_with_retry(path, content, max_retries=5):
        for attempt in range(max_retries):
            print(f"文件 {path} API call attempt {attempt + 1}/{max_retries}")
            try:
                translated = translate_text(content, api_key, target_lang, model, mock_mode=mock_mode)
                return translated
            except TranslationFailedError as e:
                print(f"文件 {path} 翻译失败: {e}")
                raise
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** (attempt + 1)
                    print(f"文件 {path} 翻译重试 {attempt + 1}/{max_retries}，等待 {wait_time} 秒: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"文件 {path} 翻译失败 after {max_retries} attempts: {e}")
                    raise TranslationFailedError(f"文件 {path} 翻译失败 after {max_retries} attempts: {e}")
    
    def translate_file(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            if not content.strip():
                return path, content
            translated = translate_file_with_retry(path, content)
            return path, translated
        except TranslationFailedError as e:
            print(f"文件 {path} 翻译失败，标记整个翻译失败: {e}")
            raise
        except Exception as e:
            print(f"处理文件 {path} 时出错: {e}")
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except:
                content = ""
            return path, content
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_path = {executor.submit(translate_file, path): path for path in file_paths}
        completed_count = 0
        for future in concurrent.futures.as_completed(future_to_path):
            path, translated_content = future.result()
            results[path] = translated_content
            completed_count += 1
            if total_files > 1:
                percentage = (completed_count / total_files * 100)
                print(f"进度: {completed_count}/{total_files} 文件完成 ({percentage:.1f}%)")
                if progress_queue:
                    progress_queue.append({
                        'progress': percentage,
                        'message': f'进度: {completed_count}/{total_files} 文件完成 ({percentage:.1f}%)'
                    })
    
    return results