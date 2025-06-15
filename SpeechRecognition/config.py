#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FunASR 语音识别配置文件
统一管理所有配置项，包括缓存目录设置
"""

import os
import platform
from pathlib import Path

# ==================== 缓存目录配置 ====================
# 自定义缓存根目录（改为 G 盘）
CUSTOM_CACHE_ROOT = r"G:\Users\ASUS\.cache"

# 确保缓存目录存在
def setup_cache_directories():
    """设置并创建缓存目录"""
    cache_root = Path(CUSTOM_CACHE_ROOT)
    
    # 创建主缓存目录
    cache_root.mkdir(parents=True, exist_ok=True)
    
    # 创建子目录
    modelscope_cache = cache_root / "modelscope"
    huggingface_cache = cache_root / "huggingface"
    torch_cache = cache_root / "torch"
    
    modelscope_cache.mkdir(exist_ok=True)
    huggingface_cache.mkdir(exist_ok=True)
    torch_cache.mkdir(exist_ok=True)
    
    return {
        "modelscope": str(modelscope_cache),
        "huggingface": str(huggingface_cache),
        "torch": str(torch_cache)
    }

# 设置环境变量
def set_cache_environment():
    """设置缓存相关的环境变量"""
    cache_dirs = setup_cache_directories()
    
    # ModelScope 缓存目录
    os.environ['MODELSCOPE_CACHE'] = cache_dirs["modelscope"]
    
    # Hugging Face 缓存目录
    os.environ['HF_HOME'] = cache_dirs["huggingface"]
    os.environ['HUGGINGFACE_HUB_CACHE'] = cache_dirs["huggingface"]
    
    # PyTorch 缓存目录
    os.environ['TORCH_HOME'] = cache_dirs["torch"]
    
    # 设置下载镜像（加速国内下载）
    os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
    
    print("缓存目录已设置:")
    print(f"  ModelScope: {cache_dirs['modelscope']}")
    print(f"  Hugging Face: {cache_dirs['huggingface']}")
    print(f"  PyTorch: {cache_dirs['torch']}")

# 在模块导入时自动设置
set_cache_environment()

# ==================== 模型配置 ====================
# 默认模型配置
DEFAULT_MODEL = "paraformer-zh"
VAD_MODEL = "fsmn-vad"
PUNC_MODEL = "ct-punc"
STREAMING_MODEL = "paraformer-zh-streaming"

# 设备配置
DEVICE = "cpu"  # 可选: "cpu", "cuda:0"

# 批处理配置
BATCH_SIZE_S = 300

# VAD 配置
MAX_SINGLE_SEGMENT_TIME = 30000  # 毫秒

# 流式识别配置
CHUNK_SIZE = [0, 10, 5]  # [0, 10, 5] 表示 600ms
ENCODER_CHUNK_LOOK_BACK = 4
DECODER_CHUNK_LOOK_BACK = 1

# ==================== 音频配置 ====================
# 支持的音频格式
SUPPORTED_FORMATS = [".wav", ".mp3", ".flac", ".m4a"]

# 推荐的音频参数
RECOMMENDED_SAMPLE_RATE = 16000
RECOMMENDED_CHANNELS = 1

# ==================== Web API 配置 ====================
# Flask 服务配置
WEB_HOST = "0.0.0.0"
WEB_PORT = 5000
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB

# ==================== 日志配置 ====================
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ==================== 下载配置 ====================
# 测试音频下载 URL
TEST_AUDIO_URL = "https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ASR/test_audio/vad_example.wav"
TEST_AUDIO_FILE = "test_audio.wav"

# ==================== 工具函数 ====================
def get_cache_info():
    """获取缓存目录信息"""
    cache_dirs = setup_cache_directories()
    info = {
        "cache_root": CUSTOM_CACHE_ROOT,
        "directories": cache_dirs,
        "environment_variables": {
            "MODELSCOPE_CACHE": os.environ.get("MODELSCOPE_CACHE"),
            "HF_HOME": os.environ.get("HF_HOME"),
            "TORCH_HOME": os.environ.get("TORCH_HOME"),
            "HF_ENDPOINT": os.environ.get("HF_ENDPOINT")
        }
    }
    return info

def check_cache_space():
    """检查缓存目录的磁盘空间"""
    try:
        import shutil
        cache_root = Path(CUSTOM_CACHE_ROOT)
        if cache_root.exists():
            total, used, free = shutil.disk_usage(cache_root)
            return {
                "total_gb": total // (1024**3),
                "used_gb": used // (1024**3),
                "free_gb": free // (1024**3),
                "usage_percent": (used / total) * 100
            }
    except Exception as e:
        return {"error": str(e)}
    return None

if __name__ == "__main__":
    print("FunASR 配置信息")
    print("=" * 50)
    
    # 显示缓存信息
    cache_info = get_cache_info()
    print("缓存配置:")
    for key, value in cache_info["environment_variables"].items():
        print(f"  {key}: {value}")
    
    # 显示磁盘空间
    space_info = check_cache_space()
    if space_info and "error" not in space_info:
        print(f"\nG 盘磁盘空间:")
        print(f"  总空间: {space_info['total_gb']} GB")
        print(f"  已使用: {space_info['used_gb']} GB")
        print(f"  剩余空间: {space_info['free_gb']} GB")
        print(f"  使用率: {space_info['usage_percent']:.1f}%")
    
    print("\n模型配置:")
    print(f"  默认模型: {DEFAULT_MODEL}")
    print(f"  VAD 模型: {VAD_MODEL}")
    print(f"  标点模型: {PUNC_MODEL}")
    print(f"  流式模型: {STREAMING_MODEL}")
    print(f"  设备: {DEVICE}") 