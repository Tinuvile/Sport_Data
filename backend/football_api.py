#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
足球数据API模块
使用 football-data.org API 获取足球比赛数据、球队数据等
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta

from .base_api import BaseAPI
from .config import API_CONFIG


class FootballDataAPI(BaseAPI):
    """足球数据API类"""
    
    def __init__(self):
        """初始化足球API"""
        config = API_CONFIG['FOOTBALL_DATA']
        super().__init__(
            name="Football",
            base_url=config['BASE_URL'],
            headers=config['HEADERS'],
            rate_limit=config['RATE_LIMIT'],
            timeout=config['TIMEOUT']
        )
        
        # 主要联赛ID映射
        self.league_codes = {
            'premier_league': 'PL',    # 英超
            'la_liga': 'PD',           # 西甲
            'bundesliga': 'BL1',       # 德甲
            'serie_a': 'SA',           # 意甲
            'ligue_1': 'FL1',          # 法甲
            'champions_league': 'CL',   # 欧冠
            'europa_league': 'EL',      # 欧联杯
            'world_cup': 'WC',         # 世界杯
            'euros': 'EC'              # 欧洲杯
        }
        
        self.logger.info("足球API初始化完成")
    
    def get_matches(self, competition_code: Optional[str] = None,
                   date_from: Optional[str] = None,
                   date_to: Optional[str] = None,
                   status: Optional[str] = None) -> Dict[str, Any]:
        """
        获取比赛列表
        
        Args:
            competition_code: 联赛代码
            date_from: 开始日期 (YYYY-MM-DD)
            date_to: 结束日期 (YYYY-MM-DD)
            status: 比赛状态 ('SCHEDULED', 'LIVE', 'IN_PLAY', 'PAUSED', 'FINISHED', 'POSTPONED', 'SUSPENDED', 'CANCELLED')
            
        Returns:
            比赛列表字典
        """
        try:
            endpoint = f'competitions/{competition_code}/matches' if competition_code else 'matches'
            
            params = {}
            if date_from:
                params['dateFrom'] = date_from
            if date_to:
                params['dateTo'] = date_to
            if status:
                params['status'] = status
            
            response = self.get(endpoint, params=params)
            
            matches = []
            for match in response.get('matches', []):
                match_dict = {
                    'id': match['id'],
                    'utc_date': match['utcDate'],
                    'status': match['status'],
                    'matchday': match.get('matchday'),
                    'stage': match.get('stage'),
                    'group': match.get('group'),
                    'last_updated': match.get('lastUpdated'),
                    
                    # 主队信息
                    'home_team': {
                        'id': match['homeTeam']['id'],
                        'name': match['homeTeam']['name'],
                        'short_name': match['homeTeam'].get('shortName'),
                        'tla': match['homeTeam'].get('tla'),
                        'crest': match['homeTeam'].get('crest')
                    },
                    
                    # 客队信息
                    'away_team': {
                        'id': match['awayTeam']['id'],
                        'name': match['awayTeam']['name'],
                        'short_name': match['awayTeam'].get('shortName'),
                        'tla': match['awayTeam'].get('tla'),
                        'crest': match['awayTeam'].get('crest')
                    },
                    
                    # 比分信息
                    'score': {
                        'winner': match.get('score', {}).get('winner'),
                        'duration': match.get('score', {}).get('duration'),
                        'full_time': match.get('score', {}).get('fullTime'),
                        'half_time': match.get('score', {}).get('halfTime'),
                        'regular_time': match.get('score', {}).get('regularTime'),
                        'extra_time': match.get('score', {}).get('extraTime'),
                        'penalties': match.get('score', {}).get('penalties')
                    },
                    
                    # 比赛信息
                    'competition': {
                        'id': match.get('competition', {}).get('id'),
                        'name': match.get('competition', {}).get('name'),
                        'code': match.get('competition', {}).get('code'),
                        'type': match.get('competition', {}).get('type'),
                        'emblem': match.get('competition', {}).get('emblem')
                    },
                    
                    # 赛季信息
                    'season': {
                        'id': match.get('season', {}).get('id'),
                        'start_date': match.get('season', {}).get('startDate'),
                        'end_date': match.get('season', {}).get('endDate'),
                        'current_matchday': match.get('season', {}).get('currentMatchday')
                    }
                }
                matches.append(match_dict)
            
            return {
                'success': True,
                'total_count': len(matches),
                'matches': matches
            }
            
        except Exception as e:
            self.logger.error(f"获取比赛列表失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_standings(self, competition_code: str, season: Optional[int] = None) -> Dict[str, Any]:
        """
        获取联赛积分榜
        
        Args:
            competition_code: 联赛代码
            season: 赛季年份（已废弃，免费API只支持当前赛季）
            
        Returns:
            积分榜字典
        """
        try:
            endpoint = f'competitions/{competition_code}/standings'
            
            # 免费API只支持当前赛季，忽略season参数
            if season and season != 2024:
                return {
                    'success': False,
                    'error': f'历史数据查询需要付费订阅。免费版本只支持当前赛季(2024-25)数据。',
                    'suggestion': '请查询当前赛季数据或升级到付费版本。'
                }
            
            response = self.get(endpoint)
            
            standings_data = []
            for standing in response.get('standings', []):
                standing_dict = {
                    'stage': standing.get('stage'),
                    'type': standing.get('type'),
                    'group': standing.get('group'),
                    'table': []
                }
                
                for table_entry in standing.get('table', []):
                    entry_dict = {
                        'position': table_entry['position'],
                        'team': {
                            'id': table_entry['team']['id'],
                            'name': table_entry['team']['name'],
                            'short_name': table_entry['team'].get('shortName'),
                            'tla': table_entry['team'].get('tla'),
                            'crest': table_entry['team'].get('crest')
                        },
                        'played_games': table_entry['playedGames'],
                        'form': table_entry.get('form'),
                        'won': table_entry['won'],
                        'draw': table_entry['draw'],
                        'lost': table_entry['lost'],
                        'points': table_entry['points'],
                        'goals_for': table_entry['goalsFor'],
                        'goals_against': table_entry['goalsAgainst'],
                        'goal_difference': table_entry['goalDifference']
                    }
                    standing_dict['table'].append(entry_dict)
                
                standings_data.append(standing_dict)
            
            # 比赛信息
            competition_info = {
                'id': response.get('competition', {}).get('id'),
                'name': response.get('competition', {}).get('name'),
                'code': response.get('competition', {}).get('code'),
                'type': response.get('competition', {}).get('type'),
                'emblem': response.get('competition', {}).get('emblem')
            }
            
            # 赛季信息
            season_info = {
                'id': response.get('season', {}).get('id'),
                'start_date': response.get('season', {}).get('startDate'),
                'end_date': response.get('season', {}).get('endDate'),
                'current_matchday': response.get('season', {}).get('currentMatchday')
            }
            
            return {
                'success': True,
                'competition': competition_info,
                'season': season_info,
                'standings': standings_data
            }
            
        except Exception as e:
            self.logger.error(f"获取积分榜失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_team_info(self, team_id: int) -> Dict[str, Any]:
        """
        获取球队信息
        
        Args:
            team_id: 球队ID
            
        Returns:
            球队信息字典
        """
        try:
            endpoint = f'teams/{team_id}'
            response = self.get(endpoint)
            
            team_info = {
                'id': response['id'],
                'name': response['name'],
                'short_name': response.get('shortName'),
                'tla': response.get('tla'),
                'crest': response.get('crest'),
                'address': response.get('address'),
                'website': response.get('website'),
                'founded': response.get('founded'),
                'club_colors': response.get('clubColors'),
                'venue': response.get('venue'),
                'area': {
                    'id': response.get('area', {}).get('id'),
                    'name': response.get('area', {}).get('name'),
                    'code': response.get('area', {}).get('code'),
                    'flag': response.get('area', {}).get('flag')
                } if response.get('area') else None,
                'running_competitions': []
            }
            
            # 正在参与的比赛
            for comp in response.get('runningCompetitions', []):
                comp_dict = {
                    'id': comp['id'],
                    'name': comp['name'],
                    'code': comp.get('code'),
                    'type': comp.get('type'),
                    'emblem': comp.get('emblem')
                }
                team_info['running_competitions'].append(comp_dict)
            
            # 球员名单
            squad = []
            for player in response.get('squad', []):
                player_dict = {
                    'id': player['id'],
                    'name': player['name'],
                    'position': player.get('position'),
                    'date_of_birth': player.get('dateOfBirth'),
                    'nationality': player.get('nationality')
                }
                squad.append(player_dict)
            
            team_info['squad'] = squad
            
            return {
                'success': True,
                'team': team_info
            }
            
        except Exception as e:
            self.logger.error(f"获取球队信息失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_team_matches(self, team_id: int, 
                        date_from: Optional[str] = None,
                        date_to: Optional[str] = None,
                        status: Optional[str] = None,
                        venue: Optional[str] = None) -> Dict[str, Any]:
        """
        获取球队比赛列表
        
        Args:
            team_id: 球队ID
            date_from: 开始日期 (YYYY-MM-DD)
            date_to: 结束日期 (YYYY-MM-DD)
            status: 比赛状态
            venue: 比赛场地 ('home', 'away')
            
        Returns:
            比赛列表字典
        """
        try:
            endpoint = f'teams/{team_id}/matches'
            
            params = {}
            if date_from:
                params['dateFrom'] = date_from
            if date_to:
                params['dateTo'] = date_to
            if status:
                params['status'] = status
            if venue:
                params['venue'] = venue
            
            response = self.get(endpoint, params=params)
            
            matches = []
            for match in response.get('matches', []):
                match_dict = {
                    'id': match['id'],
                    'utc_date': match['utcDate'],
                    'status': match['status'],
                    'matchday': match.get('matchday'),
                    'stage': match.get('stage'),
                    'group': match.get('group'),
                    'home_team': {
                        'id': match['homeTeam']['id'],
                        'name': match['homeTeam']['name'],
                        'crest': match['homeTeam'].get('crest')
                    },
                    'away_team': {
                        'id': match['awayTeam']['id'],
                        'name': match['awayTeam']['name'],
                        'crest': match['awayTeam'].get('crest')
                    },
                    'score': match.get('score'),
                    'competition': match.get('competition')
                }
                matches.append(match_dict)
            
            return {
                'success': True,
                'total_count': len(matches),
                'matches': matches
            }
            
        except Exception as e:
            self.logger.error(f"获取球队比赛失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_top_scorers(self, competition_code: str, season: Optional[int] = None) -> Dict[str, Any]:
        """
        获取射手榜
        
        Args:
            competition_code: 联赛代码
            season: 赛季年份（已废弃，免费API只支持当前赛季）
            
        Returns:
            射手榜字典
        """
        try:
            # 免费API只支持当前赛季，检查历史数据请求
            if season and season != 2024:
                return {
                    'success': False,
                    'error': f'历史数据查询需要付费订阅。免费版本只支持当前赛季(2024-25)数据。',
                    'suggestion': '请查询当前赛季数据或升级到付费版本。'
                }
            
            endpoint = f'competitions/{competition_code}/scorers'
            
            # 不传递season参数，使用默认当前赛季
            response = self.get(endpoint)
            
            scorers = []
            for scorer in response.get('scorers', []):
                scorer_dict = {
                    'player': {
                        'id': scorer['player']['id'],
                        'name': scorer['player']['name'],
                        'first_name': scorer['player'].get('firstName'),
                        'last_name': scorer['player'].get('lastName'),
                        'date_of_birth': scorer['player'].get('dateOfBirth'),
                        'nationality': scorer['player'].get('nationality'),
                        'position': scorer['player'].get('position')
                    },
                    'team': {
                        'id': scorer['team']['id'],
                        'name': scorer['team']['name'],
                        'short_name': scorer['team'].get('shortName'),
                        'tla': scorer['team'].get('tla'),
                        'crest': scorer['team'].get('crest')
                    },
                    'goals': scorer['goals'],
                    'assists': scorer.get('assists'),
                    'penalties': scorer.get('penalties')
                }
                scorers.append(scorer_dict)
            
            return {
                'success': True,
                'competition': response.get('competition'),
                'season': response.get('season'),
                'total_count': len(scorers),
                'scorers': scorers
            }
            
        except Exception as e:
            self.logger.error(f"获取射手榜失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_today_matches(self) -> Dict[str, Any]:
        """获取今日比赛"""
        today = datetime.now().date()
        return self.get_matches(
            date_from=today.isoformat(),
            date_to=today.isoformat()
        )
    
    def get_live_matches(self) -> Dict[str, Any]:
        """获取正在进行的比赛"""
        return self.get_matches(status='IN_PLAY')
    
    def get_premier_league_standings(self) -> Dict[str, Any]:
        """获取英超积分榜"""
        return self.get_standings('PL')
    
    def get_champions_league_matches(self) -> Dict[str, Any]:
        """获取欧冠比赛"""
        return self.get_matches('CL')