#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存管理工具
管理 FunASR 模型缓存，包括清理、迁移等功能
"""

import os
import shutil
import argparse
import logging
from pathlib import Path
from typing import Dict, List
import config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 默认的旧缓存位置
OLD_CACHE_LOCATIONS = [
    Path.home() / ".cache",
    Path("C:/Users/ASUS/.cache") if os.name == 'nt' else Path.home() / ".cache",
    Path.home() / ".modelscope",
    Path.home() / ".huggingface",
]


def get_directory_size(path: Path) -> int:
    """获取目录大小（字节）"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total_size += os.path.getsize(fp)
    except Exception as e:
        logger.warning(f"计算目录大小失败 {path}: {e}")
    return total_size


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"


def scan_cache_directories() -> Dict[str, Dict]:
    """扫描所有缓存目录"""
    logger.info("扫描缓存目录...")
    
    cache_info = {}
    
    # 当前配置的缓存目录
    current_cache = Path(config.CUSTOM_CACHE_ROOT)
    if current_cache.exists():
        size = get_directory_size(current_cache)
        cache_info["current"] = {
            "path": str(current_cache),
            "exists": True,
            "size": size,
            "formatted_size": format_size(size),
            "description": "当前配置的缓存目录 (G盘)"
        }
    else:
        cache_info["current"] = {
            "path": str(current_cache),
            "exists": False,
            "size": 0,
            "formatted_size": "0 B",
            "description": "当前配置的缓存目录 (G盘) - 不存在"
        }
    
    # 扫描可能的旧缓存位置
    old_caches = {}
    for old_location in OLD_CACHE_LOCATIONS:
        for cache_type in ["modelscope", "huggingface", "torch"]:
            old_cache_path = old_location / cache_type
            if old_cache_path.exists():
                size = get_directory_size(old_cache_path)
                old_caches[f"{old_location.name}_{cache_type}"] = {
                    "path": str(old_cache_path),
                    "exists": True,
                    "size": size,
                    "formatted_size": format_size(size),
                    "description": f"旧缓存: {cache_type} 在 {old_location}"
                }
    
    cache_info["old"] = old_caches
    
    return cache_info


def show_cache_status():
    """显示缓存状态"""
    logger.info("=" * 60)
    logger.info("FunASR 缓存状态报告")
    logger.info("=" * 60)
    
    cache_info = scan_cache_directories()
    
    # 显示当前缓存
    current = cache_info["current"]
    logger.info(f"\n📁 {current['description']}")
    logger.info(f"   路径: {current['path']}")
    logger.info(f"   大小: {current['formatted_size']}")
    logger.info(f"   状态: {'✓ 存在' if current['exists'] else '✗ 不存在'}")
    
    # 显示配置信息
    logger.info(f"\n⚙️  环境变量配置:")
    logger.info(f"   MODELSCOPE_CACHE: {os.environ.get('MODELSCOPE_CACHE', '未设置')}")
    logger.info(f"   HF_HOME: {os.environ.get('HF_HOME', '未设置')}")
    logger.info(f"   TORCH_HOME: {os.environ.get('TORCH_HOME', '未设置')}")
    
    # 显示旧缓存
    old_caches = cache_info["old"]
    if old_caches:
        logger.info(f"\n⚠️  发现旧缓存目录:")
        total_old_size = 0
        for name, info in old_caches.items():
            logger.info(f"   {info['description']}")
            logger.info(f"     路径: {info['path']}")
            logger.info(f"     大小: {info['formatted_size']}")
            total_old_size += info['size']
        
        logger.info(f"\n📊 旧缓存总大小: {format_size(total_old_size)}")
        logger.info(f"💡 建议: 运行 'python cache_manager.py --migrate' 迁移旧缓存")
    else:
        logger.info(f"\n✓ 未发现旧缓存目录")
    
    # 显示磁盘空间
    space_info = config.check_cache_space()
    if space_info and "error" not in space_info:
        logger.info(f"\n💾 G盘空间状态:")
        logger.info(f"   总容量: {space_info['total_gb']} GB")
        logger.info(f"   已使用: {space_info['used_gb']} GB")
        logger.info(f"   剩余空间: {space_info['free_gb']} GB")
        logger.info(f"   使用率: {space_info['usage_percent']:.1f}%")


