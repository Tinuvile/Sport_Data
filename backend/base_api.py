#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础API类
提供通用的HTTP请求、缓存、限流等功能
"""

import time
import json
import hashlib
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import CACHE_CONFIG, LOGGING_CONFIG


class RateLimiter:
    """API限流器"""
    
    def __init__(self, max_requests: int, time_window: int = 60):
        """
        初始化限流器
        
        Args:
            max_requests: 时间窗口内最大请求数
            time_window: 时间窗口（秒）
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    def can_request(self) -> bool:
        """检查是否可以发起请求"""
        now = time.time()
        
        # 清理过期的请求记录
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < self.time_window]
        
        return len(self.requests) < self.max_requests
    
    def add_request(self):
        """记录新的请求"""
        self.requests.append(time.time())
    
    def wait_if_needed(self):
        """如果需要，等待到可以发起请求"""
        while not self.can_request():
            time.sleep(1)


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache_dir: str, expire_time: int = 3600):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录
            expire_time: 缓存过期时间（秒）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.expire_time = expire_time
    
    def _get_cache_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{hash_key}.json"
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """从缓存获取数据"""
        if not CACHE_CONFIG['ENABLED']:
            return None
        
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 检查是否过期
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cached_time > timedelta(seconds=self.expire_time):
                cache_path.unlink()  # 删除过期缓存
                return None
            
            return cache_data['data']
            
        except (json.JSONDecodeError, KeyError, ValueError):
            # 缓存文件损坏，删除它
            if cache_path.exists():
                cache_path.unlink()
            return None
    
    def set(self, key: str, data: Dict[str, Any]):
        """设置缓存数据"""
        if not CACHE_CONFIG['ENABLED']:
            return
        
        cache_path = self._get_cache_path(key)
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.warning(f"缓存写入失败: {e}")
    
    def clear(self):
        """清空所有缓存"""
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
            except Exception as e:
                logging.warning(f"删除缓存文件失败 {cache_file}: {e}")


class BaseAPI:
    """基础API类"""
    
    def __init__(self, name: str, base_url: str, headers: Dict[str, str] = None,
                 rate_limit: int = 60, timeout: int = 30):
        """
        初始化基础API
        
        Args:
            name: API名称
            base_url: API基础URL
            headers: 默认请求头
            rate_limit: 每分钟最大请求数
            timeout: 请求超时时间
        """
        self.name = name
        self.base_url = base_url.rstrip('/')
        self.headers = headers or {}
        self.timeout = timeout
        
        # 初始化限流器
        self.rate_limiter = RateLimiter(rate_limit, 60)
        
        # 初始化缓存管理器
        cache_dir = Path(__file__).parent.parent / "cache" / "backend" / name.lower()
        self.cache_manager = CacheManager(str(cache_dir))
        
        # 配置日志
        self.logger = logging.getLogger(f"backend.{name}")
        
        # 配置HTTP会话
        self.session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.logger.info(f"{self.name} API 初始化完成")
    
    def _make_request(self, method: str, endpoint: str, 
                     params: Dict[str, Any] = None,
                     data: Dict[str, Any] = None,
                     use_cache: bool = True) -> Dict[str, Any]:
        """
        发起HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            params: URL参数
            data: 请求体数据
            use_cache: 是否使用缓存
            
        Returns:
            响应数据
        """
        # 构建完整URL
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # 生成缓存键
        cache_key = f"{method}:{url}:{json.dumps(params or {}, sort_keys=True)}"
        
        # 尝试从缓存获取
        if use_cache and method.upper() == 'GET':
            cached_data = self.cache_manager.get(cache_key)
            if cached_data:
                self.logger.debug(f"从缓存获取数据: {endpoint}")
                return cached_data
        
        # 限流检查
        self.rate_limiter.wait_if_needed()
        
        try:
            self.logger.info(f"请求 {method} {url}")
            
            # 发起请求
            response = self.session.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=data,
                timeout=self.timeout
            )
            
            # 记录请求
            self.rate_limiter.add_request()
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析JSON响应
            try:
                data = response.json()
            except json.JSONDecodeError:
                self.logger.error(f"响应不是有效的JSON: {response.text[:200]}")
                raise ValueError("响应格式错误")
            
            # 缓存GET请求的响应
            if use_cache and method.upper() == 'GET':
                self.cache_manager.set(cache_key, data)
            
            self.logger.debug(f"请求成功: {endpoint}")
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求失败 {endpoint}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"处理响应时发生错误: {e}")
            raise
    
    def get(self, endpoint: str, params: Dict[str, Any] = None, 
            use_cache: bool = True) -> Dict[str, Any]:
        """GET请求"""
        return self._make_request('GET', endpoint, params=params, use_cache=use_cache)
    
    def post(self, endpoint: str, data: Dict[str, Any] = None,
             params: Dict[str, Any] = None) -> Dict[str, Any]:
        """POST请求"""
        return self._make_request('POST', endpoint, params=params, data=data, use_cache=False)
    
    def put(self, endpoint: str, data: Dict[str, Any] = None,
            params: Dict[str, Any] = None) -> Dict[str, Any]:
        """PUT请求"""
        return self._make_request('PUT', endpoint, params=params, data=data, use_cache=False)
    
    def delete(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """DELETE请求"""
        return self._make_request('DELETE', endpoint, params=params, use_cache=False)
    
    def clear_cache(self):
        """清空缓存"""
        self.cache_manager.clear()
        self.logger.info(f"{self.name} API 缓存已清空") 