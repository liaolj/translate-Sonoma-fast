# Sonoma 翻译工具

## 项目概述

Sonoma 是一个高效的文件翻译工具，使用 OpenAI GPT 模型（如 gpt-3.5-turbo）进行文本翻译。支持并行处理多个文件、CLI 命令行界面、FastAPI Web API 和 Streamlit Web UI。适用于批量翻译文本文件，支持中文等目标语言，包含错误重试机制和 mock 模式测试。

## 文件结构

- **main.py**: CLI 入口脚本，处理文件路径参数，调用并行翻译函数，支持临时文件处理和结果输出。
- **parallel_translator.py**: 并行翻译模块，使用 `concurrent.futures.ThreadPoolExecutor` 处理多个文件，支持多线程、文件类型过滤、重试机制和 mock 模式。
- **translator.py**: 核心翻译函数 `translate_text`，调用 OpenAI API 进行单个文本翻译，支持重试和 mock 模式。
- **utils.py**: 实用工具函数，包括加载环境变量、处理文件路径、读取文件内容等辅助功能。
- **web/app.py**: FastAPI Web 应用，提供 `/translate` 端点，支持文件上传和翻译请求，集成限流（slowapi）和 CORS。
- **web/streamlit_app.py**: Streamlit Web UI，提供文件上传、目标语言选择和翻译结果显示界面。
- **requirements.txt**: 项目依赖列表。
- **其他**: `.env` 用于存储 OpenAI API 密钥，`.gitignore` 用于忽略虚拟环境和临时文件，`test_gui/` 用于测试文件。

## 核心功能描述

- **翻译功能**: 使用 OpenAI API 将文本翻译到指定语言（如中文），支持模型选择和重试机制。
- **并行处理**: 支持多线程并行翻译多个文件，提高效率。
- **Web 接口**:
  - FastAPI: RESTful API，支持 POST `/translate` 上传文件并获取翻译结果。
  - Streamlit: 交互式 UI，支持文件上传和实时翻译显示。
- **错误处理**: API 调用失败时自动重试，支持 mock 模式模拟翻译。
- **文件支持**: 读取 txt、md 等文本文件，处理编码问题。

## 依赖安装

1. 克隆或下载项目。
2. 创建虚拟环境：`python -m venv venv`。
3. 激活虚拟环境：`source venv/bin/activate` (Linux/Mac) 或 `venv\Scripts\activate` (Windows)。
4. 安装依赖：`pip install -r requirements.txt`。
   - 关键依赖：`requests` (API 调用)、`python-dotenv` (环境变量)、`fastapi[all]` 和 `uvicorn` (Web API)、`streamlit` (UI)、`python-multipart` (文件上传)、`slowapi` (限流)。

5. 配置 `.env` 文件，添加 `OPENAI_API_KEY=your_api_key`。

## 使用方法

### CLI 使用
运行：`python main.py file1.txt file2.md --target_lang zh --api_key your_key --num_threads 4 --model gpt-3.5-turbo`

- 参数：
  - `file_paths`: 输入文件路径列表。
  - `--target_lang`: 目标语言 (默认 'zh')。
  - `--api_key`: OpenAI API 密钥。
  - `--num_threads`: 线程数 (默认 4)。
  - `--model`: 模型名称 (默认 'gpt-3.5-turbo')。
  - `--mock_mode`: 模拟模式 (默认 False)。

输出翻译结果到控制台或文件。

### FastAPI Web API
- 运行服务器：`uvicorn web.app:app --reload --port 8000`。
- API 端点：POST `/translate`，body 包含 `files` (文件列表)、`target_lang`、`model` 等。
- 示例：使用 curl 或 Postman 上传文件进行翻译。

### Streamlit UI
- 运行：`streamlit run web/streamlit_app.py`。
- 在浏览器打开 localhost:8501，上传文件，选择语言，点击翻译。

## 运行说明

- 确保 OpenAI API 密钥有效且有足够配额。
- 项目运行在 Python 3.8+ 环境。
- 对于大文件或多文件，调整 `--num_threads` 以优化性能。
- 测试：使用 `test_gui/sample.txt` 作为示例文件。
- 临时文件处理：支持 /tmp/ 路径下的临时文件自动清理。
- 限流：FastAPI 接口有速率限制，避免 API 滥用。

此工具适合开发者快速翻译代码注释、文档等，支持扩展到更多语言模型。