def migrate_cache():
    """迁移旧缓存到新位置"""
    logger.info("开始迁移缓存到 G盘...")
    
    cache_info = scan_cache_directories()
    old_caches = cache_info["old"]
    
    if not old_caches:
        logger.info("✓ 未发现需要迁移的旧缓存")
        return
    
    # 确保新缓存目录存在
    config.setup_cache_directories()
    
    migrated_count = 0
    total_migrated_size = 0
    
    for name, info in old_caches.items():
        if not info['exists']:
            continue
            
        old_path = Path(info['path'])
        
        # 确定新路径
        if "modelscope" in name:
            new_path = Path(config.CUSTOM_CACHE_ROOT) / "modelscope"
        elif "huggingface" in name:
            new_path = Path(config.CUSTOM_CACHE_ROOT) / "huggingface"
        elif "torch" in name:
            new_path = Path(config.CUSTOM_CACHE_ROOT) / "torch"
        else:
            continue
        
        try:
            logger.info(f"迁移 {old_path} -> {new_path}")
            
            # 创建目标目录
            new_path.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            for item in old_path.iterdir():
                if item.is_file():
                    shutil.copy2(item, new_path / item.name)
                elif item.is_dir():
                    shutil.copytree(item, new_path / item.name, dirs_exist_ok=True)
            
            migrated_count += 1
            total_migrated_size += info['size']
            
            logger.info(f"✓ 迁移完成: {format_size(info['size'])}")
            
        except Exception as e:
            logger.error(f"✗ 迁移失败 {old_path}: {e}")
    
    if migrated_count > 0:
        logger.info(f"\n🎉 迁移完成!")
        logger.info(f"   迁移目录数: {migrated_count}")
        logger.info(f"   迁移数据量: {format_size(total_migrated_size)}")
        logger.info(f"   新缓存位置: {config.CUSTOM_CACHE_ROOT}")
        
        # 询问是否删除旧缓存
        response = input("\n是否删除旧缓存目录? (y/N): ").strip().lower()
        if response == 'y':
            clean_old_cache()
    else:
        logger.info("没有成功迁移任何目录")


def clean_old_cache():
    """清理旧缓存目录"""
    logger.info("清理旧缓存目录...")
    
    cache_info = scan_cache_directories()
    old_caches = cache_info["old"]
    
    if not old_caches:
        logger.info("✓ 没有旧缓存需要清理")
        return
    
    cleaned_count = 0
    total_cleaned_size = 0
    
    for name, info in old_caches.items():
        if not info['exists']:
            continue
            
        old_path = Path(info['path'])
        
        try:
            logger.info(f"删除 {old_path}")
            shutil.rmtree(old_path)
            
            cleaned_count += 1
            total_cleaned_size += info['size']
            
            logger.info(f"✓ 删除完成: {format_size(info['size'])}")
            
        except Exception as e:
            logger.error(f"✗ 删除失败 {old_path}: {e}")
    
    if cleaned_count > 0:
        logger.info(f"\n🧹 清理完成!")
        logger.info(f"   删除目录数: {cleaned_count}")
        logger.info(f"   释放空间: {format_size(total_cleaned_size)}")


def clean_current_cache():
    """清理当前缓存目录"""
    logger.info("清理当前缓存目录...")
    
    cache_path = Path(config.CUSTOM_CACHE_ROOT)
    
    if not cache_path.exists():
        logger.info("✓ 缓存目录不存在，无需清理")
        return
    
    # 确认清理
    size = get_directory_size(cache_path)
    logger.warning(f"将删除 {cache_path} ({format_size(size)})")
    response = input("确认清理? (y/N): ").strip().lower()
    
    if response != 'y':
        logger.info("取消清理")
        return
    
    try:
        shutil.rmtree(cache_path)
        logger.info(f"✓ 清理完成，释放空间: {format_size(size)}")
        
        # 重新创建目录结构
        config.setup_cache_directories()
        logger.info("✓ 重新创建缓存目录结构")
        
    except Exception as e:
        logger.error(f"✗ 清理失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="FunASR 缓存管理工具")
    parser.add_argument('--status', action='store_true', help='显示缓存状态')
    parser.add_argument('--migrate', action='store_true', help='迁移旧缓存到新位置')
    parser.add_argument('--clean-old', action='store_true', help='清理旧缓存目录')
    parser.add_argument('--clean-current', action='store_true', help='清理当前缓存目录')
    
    args = parser.parse_args()
    
    if args.status:
        show_cache_status()
    elif args.migrate:
        migrate_cache()
    elif args.clean_old:
        clean_old_cache()
    elif args.clean_current:
        clean_current_cache()
    else:
        # 默认显示状态
        show_cache_status()
        print("\n可用命令:")
        print("  python cache_manager.py --status       - 显示缓存状态")
        print("  python cache_manager.py --migrate      - 迁移旧缓存")
        print("  python cache_manager.py --clean-old    - 清理旧缓存")
        print("  python cache_manager.py --clean-current - 清理当前缓存")


if __name__ == "__main__":
    main() 