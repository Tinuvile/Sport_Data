#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端配置文件
包含各种API的配置信息
"""

import os
from pathlib import Path

# 基础配置
BASE_DIR = Path(__file__).parent.parent
CACHE_DIR = BASE_DIR / "cache" / "backend"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# API配置
API_CONFIG = {
    # Football Data API
    'FOOTBALL_DATA': {
        'BASE_URL': 'https://api.football-data.org/v4',
        'API_TOKEN': 'bfd8d2441c9f4fe2af371f607d35e40b',
        'HEADERS': {
            'X-Auth-Token': 'bfd8d2441c9f4fe2af371f607d35e40b',
            'Content-Type': 'application/json'
        },
        'RATE_LIMIT': 10,  # 每分钟请求次数
        'TIMEOUT': 30
    },
    
    # NBA API配置
    'NBA_API': {
        'BASE_URL': 'https://stats.nba.com/stats',
        'HEADERS': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.nba.com/'
        },
        'RATE_LIMIT': 60,  # 每分钟请求次数
        'TIMEOUT': 30
    },
    
    # ESPN API配置
    'ESPN_API': {
        'BASE_URL': 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba',
        'HEADERS': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        },
        'RATE_LIMIT': 60,  # 每分钟请求次数
        'TIMEOUT': 30
    },
    
    # F1 API配置 (使用FastF1库)
    'F1_API': {
        'CACHE_ENABLED': True,
        'CACHE_DIR': str(CACHE_DIR / 'f1'),
        'ERGAST_URL': 'http://ergast.com/api/f1',
        'TIMEOUT': 60
    }
}

# 缓存配置
CACHE_CONFIG = {
    'ENABLED': True,
    'EXPIRE_TIME': 3600,  # 1小时
    'MAX_SIZE': 1000  # 最大缓存条目数
}

# 日志配置
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': str(BASE_DIR / 'logs' / 'backend.log')
}

# 创建日志目录
log_dir = Path(LOGGING_CONFIG['file']).parent
log_dir.mkdir(parents=True, exist_ok=True) 