#!/usr/bin/env python3
import argparse
import sys
from utils import load_env
from parallel_translator import translate_parallel

def main():
    parser = argparse.ArgumentParser(description='翻译CLI程序，使用OpenRouter API')
    parser.add_argument('--file-types', type=str, help='文件类型列表（逗号分隔，如 txt,md）')
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument('--input', '-i', type=str, nargs='+', help='输入文件路径列表（多个文件）')
    input_group.add_argument('--input-dir', type=str, help='输入目录路径（翻译目录下所有.txt文件）')
    parser.add_argument('--output', '-o', type=str, help='单个输出文件路径（仅限单文件输入）')
    parser.add_argument('--output-dir', type=str, help='输出目录路径（用于多文件输入）')
    parser.add_argument('--target-lang', '-t', type=str, default='zh', help='目标语言（默认: zh）')
    parser.add_argument('--input-file', type=str, default='test_input.txt', help='输入文件路径（默认: test_input.txt）')
    parser.add_argument('--model', type=str, help='模型名称（覆盖 .env 中的 model）')
    parser.add_argument('text', nargs='*', help='要翻译的文本（如果未指定输入文件，则使用此参数）')
    
    args = parser.parse_args()
    
    # 加载环境变量
    import os
    api_key, num_threads, model, mock_mode = load_env()
    from utils import mock_mode_global
    mock_mode_global = mock_mode
    file_types = None
    print(f"调试: args.file_types value: {repr(args.file_types)}")  # 临时调试
    if args.file_types is not None:
        file_types = [t.strip() for t in args.file_types.split(',') if t.strip()]
        print(f"使用file_types: {file_types}")
        if not file_types:
            print(f"无效文件类型: '{args.file_types}'")
            sys.exit(1)
    if file_types is None:
        env_types = os.getenv('FILE_TYPES', '').split(',')
        file_types = [t.strip() for t in env_types if t.strip()]
        print(f"使用file_types: {file_types}")
        if not file_types:
            print("无效文件类型: '' (从.env加载)")
            sys.exit(1)
    if args.model:
        model = args.model
    
    # 确定输入文件列表
    file_paths = []
    if args.input_dir:
        if not os.path.exists(args.input_dir):
            print(f"错误: 输入目录 {args.input_dir} 不存在")
            sys.exit(1)
        # 递归遍历目录，收集所有匹配文件类型
        file_paths = []
        for root, dirs, files in os.walk(args.input_dir):
            for file in files:
                if file_types and any(file.endswith('.' + ft) for ft in file_types):
                    file_path = os.path.join(root, file)
                    file_paths.append(file_path)
        print(f"递归找到匹配文件: {len(file_paths)} 个")
    elif args.input:
        file_paths = args.input
    elif args.input_file:
        if not os.path.exists(args.input_file):
            print(f"错误: 输入文件 {args.input_file} 不存在")
            sys.exit(1)
        file_paths = [args.input_file]
        print(f"过滤前文件路径: {file_paths}")  # 调试打印
        if not file_paths:
            print(f"警告: 目录 {args.input_dir} 中没有找到文件")
            sys.exit(0)
    elif args.text:
        input_text = ' '.join(args.text)
        # 对于文本输入，创建临时文件处理
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp:
            tmp.write(input_text)
            file_paths = [tmp.name]
    else:
        input_text = sys.stdin.read()
        if input_text.strip():
            # 对于 stdin，创建临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp:
                tmp.write(input_text)
                file_paths = [tmp.name]
        else:
            print("警告: 输入为空")
            sys.exit(0)
    
    if not file_paths:
        print("警告: 输入为空")
        sys.exit(0)
    
    from utils import filter_files_by_types
    file_paths = filter_files_by_types(file_paths, file_types)
    print(f"过滤后文件路径: {file_paths}")  # 调试打印过滤结果
    
    if not file_paths:
        print("无匹配文件")
        sys.exit(0)
    
    # 初始化结果字典
    translation_results = {}
    
    # 并行翻译（统一处理单/多文件）
    print("开始翻译...")
    if len(file_paths) == 1:
        # 单文件模式
        with open(file_paths[0], 'r', encoding='utf-8') as f:
            input_text = f.read()
        from translator import translate_text
        try:
            translated_text = translate_text(input_text, api_key, args.target_lang, model, mock_mode=mock_mode_global)
        except Exception as e:
            print(f"翻译单文件时出错: {e}。使用原始内容。")
            translated_text = input_text
        translation_results[file_paths[0]] = translated_text
    else:
        translation_results = translate_parallel(file_paths, api_key, args.target_lang, num_threads, model, file_types, mock_mode_global, len(file_paths))
    
    # 统一写入输出（单/多文件）
    output_dir = args.output_dir or 'translated/'
    os.makedirs(output_dir, exist_ok=True)
    if len(file_paths) == 1 and args.output:
        # 单文件指定输出路径
        input_path = file_paths[0]
        translated_content = translation_results.get(input_path, '')
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(translated_content)
            print(f"翻译结果已保存到: {args.output}")
        except IOError:
            print(f"错误: 无法写入输出文件 {args.output}")
            sys.exit(1)
    elif len(file_paths) == 1:
        # 单文件使用output_dir
        input_path = file_paths[0]
        translated_content = translation_results.get(input_path, '')
        base_name = os.path.basename(input_path)
        if args.input_dir:
            # 计算相对路径，保持目录结构
            rel_path = os.path.relpath(input_path, args.input_dir)
            input_dir_basename = os.path.basename(args.input_dir)
            rel_dir = os.path.dirname(f"{input_dir_basename}/{rel_path}")
            name, ext = os.path.splitext(base_name)
            translated_name = f"{name}_translated{ext}"
            if rel_dir == '.':
                output_path = os.path.join(output_dir, translated_name)
            else:
                output_subdir = os.path.join(output_dir, rel_dir)
                os.makedirs(output_subdir, exist_ok=True)
                output_path = os.path.join(output_subdir, translated_name)
        else:
            name, ext = os.path.splitext(base_name)
            output_path = os.path.join(output_dir, f"{name}_translated{ext}")
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(translated_content)
            print(f"翻译结果已保存到: {output_path}")
        except IOError:
            print(f"错误: 无法写入输出文件 {output_path}")
            sys.exit(1)
    else:
        # 多文件使用output_dir，保持目录结构
        for input_path, translated_content in translation_results.items():
            if input_path.startswith('/tmp/'):  # 临时文件
                base_name = os.path.basename(input_path)
                output_path = os.path.join(output_dir, f"translated_{base_name}")
            else:
                # 计算相对路径，保持目录结构
                rel_path = os.path.relpath(input_path, args.input_dir)
                input_dir_basename = os.path.basename(args.input_dir)
                rel_dir = os.path.dirname(f"{input_dir_basename}/{rel_path}")
                base_name = os.path.basename(input_path)
                name, ext = os.path.splitext(base_name)
                translated_name = f"{name}_translated{ext}"
                if rel_dir == '.':
                    output_path = os.path.join(output_dir, translated_name)
                else:
                    output_subdir = os.path.join(output_dir, rel_dir)
                    os.makedirs(output_subdir, exist_ok=True)
                    output_path = os.path.join(output_subdir, translated_name)
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(translated_content)
                print(f"翻译结果已保存到: {output_path}")
            except IOError:
                print(f"错误: 无法写入输出文件 {output_path}")
                sys.exit(1)

if __name__ == '__main__':
    main()