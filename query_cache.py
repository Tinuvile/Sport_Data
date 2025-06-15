#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询结果缓存系统
用于存储语音查询的结果，并提供给各个页面动态使用
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class QueryCache:
    """查询结果缓存管理器"""
    
    def __init__(self, cache_file: Optional[str] = None):
        """
        初始化查询缓存
        
        Args:
            cache_file: 缓存文件路径（可选，默认使用cache目录）
        """
        if cache_file is None:
            # 创建cache目录
            cache_dir = Path("cache")
            cache_dir.mkdir(exist_ok=True)
            self.cache_file = cache_dir / "query_cache.json"
        else:
            self.cache_file = Path(cache_file)
        
        self.cache_data = self._load_cache()
        logger.info(f"查询缓存系统初始化完成，缓存文件: {self.cache_file}")
    
    def _load_cache(self) -> Dict[str, Any]:
        """加载缓存数据"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 清理过期数据
                    self._clean_expired_data(data)
                    return data
            else:
                return {
                    'f1': {},
                    'football': {},
                    'nba': {},
                    'metadata': {
                        'last_updated': datetime.now().isoformat(),
                        'version': '1.0'
                    }
                }
        except Exception as e:
            logger.error(f"加载缓存失败: {e}")
            return {
                'f1': {},
                'football': {},
                'nba': {},
                'metadata': {
                    'last_updated': datetime.now().isoformat(),
                    'version': '1.0'
                }
            }
    
    def _save_cache(self):
        """保存缓存数据"""
        try:
            self.cache_data['metadata']['last_updated'] = datetime.now().isoformat()
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, ensure_ascii=False, indent=2)
            logger.info("缓存数据已保存")
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
    
    def _clean_expired_data(self, data: Dict[str, Any], max_age_days: int = 7):
        """清理过期数据"""
        try:
            cutoff_time = datetime.now() - timedelta(days=max_age_days)
            
            for sport in ['f1', 'football', 'nba']:
                if sport in data:
                    expired_keys = []
                    for key, value in data[sport].items():
                        if isinstance(value, dict) and 'timestamp' in value:
                            try:
                                item_time = datetime.fromisoformat(value['timestamp'])
                                if item_time < cutoff_time:
                                    expired_keys.append(key)
                            except:
                                expired_keys.append(key)
                    
                    for key in expired_keys:
                        del data[sport][key]
                        logger.info(f"清理过期数据: {sport}.{key}")
        except Exception as e:
            logger.error(f"清理过期数据失败: {e}")
    
    def store_query_result(self, sport: str, query_type: str, parameters: Dict[str, Any], 
                          result_data: Dict[str, Any], original_text: str):
        """
        存储查询结果
        
        Args:
            sport: 体育项目 (f1, football, nba)
            query_type: 查询类型 (standings, schedule, etc.)
            parameters: 查询参数
            result_data: 查询结果数据
            original_text: 原始查询文本
        """
        try:
            # 生成缓存键
            cache_key = self._generate_cache_key(query_type, parameters)
            
            # 存储数据
            cache_entry = {
                'query_type': query_type,
                'parameters': parameters,
                'result_data': result_data,
                'original_text': original_text,
                'timestamp': datetime.now().isoformat(),
                'success': result_data.get('success', False)
            }
            
            if sport not in self.cache_data:
                self.cache_data[sport] = {}
            
            self.cache_data[sport][cache_key] = cache_entry
            self._save_cache()
            
            logger.info(f"存储查询结果: {sport}.{cache_key}")
            return cache_key
            
        except Exception as e:
            logger.error(f"存储查询结果失败: {e}")
            return None
    
    def get_query_result(self, sport: str, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        获取查询结果
        
        Args:
            sport: 体育项目
            cache_key: 缓存键
            
        Returns:
            查询结果或None
        """
        try:
            if sport in self.cache_data and cache_key in self.cache_data[sport]:
                return self.cache_data[sport][cache_key]
            return None
        except Exception as e:
            logger.error(f"获取查询结果失败: {e}")
            return None
    
    def get_available_options(self, sport: str, query_type: str) -> List[Dict[str, Any]]:
        """
        获取可用的选项列表（用于动态添加到页面选择器中）
        
        Args:
            sport: 体育项目
            query_type: 查询类型
            
        Returns:
            可用选项列表
        """
        try:
            options = []
            
            if sport in self.cache_data:
                for cache_key, cache_entry in self.cache_data[sport].items():
                    if cache_entry.get('query_type') == query_type and cache_entry.get('success'):
                        parameters = cache_entry.get('parameters', {})
                        
                        # 根据不同的查询类型生成选项
                        if query_type == 'standings' and sport == 'football':
                            # 足球联赛积分榜
                            league_id = parameters.get('league_id')
                            if league_id:
                                league_name = self._get_league_name(league_id)
                                options.append({
                                    'value': league_id,
                                    'label': league_name,
                                    'cache_key': cache_key,
                                    'original_text': cache_entry.get('original_text', ''),
                                    'timestamp': cache_entry.get('timestamp')
                                })
                        
                        elif query_type == 'schedule' and sport == 'nba':
                            # NBA球队赛程
                            team = parameters.get('team')
                            if team:
                                options.append({
                                    'value': team,
                                    'label': f"{team} 赛程",
                                    'cache_key': cache_key,
                                    'original_text': cache_entry.get('original_text', ''),
                                    'timestamp': cache_entry.get('timestamp')
                                })
                        
                        elif query_type == 'standings' and sport == 'f1':
                            # F1积分榜
                            year = parameters.get('year', datetime.now().year)
                            options.append({
                                'value': f"f1_{year}",
                                'label': f"{year}年 F1积分榜",
                                'cache_key': cache_key,
                                'original_text': cache_entry.get('original_text', ''),
                                'timestamp': cache_entry.get('timestamp')
                            })
            
            # 按时间排序，最新的在前
            options.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return options
            
        except Exception as e:
            logger.error(f"获取可用选项失败: {e}")
            return []
    
    def _generate_cache_key(self, query_type: str, parameters: Dict[str, Any]) -> str:
        """生成缓存键"""
        key_parts = [query_type]
        
        # 添加重要参数到键中
        for param in ['league_id', 'team', 'year', 'round']:
            if param in parameters:
                key_parts.append(f"{param}_{parameters[param]}")
        
        return "_".join(key_parts)
    
    def _get_league_name(self, league_id: int) -> str:
        """根据联赛ID获取联赛名称"""
        league_names = {
            2021: "英超",
            2014: "西甲", 
            2002: "德甲",
            2019: "意甲",
            2015: "法甲",
            2017: "葡超",
            2003: "荷甲",
            2013: "巴甲"
        }
        return league_names.get(league_id, f"联赛{league_id}")
    
    def get_all_cached_data(self) -> Dict[str, Any]:
        """获取所有缓存数据"""
        return self.cache_data.copy()
    
    def clear_cache(self, sport: Optional[str] = None):
        """
        清理缓存
        
        Args:
            sport: 指定体育项目，None表示清理所有
        """
        try:
            if sport:
                if sport in self.cache_data:
                    self.cache_data[sport] = {}
                    logger.info(f"清理{sport}缓存")
            else:
                self.cache_data = {
                    'f1': {},
                    'football': {},
                    'nba': {},
                    'metadata': {
                        'last_updated': datetime.now().isoformat(),
                        'version': '1.0'
                    }
                }
                logger.info("清理所有缓存")
            
            self._save_cache()
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")


# 全局缓存实例
query_cache = QueryCache() 