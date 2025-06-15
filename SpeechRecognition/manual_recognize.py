#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动语音识别脚本
用于识别 recordings 文件夹中的音频文件
"""

import os
import sys
from pathlib import Path
import argparse

# 首先导入配置，设置缓存目录
import config

def print_with_flush(message):
    """打印并强制刷新输出"""
    print(message)
    sys.stdout.flush()

def recognize_audio_file(audio_file_path: str, verbose: bool = True) -> dict:
    """
    识别音频文件的可重用函数
    
    Args:
        audio_file_path: 音频文件路径
        verbose: 是否打印详细信息
        
    Returns:
        识别结果字典 {'success': bool, 'text': str, 'error': str, 'result': dict}
    """
    try:
        audio_path = Path(audio_file_path)
        
        if not audio_path.exists():
            return {
                'success': False,
                'error': f'音频文件不存在: {audio_file_path}',
                'text': '',
                'result': None
            }
        
        if verbose:
            print_with_flush(f"准备识别: {audio_path.name}")
            print_with_flush(f"文件大小: {audio_path.stat().st_size / 1024:.1f} KB")
        
        # 初始化语音识别器
        try:
            if verbose:
                print_with_flush("正在初始化语音识别器...")
            from speech_recognition import SpeechRecognizer
            
            recognizer = SpeechRecognizer(
                model_name=config.DEFAULT_MODEL,
                vad_model=config.VAD_MODEL,
                punc_model=config.PUNC_MODEL,
                device=config.DEVICE
            )
            if verbose:
                print_with_flush("语音识别器初始化成功")
            
        except Exception as e:
            return {
                'success': False,
                'error': f'语音识别器初始化失败: {e}',
                'text': '',
                'result': None
            }
        
        # 开始识别
        try:
            if verbose:
                print_with_flush("正在进行语音识别...")
            result = recognizer.recognize_file(str(audio_path.absolute()))
            
            if result and result.get('text'):
                text = result['text'].strip()
                if text:
                    if verbose:
                        print_with_flush("\n识别结果:")
                        print_with_flush("=" * 50)
                        print_with_flush(f"识别文本: {text}")
                        if result.get('timestamp'):
                            print_with_flush(f"时间戳: {result['timestamp']}")
                        print_with_flush("=" * 50)
                    
                    return {
                        'success': True,
                        'text': text,
                        'error': '',
                        'result': result
                    }
                else:
                    return {
                        'success': False,
                        'error': '识别结果为空',
                        'text': '',
                        'result': result
                    }
            else:
                return {
                    'success': False,
                    'error': '未识别到有效内容',
                    'text': '',
                    'result': result
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'语音识别失败: {e}',
                'text': '',
                'result': None
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'音频处理异常: {e}',
            'text': '',
            'result': None
        }

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="手动语音识别")
    parser.add_argument('--file', type=str, help='指定音频文件路径')
    parser.add_argument('--list', action='store_true', help='列出所有录音文件')
    
    args = parser.parse_args()
    
    print_with_flush("手动语音识别工具")
    print_with_flush("=" * 50)
    
    # 录音文件目录
    recordings_dir = Path("../recordings")
    
    if args.list:
        # 列出所有录音文件
        if not recordings_dir.exists():
            print_with_flush("recordings 目录不存在")
            return
        
        audio_files = list(recordings_dir.glob("*.wav"))
        if not audio_files:
            print_with_flush("没有找到音频文件")
            return
        
        print_with_flush(f"找到 {len(audio_files)} 个音频文件:")
        for i, audio_file in enumerate(sorted(audio_files), 1):
            size_kb = audio_file.stat().st_size / 1024
            print_with_flush(f"  {i:2d}. {audio_file.name} ({size_kb:.1f} KB)")
        
        return
    
    # 获取要识别的文件
    audio_file = None
    if args.file:
        audio_file = Path(args.file)
    else:
        # 让用户选择文件
        if not recordings_dir.exists():
            print_with_flush("recordings 目录不存在")
            return
        
        audio_files = list(recordings_dir.glob("*.wav"))
        if not audio_files:
            print_with_flush("没有找到音频文件")
            print_with_flush("请先使用录音脚本录制音频")
            return
        
        print_with_flush(f"找到 {len(audio_files)} 个音频文件:")
        for i, af in enumerate(sorted(audio_files), 1):
            size_kb = af.stat().st_size / 1024
            print_with_flush(f"  {i:2d}. {af.name} ({size_kb:.1f} KB)")
        
        try:
            choice = input("\n请选择要识别的文件编号 (回车选择最新的): ").strip()
            if choice:
                index = int(choice) - 1
                audio_file = sorted(audio_files)[index]
            else:
                audio_file = sorted(audio_files)[-1]  # 最新的文件
        except (ValueError, IndexError):
            print_with_flush("无效的选择")
            return
    
    if not audio_file.exists():
        print_with_flush(f"文件不存在: {audio_file}")
        return
    
    # 使用可重用函数进行识别
    result = recognize_audio_file(str(audio_file), verbose=True)
    
    if not result['success']:
        print_with_flush(f"错误: {result['error']}")
        print_with_flush("建议检查音频质量或网络连接")

if __name__ == "__main__":
    main() 