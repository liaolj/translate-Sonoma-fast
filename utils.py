import os
from dotenv import load_dotenv

def load_env():
    load_dotenv()
    api_key = os.getenv('OPENROUTER_API_KEY')
    num_threads = int(os.getenv('NUM_THREADS', 5))
    model = os.getenv('MODEL', 'gpt-3.5-turbo')
    mock_mode = os.getenv('MOCK_MODE', 'false').lower() == 'true'
    global mock_mode_global
    mock_mode_global = mock_mode
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found in .env file")
    return api_key, num_threads, model, mock_mode
mock_mode_global = False

def filter_files_by_types(files_list, types_list):
    """过滤文件列表，只返回匹配指定扩展名的文件"""
    if not types_list or all(not t.strip() for t in types_list):
        print("警告: 文件类型列表为空，返回所有文件")
        return files_list
    
    filtered = []
    for file_path in files_list:
        _, ext = os.path.splitext(file_path)
        ext = ext.lstrip('.')  # 忽略点前缀
        if ext in types_list:
            filtered.append(file_path)
    return filtered