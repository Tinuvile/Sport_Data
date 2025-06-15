#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1 数据API模块
使用 FastF1 库获取F1比赛数据、车手信息、赛程等
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import pandas as pd
import numpy as np

try:
    import fastf1
    from fastf1 import get_session, get_event_schedule, get_event
    from fastf1.ergast import Ergast
    FASTF1_AVAILABLE = True
except ImportError:
    FASTF1_AVAILABLE = False

from .config import API_CONFIG


def safe_int(value, default=0):
    """安全转换为整数，处理NaN值"""
    if pd.isna(value) or value is None:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    """安全转换为浮点数，处理NaN值"""
    if pd.isna(value) or value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_str(value, default=''):
    """安全转换为字符串，处理NaN值"""
    if pd.isna(value) or value is None:
        return default
    return str(value)


class F1DataAPI:
    """F1数据API类"""
    
    def __init__(self):
        """初始化F1 API"""
        if not FASTF1_AVAILABLE:
            raise ImportError("FastF1库未安装，请运行: pip install fastf1")
        
        self.config = API_CONFIG['F1_API']
        self.logger = logging.getLogger("backend.f1")
        
        # 设置FastF1缓存
        if self.config['CACHE_ENABLED']:
            cache_dir = Path(self.config['CACHE_DIR'])
            cache_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"创建F1缓存目录: {cache_dir}")
            fastf1.Cache.enable_cache(str(cache_dir))
        
        # 初始化Ergast API（历史数据）- 使用pandas格式和自动类型转换
        self.ergast = Ergast(result_type='pandas', auto_cast=True)
        
        self.logger.info("F1 API 初始化完成")
    
    def get_current_season_schedule(self) -> Dict[str, Any]:
        """
        获取当前赛季赛程
        
        Returns:
            赛程信息字典
        """
        try:
            current_year = datetime.now().year
            self.logger.info(f"获取{current_year}赛季赛程...")
            
            # 使用FastF1获取赛程
            schedule = fastf1.get_event_schedule(current_year)
            
            events = []
            for idx, event in schedule.iterrows():
                # 安全地处理日期字段
                event_date = None
                if pd.notna(event.get('EventDate')):
                    try:
                        event_date = event['EventDate'].strftime('%Y-%m-%d')
                    except:
                        event_date = str(event['EventDate'])
                
                # 处理会话日期
                sessions = {}
                for i in range(1, 6):
                    session_key = f'Session{i}Date'
                    if session_key in event and pd.notna(event[session_key]):
                        try:
                            sessions[f'session_{i}_date'] = event[session_key].strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            sessions[f'session_{i}_date'] = str(event[session_key])
                    else:
                        sessions[f'session_{i}_date'] = None
                
                event_dict = {
                    'round_number': int(event.get('RoundNumber', 0)),
                    'event_name': str(event.get('EventName', '')),
                    'location': str(event.get('Location', '')),
                    'country': str(event.get('Country', '')),
                    'event_date': event_date,
                    **sessions
                }
                events.append(event_dict)
            
            return {
                'success': True,
                'year': current_year,
                'total_events': len(events),
                'events': events
            }
            
        except Exception as e:
            self.logger.error(f"获取赛季赛程失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'year': datetime.now().year,
                'total_events': 0,
                'events': []
            }
    
    def get_race_results(self, year: int, round_number: int) -> Dict[str, Any]:
        """
        获取比赛结果
        
        Args:
            year: 赛季年份
            round_number: 比赛轮次
            
        Returns:
            比赛结果字典
        """
        try:
            self.logger.info(f"获取{year}年第{round_number}轮比赛结果...")
            
            # 获取比赛会话
            session = fastf1.get_session(year, round_number, 'Race')
            
            # 检查会话是否支持
            if not session.f1_api_support:
                self.logger.warning(f"{year}年第{round_number}轮比赛不支持F1 API，尝试使用Ergast API")
                return self._get_race_results_from_ergast(year, round_number)
            
            # 加载会话数据
            session.load()
            
            results = []
            if hasattr(session, 'results') and session.results is not None:
                for idx, result in session.results.iterrows():
                    result_dict = {
                        'position': int(result.get('Position', 0)) if pd.notna(result.get('Position')) else None,
                        'driver_number': int(result.get('DriverNumber', 0)) if pd.notna(result.get('DriverNumber')) else None,
                        'driver_code': str(result.get('Abbreviation', '')),
                        'driver_name': f"{result.get('FirstName', '')} {result.get('LastName', '')}".strip(),
                        'team_name': str(result.get('TeamName', '')),
                        'team_color': str(result.get('TeamColor', '')),
                        'grid_position': int(result.get('GridPosition', 0)) if pd.notna(result.get('GridPosition')) else None,
                        'time': str(result.get('Time', '')) if pd.notna(result.get('Time')) else None,
                        'status': str(result.get('Status', '')),
                        'points': float(result.get('Points', 0)) if pd.notna(result.get('Points')) else 0.0
                    }
                    results.append(result_dict)
            
            # 获取比赛信息
            race_info = {
                'year': year,
                'round_number': round_number,
                'event_name': str(session.event.get('EventName', '')),
                'location': str(session.event.get('Location', '')),
                'country': str(session.event.get('Country', '')),
                'date': session.date.strftime('%Y-%m-%d %H:%M:%S') if session.date else None,
                'total_laps': len(session.laps) if hasattr(session, 'laps') and session.laps is not None else None
            }
            
            return {
                'success': True,
                'race_info': race_info,
                'results': results
            }
            
        except Exception as e:
            self.logger.error(f"获取比赛结果失败: {e}")
            # 尝试使用Ergast API作为备选
            return self._get_race_results_from_ergast(year, round_number)
    
    def _get_race_results_from_ergast(self, year: int, round_number: int) -> Dict[str, Any]:
        """
        使用Ergast API获取比赛结果（备选方案）
        
        Args:
            year: 赛季年份
            round_number: 比赛轮次
            
        Returns:
            比赛结果字典
        """
        try:
            self.logger.info(f"使用Ergast API获取{year}年第{round_number}轮比赛结果...")
            
            # 获取比赛结果 - 根据文档，这返回ErgastMultiResponse
            race_response = self.ergast.get_race_results(season=year, round=round_number)
            
            results = []
            race_info = None
            
            # 检查是否有数据
            if race_response and hasattr(race_response, 'description') and len(race_response.description) > 0:
                # 获取比赛描述信息
                race_desc = race_response.description.iloc[0]
                race_info = {
                    'year': int(race_desc.get('season', year)),
                    'round_number': int(race_desc.get('round', round_number)),
                    'event_name': str(race_desc.get('raceName', f'Round {round_number}')),
                    'location': str(race_desc.get('locality', '')),
                    'country': str(race_desc.get('country', '')),
                    'date': str(race_desc.get('date', '')) if pd.notna(race_desc.get('date')) else None,
                    'total_laps': None
                }
                
                # 获取比赛结果数据
                if hasattr(race_response, 'content') and len(race_response.content) > 0:
                    race_results_df = race_response.content[0]  # 第一场比赛的结果
                    
                    for idx, result in race_results_df.iterrows():
                        result_dict = {
                            'position': int(result.get('position', 0)) if pd.notna(result.get('position')) else None,
                            'driver_number': int(result.get('number', 0)) if pd.notna(result.get('number')) else None,
                            'driver_code': str(result.get('code', '')),
                            'driver_name': f"{result.get('givenName', '')} {result.get('familyName', '')}".strip(),
                            'team_name': str(result.get('constructorName', '')),
                            'team_color': None,
                            'grid_position': int(result.get('grid', 0)) if pd.notna(result.get('grid')) else None,
                            'time': str(result.get('time', '')) if pd.notna(result.get('time')) else None,
                            'status': str(result.get('status', '')),
                            'points': float(result.get('points', 0)) if pd.notna(result.get('points')) else 0.0
                        }
                        results.append(result_dict)
            
            return {
                'success': True,
                'race_info': race_info or {
                    'year': year,
                    'round_number': round_number,
                    'event_name': f'Round {round_number}',
                    'location': '',
                    'country': '',
                    'date': None,
                    'total_laps': None
                },
                'results': results,
                'source': 'Ergast API'
            }
            
        except Exception as e:
            self.logger.error(f"Ergast API获取比赛结果失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'source': 'Ergast API'
            }
    
    def get_driver_standings(self, year: int) -> Dict[str, Any]:
        """
        获取车手积分榜
        
        Args:
            year: 赛季年份
            
        Returns:
            车手积分榜字典
        """
        try:
            self.logger.info(f"获取{year}年车手积分榜...")
            
            # 使用Ergast API获取车手积分榜
            standings_response = self.ergast.get_driver_standings(season=year)
            
            drivers = []
            
            # 检查响应类型和数据
            if standings_response and hasattr(standings_response, 'content') and len(standings_response.content) > 0:
                # ErgastMultiResponse - 获取最后一轮的积分榜
                latest_standings_df = standings_response.content[-1]  # 最后一轮
                
                for idx, standing in latest_standings_df.iterrows():
                    # 处理车队名称（可能是列表）
                    team_name = ''
                    if 'constructorNames' in standing and standing['constructorNames']:
                        team_name = safe_str(standing['constructorNames'][0]) if isinstance(standing['constructorNames'], list) else safe_str(standing['constructorNames'])
                    
                    driver_dict = {
                        'position': safe_int(standing.get('position', 0)),
                        'points': safe_float(standing.get('points', 0)),
                        'wins': safe_int(standing.get('wins', 0)),
                        'driver_id': safe_str(standing.get('driverId', '')),
                        'driver_code': safe_str(standing.get('driverCode', '')),
                        'driver_name': f"{safe_str(standing.get('givenName', ''))} {safe_str(standing.get('familyName', ''))}".strip(),
                        'nationality': safe_str(standing.get('driverNationality', '')),
                        'team_name': team_name
                    }
                    drivers.append(driver_dict)
                    
            elif isinstance(standings_response, pd.DataFrame):
                # ErgastSimpleResponse - 直接是DataFrame
                for idx, standing in standings_response.iterrows():
                    driver_dict = {
                        'position': safe_int(standing.get('position', 0)),
                        'points': safe_float(standing.get('points', 0)),
                        'wins': safe_int(standing.get('wins', 0)),
                        'driver_id': safe_str(standing.get('driverId', '')),
                        'driver_code': safe_str(standing.get('code', '')),
                        'driver_name': f"{safe_str(standing.get('givenName', ''))} {safe_str(standing.get('familyName', ''))}".strip(),
                        'nationality': safe_str(standing.get('nationality', '')),
                        'team_name': safe_str(standing.get('constructorName', ''))
                    }
                    drivers.append(driver_dict)
            
            return {
                'success': True,
                'year': year,
                'total_drivers': len(drivers),
                'standings': drivers,
                'source': 'Ergast API'
            }
            
        except Exception as e:
            self.logger.error(f"获取车手积分榜失败: {e}")
            # 备选方案：使用HTTP请求
            return self._get_driver_standings_http(year)
    
    def _get_driver_standings_http(self, year: int) -> Dict[str, Any]:
        """使用HTTP请求获取车手积分榜（备选方案）"""
        try:
            import requests
            
            url = f"http://ergast.com/api/f1/{year}/driverStandings.json"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                standings_table = data['MRData']['StandingsTable']['StandingsLists']
                
                drivers = []
                if standings_table:
                    # 获取最后一轮的积分榜
                    latest_standings = standings_table[-1]['DriverStandings']
                    
                    for standing in latest_standings:
                        driver_dict = {
                            'position': safe_int(standing['position']),
                            'points': safe_float(standing['points']),
                            'wins': safe_int(standing['wins']),
                            'driver_id': safe_str(standing['Driver']['driverId']),
                            'driver_code': safe_str(standing['Driver'].get('code', '')),
                            'driver_name': f"{safe_str(standing['Driver']['givenName'])} {safe_str(standing['Driver']['familyName'])}",
                            'nationality': safe_str(standing['Driver']['nationality']),
                            'team_name': safe_str(standing['Constructors'][0]['name']) if standing['Constructors'] else ''
                        }
                        drivers.append(driver_dict)
                
                return {
                    'success': True,
                    'year': year,
                    'total_drivers': len(drivers),
                    'standings': drivers,
                    'source': 'Ergast HTTP API'
                }
            else:
                raise Exception(f"HTTP请求失败: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"HTTP方式获取车手积分榜失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'year': year,
                'total_drivers': 0,
                'standings': []
            }
    
    def get_constructor_standings(self, year: int) -> Dict[str, Any]:
        """
        获取车队积分榜
        
        Args:
            year: 赛季年份
            
        Returns:
            车队积分榜字典
        """
        try:
            self.logger.info(f"获取{year}年车队积分榜...")
            
            # 使用Ergast API获取车队积分榜
            standings_response = self.ergast.get_constructor_standings(season=year)
            
            constructors = []
            
            # 检查响应类型和数据
            if standings_response and hasattr(standings_response, 'content') and len(standings_response.content) > 0:
                # ErgastMultiResponse - 获取最后一轮的积分榜
                latest_standings_df = standings_response.content[-1]  # 最后一轮
                
                for idx, standing in latest_standings_df.iterrows():
                    constructor_dict = {
                        'position': safe_int(standing.get('position', 0)),
                        'points': safe_float(standing.get('points', 0)),
                        'wins': safe_int(standing.get('wins', 0)),
                        'constructor_id': safe_str(standing.get('constructorId', '')),
                        'team_name': safe_str(standing.get('constructorName', '')),
                        'nationality': safe_str(standing.get('constructorNationality', ''))
                    }
                    constructors.append(constructor_dict)
                    
            elif isinstance(standings_response, pd.DataFrame):
                # ErgastSimpleResponse - 直接是DataFrame
                for idx, standing in standings_response.iterrows():
                    constructor_dict = {
                        'position': safe_int(standing.get('position', 0)),
                        'points': safe_float(standing.get('points', 0)),
                        'wins': safe_int(standing.get('wins', 0)),
                        'constructor_id': safe_str(standing.get('constructorId', '')),
                        'team_name': safe_str(standing.get('constructorName', '')),
                        'nationality': safe_str(standing.get('constructorNationality', ''))
                    }
                    constructors.append(constructor_dict)
            
            return {
                'success': True,
                'year': year,
                'total_constructors': len(constructors),
                'standings': constructors,
                'source': 'Ergast API'
            }
            
        except Exception as e:
            self.logger.error(f"获取车队积分榜失败: {e}")
            # 备选方案：使用HTTP请求
            return self._get_constructor_standings_http(year)
    
    def _get_constructor_standings_http(self, year: int) -> Dict[str, Any]:
        """使用HTTP请求获取车队积分榜（备选方案）"""
        try:
            import requests
            
            url = f"http://ergast.com/api/f1/{year}/constructorStandings.json"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                standings_table = data['MRData']['StandingsTable']['StandingsLists']
                
                constructors = []
                if standings_table:
                    # 获取最后一轮的积分榜
                    latest_standings = standings_table[-1]['ConstructorStandings']
                    
                    for standing in latest_standings:
                        constructor_dict = {
                            'position': safe_int(standing['position']),
                            'points': safe_float(standing['points']),
                            'wins': safe_int(standing['wins']),
                            'constructor_id': safe_str(standing['Constructor']['constructorId']),
                            'team_name': safe_str(standing['Constructor']['name']),
                            'nationality': safe_str(standing['Constructor']['nationality'])
                        }
                        constructors.append(constructor_dict)
                
                return {
                    'success': True,
                    'year': year,
                    'total_constructors': len(constructors),
                    'standings': constructors,
                    'source': 'Ergast HTTP API'
                }
            else:
                raise Exception(f"HTTP请求失败: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"HTTP方式获取车队积分榜失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'year': year,
                'total_constructors': 0,
                'standings': []
            }
    
    def get_qualifying_results(self, year: int, round_number: int) -> Dict[str, Any]:
        """
        获取排位赛结果
        
        Args:
            year: 赛季年份
            round_number: 比赛轮次
            
        Returns:
            排位赛结果字典
        """
        try:
            self.logger.info(f"获取{year}年第{round_number}轮排位赛结果...")
            
            # 首先尝试使用Ergast API
            try:
                qualifying_response = self.ergast.get_qualifying_results(season=year, round=round_number)
                
                results = []
                session_info = None
                
                if qualifying_response and hasattr(qualifying_response, 'description') and len(qualifying_response.description) > 0:
                    # 获取会话描述信息
                    session_desc = qualifying_response.description.iloc[0]
                    session_info = {
                        'year': int(session_desc.get('season', year)),
                        'round_number': int(session_desc.get('round', round_number)),
                        'event_name': str(session_desc.get('raceName', f'Round {round_number}')),
                        'location': str(session_desc.get('locality', '')),
                        'country': str(session_desc.get('country', '')),
                        'date': str(session_desc.get('date', '')) if pd.notna(session_desc.get('date')) else None
                    }
                    
                    # 获取排位赛结果数据
                    if hasattr(qualifying_response, 'content') and len(qualifying_response.content) > 0:
                        qualifying_results_df = qualifying_response.content[0]
                        
                        for idx, result in qualifying_results_df.iterrows():
                            result_dict = {
                                'position': int(result.get('position', 0)) if pd.notna(result.get('position')) else None,
                                'driver_number': int(result.get('number', 0)) if pd.notna(result.get('number')) else None,
                                'driver_code': str(result.get('code', '')),
                                'driver_name': f"{result.get('givenName', '')} {result.get('familyName', '')}".strip(),
                                'team_name': str(result.get('constructorName', '')),
                                'team_color': None,
                                'q1_time': str(result.get('q1', '')) if pd.notna(result.get('q1')) else None,
                                'q2_time': str(result.get('q2', '')) if pd.notna(result.get('q2')) else None,
                                'q3_time': str(result.get('q3', '')) if pd.notna(result.get('q3')) else None,
                            }
                            results.append(result_dict)
                
                return {
                    'success': True,
                    'session_info': session_info or {
                        'year': year,
                        'round_number': round_number,
                        'event_name': f'Round {round_number}',
                        'location': '',
                        'country': '',
                        'date': None
                    },
                    'results': results,
                    'source': 'Ergast API'
                }
                
            except Exception as ergast_error:
                self.logger.warning(f"Ergast API获取排位赛结果失败，尝试FastF1: {ergast_error}")
                
                # 备选方案：使用FastF1
                session = get_session(year, round_number, 'Qualifying')
                session.load()
                
                results = []
                for idx, result in session.results.iterrows():
                    result_dict = {
                        'position': int(result['Position']) if pd.notna(result['Position']) else None,
                        'driver_number': int(result['DriverNumber']) if pd.notna(result['DriverNumber']) else None,
                        'driver_code': result['Abbreviation'],
                        'driver_name': f"{result['FirstName']} {result['LastName']}",
                        'team_name': result['TeamName'],
                        'team_color': result['TeamColor'],
                        'q1_time': str(result['Q1']) if pd.notna(result['Q1']) else None,
                        'q2_time': str(result['Q2']) if pd.notna(result['Q2']) else None,
                        'q3_time': str(result['Q3']) if pd.notna(result['Q3']) else None,
                    }
                    results.append(result_dict)
                
                # 获取会话信息
                session_info = {
                    'year': year,
                    'round_number': round_number,
                    'event_name': session.event['EventName'],
                    'location': session.event['Location'],
                    'country': session.event['Country'],
                    'date': session.date.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                return {
                    'success': True,
                    'session_info': session_info,
                    'results': results,
                    'source': 'FastF1'
                }
            
        except Exception as e:
            self.logger.error(f"获取排位赛结果失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_lap_times(self, year: int, round_number: int, 
                     driver_code: Optional[str] = None) -> Dict[str, Any]:
        """
        获取圈速数据
        
        Args:
            year: 赛季年份
            round_number: 比赛轮次
            driver_code: 车手代码（可选，如果不指定则返回所有车手）
            
        Returns:
            圈速数据字典
        """
        try:
            self.logger.info(f"获取{year}年第{round_number}轮圈速数据...")
            
            # 首先尝试使用Ergast API获取圈速数据
            try:
                if driver_code:
                    # 获取特定车手的圈速
                    lap_times_response = self.ergast.get_lap_times(season=year, round=round_number, driver=driver_code)
                else:
                    # 获取所有车手的圈速（可能数据量很大，建议限制）
                    lap_times_response = self.ergast.get_lap_times(season=year, round=round_number, limit=100)
                
                laps_data = []
                
                if lap_times_response and hasattr(lap_times_response, 'content') and len(lap_times_response.content) > 0:
                    lap_times_df = lap_times_response.content[0]
                    
                    for idx, lap in lap_times_df.iterrows():
                        lap_dict = {
                            'lap_number': int(lap.get('lap', 0)),
                            'driver_code': str(lap.get('code', '')),
                            'driver_name': f"{lap.get('givenName', '')} {lap.get('familyName', '')}".strip(),
                            'lap_time': str(lap.get('time', '')) if pd.notna(lap.get('time')) else None,
                            'position': int(lap.get('position', 0)) if pd.notna(lap.get('position')) else None
                        }
                        laps_data.append(lap_dict)
                
                return {
                    'success': True,
                    'year': year,
                    'round_number': round_number,
                    'driver_code': driver_code,
                    'laps': laps_data,
                    'source': 'Ergast API'
                }
                
            except Exception as ergast_error:
                self.logger.warning(f"Ergast API获取圈速失败，尝试FastF1: {ergast_error}")
                
                # 备选方案：使用FastF1
                session = get_session(year, round_number, 'Race')
                session.load()
                
                laps_data = []
                
                if driver_code:
                    # 获取特定车手的圈速
                    driver_laps = session.laps.pick_driver(driver_code)
                    for idx, lap in driver_laps.iterrows():
                        lap_dict = {
                            'lap_number': int(lap['LapNumber']),
                            'driver_code': lap['Driver'],
                            'lap_time': str(lap['LapTime']) if pd.notna(lap['LapTime']) else None,
                            'sector_1_time': str(lap['Sector1Time']) if pd.notna(lap['Sector1Time']) else None,
                            'sector_2_time': str(lap['Sector2Time']) if pd.notna(lap['Sector2Time']) else None,
                            'sector_3_time': str(lap['Sector3Time']) if pd.notna(lap['Sector3Time']) else None,
                            'position': int(lap['Position']) if pd.notna(lap['Position']) else None,
                            'compound': lap['Compound'] if pd.notna(lap['Compound']) else None,
                            'tyre_life': int(lap['TyreLife']) if pd.notna(lap['TyreLife']) else None,
                            'is_personal_best': bool(lap['IsPersonalBest']) if pd.notna(lap['IsPersonalBest']) else False
                        }
                        laps_data.append(lap_dict)
                else:
                    # 获取所有车手的最快圈速
                    fastest_laps = session.laps.pick_fastest()
                    for idx, lap in fastest_laps.iterrows():
                        lap_dict = {
                            'driver_code': lap['Driver'],
                            'fastest_lap_time': str(lap['LapTime']) if pd.notna(lap['LapTime']) else None,
                            'lap_number': int(lap['LapNumber']),
                            'compound': lap['Compound'] if pd.notna(lap['Compound']) else None
                        }
                        laps_data.append(lap_dict)
                
                return {
                    'success': True,
                    'year': year,
                    'round_number': round_number,
                    'driver_code': driver_code,
                    'laps': laps_data,
                    'source': 'FastF1'
                }
            
        except Exception as e:
            self.logger.error(f"获取圈速数据失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_available_sessions(self, year: int, round_number: int) -> Dict[str, Any]:
        """
        获取可用的会话类型
        
        Args:
            year: 赛季年份
            round_number: 比赛轮次
            
        Returns:
            可用会话列表
        """
        try:
            event = get_event(year, round_number)
            sessions = []
            
            # 标准会话类型
            session_types = ['Practice 1', 'Practice 2', 'Practice 3', 'Qualifying', 'Race']
            
            for session_type in session_types:
                try:
                    session = get_session(year, round_number, session_type)
                    if session.date:
                        sessions.append({
                            'session_type': session_type,
                            'date': session.date.strftime('%Y-%m-%d %H:%M:%S'),
                            'available': True
                        })
                except:
                    sessions.append({
                        'session_type': session_type,
                        'available': False
                    })
            
            return {
                'success': True,
                'year': year,
                'round_number': round_number,
                'event_name': event['EventName'],
                'sessions': sessions
            }
            
        except Exception as e:
            self.logger.error(f"获取可用会话失败: {e}")
            return {
                'success': False,
                'error': str(e)
            } 