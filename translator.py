import requests
import time
from typing import Optional

class TranslationFailedError(Exception):
    pass

def translate_text(text: str, api_key: str, target_lang: str, model: str = "gpt-3.5-turbo", max_retries: int = 5, mock_mode: bool = False) -> str:
    """
    使用OpenRouter API翻译文本，包含重试机制。
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    if mock_mode:
        # 简单mock翻译
        if 'Hello' in text:
            return text.replace('Hello', '你好')
        # 其他简单替换或fallback
        return text + " (mock translated)"
    
    prompt = f"Translate the following English text to Chinese: {text}"
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    for attempt in range(max_retries):
        print(f"API call attempt {attempt + 1}/{max_retries}")
        try:
            response = requests.post(url, json=payload, headers=headers)
            print(f"Response status: {response.status_code}")
            if response.status_code == 429:
                wait_time = 2 ** (attempt + 1)
                print(f"API速率限制，等待 {wait_time} 秒后重试 (尝试 {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            response.raise_for_status()
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0]['message']['content'].strip()
            else:
                raise ValueError("Invalid response from API")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print("API密钥无效，请检查OPENROUTER_API_KEY")
                raise TranslationFailedError("Invalid API key")
            elif attempt < max_retries - 1:
                print(f"HTTP错误: {str(e)}，重试...")
                time.sleep(2 ** (attempt + 1))
                continue
            else:
                print(f"翻译失败 after {max_retries} attempts: {str(e)}")
                raise TranslationFailedError(f"HTTP error after {max_retries} attempts: {str(e)}")
        except (requests.exceptions.RequestException, ValueError, KeyError) as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            else:
                print(f"翻译失败 after {max_retries} attempts: {str(e)}")
                raise TranslationFailedError(f"Request error after {max_retries} attempts: {str(e)}")
    
    print("翻译失败：达到最大重试次数")
    raise TranslationFailedError("Max retries exceeded")