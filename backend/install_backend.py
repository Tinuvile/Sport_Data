#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
体育数据后端安装脚本
自动安装所需依赖包
"""

import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def install_package(package):
    """安装Python包"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        logger.info(f"✓ {package} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ {package} 安装失败: {e}")
        return False

def main():
    """主安装函数"""
    logger.info("🚀 开始安装体育数据后端依赖...")
    
    # 必需的包列表
    packages = [
        "requests>=2.31.0",
        "pandas>=2.0.0", 
        "numpy>=1.24.0",
        "fastf1>=3.0.0",
        "nba-api>=1.1.0",
        "urllib3>=2.0.0"
    ]
    
    success_count = 0
    total_packages = len(packages)
    
    for package in packages:
        logger.info(f"📦 正在安装 {package}...")
        if install_package(package):
            success_count += 1
    
    logger.info("=" * 50)
    if success_count == total_packages:
        logger.info("🎉 所有依赖安装完成！")
        logger.info("📋 下一步：")
        logger.info("   1. 运行测试: python -m backend.test_apis")
        logger.info("   2. 查看文档: backend/README.md")
    else:
        failed_count = total_packages - success_count
        logger.error(f"❌ 有 {failed_count} 个包安装失败")
        logger.info("💡 建议：")
        logger.info("   1. 检查网络连接")
        logger.info("   2. 更新pip: python -m pip install --upgrade pip")
        logger.info("   3. 手动安装: pip install -r backend_requirements.txt")

if __name__ == "__main__":
    main() 