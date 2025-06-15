#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NBA数据API模块
使用 NBA_API 和 ESPN_API 获取NBA比赛数据、球员信息、球队数据、赛程等
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta

try:
    from nba_api.stats.endpoints import leaguegamefinder, teamgamelog, playergamelog
    from nba_api.stats.endpoints import leaguestandings, scoreboardv2, commonteamroster
    from nba_api.stats.endpoints import playercareerstats, teamdetails, playerprofilev2
    from nba_api.stats.static import teams, players
    NBA_API_AVAILABLE = True
except ImportError:
    NBA_API_AVAILABLE = False

from .base_api import BaseAPI
from .config import API_CONFIG
from .nba_team_ids import get_team_id, get_team_name, list_all_teams


class NBADataAPI:
    """NBA数据API类"""
    
    def __init__(self):
        """初始化NBA API"""
        self.logger = logging.getLogger("backend.nba")
        
        # 初始化ESPN API客户端
        espn_config = API_CONFIG['ESPN_API']
        self.espn_api = BaseAPI(
            name="ESPN_NBA",
            base_url=espn_config['BASE_URL'],
            headers=espn_config['HEADERS'],
            rate_limit=espn_config['RATE_LIMIT'],
            timeout=espn_config['TIMEOUT']
        )
        
        # 检查NBA_API是否可用
        if not NBA_API_AVAILABLE:
            self.logger.warning("NBA_API库未安装，仅使用ESPN API功能")
        
        self.logger.info("NBA API 初始化完成")
    
    def get_teams(self) -> Dict[str, Any]:
        """
        获取所有NBA球队信息
        
        Returns:
            球队列表字典
        """
        try:
            if NBA_API_AVAILABLE:
                # 使用NBA_API获取球队信息
                teams_data = teams.get_teams()
                
                teams_list = []
                for team in teams_data:
                    team_dict = {
                        'id': team['id'],
                        'full_name': team['full_name'],
                        'abbreviation': team['abbreviation'],
                        'nickname': team['nickname'],
                        'city': team['city'],
                        'state': team['state'],
                        'year_founded': team['year_founded']
                    }
                    teams_list.append(team_dict)
                
                return {
                    'success': True,
                    'source': 'NBA_API',
                    'total_count': len(teams_list),
                    'teams': teams_list
                }
            else:
                # 使用ESPN API作为备选
                response = self.espn_api.get('teams')
                
                teams_list = []
                for team in response.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', []):
                    team_info = team.get('team', {})
                    team_dict = {
                        'id': team_info.get('id'),
                        'full_name': team_info.get('displayName'),
                        'abbreviation': team_info.get('abbreviation'),
                        'nickname': team_info.get('name'),
                        'city': team_info.get('location'),
                        'logo': team_info.get('logo')
                    }
                    teams_list.append(team_dict)
                
                return {
                    'success': True,
                    'source': 'ESPN_API',
                    'total_count': len(teams_list),
                    'teams': teams_list
                }
                
        except Exception as e:
            self.logger.error(f"获取球队信息失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_players(self, team_id: Optional[int] = None, active_only: bool = True) -> Dict[str, Any]:
        """
        获取球员信息
        
        Args:
            team_id: 球队ID（可选）
            active_only: 是否只返回现役球员
            
        Returns:
            球员列表字典
        """
        try:
            if not NBA_API_AVAILABLE:
                return {
                    'success': False,
                    'error': 'NBA_API库未安装，无法获取球员信息'
                }
            
            # 获取球员数据
            players_data = players.get_players()
            
            if active_only:
                players_data = players.get_active_players()
            
            players_list = []
            for player in players_data:
                # 如果指定了球队ID，则过滤球员
                if team_id and hasattr(player, 'team_id') and player.get('team_id') != team_id:
                    continue
                
                player_dict = {
                    'id': player['id'],
                    'full_name': player['full_name'],
                    'first_name': player.get('first_name'),
                    'last_name': player.get('last_name'),
                    'is_active': player.get('is_active', True)
                }
                players_list.append(player_dict)
            
            return {
                'success': True,
                'source': 'NBA_API',
                'total_count': len(players_list),
                'players': players_list
            }
            
        except Exception as e:
            self.logger.error(f"获取球员信息失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_team_roster(self, team_id: int) -> Dict[str, Any]:
        """
        获取球队阵容
        
        Args:
            team_id: 球队ID (ESPN ID)
            
        Returns:
            球队阵容字典
        """
        try:
            if not NBA_API_AVAILABLE:
                return {
                    'success': False,
                    'error': 'NBA_API库未安装，无法获取球队阵容'
                }
            
            # 需要将ESPN ID转换为NBA API ID
            # 使用nba_api的teams模块获取球队信息
            nba_teams = teams.get_teams()
            
            # 根据ESPN ID找到对应的NBA API team
            nba_team = None
            team_name_from_espn = get_team_name(team_id)  # 从ESPN ID获取球队名称
            
            for team in nba_teams:
                if team['full_name'].lower() == team_name_from_espn.lower():
                    nba_team = team
                    break
            
            if not nba_team:
                return {
                    'success': False,
                    'error': f'无法找到对应的NBA API球队ID，ESPN ID: {team_id}'
                }
            
            nba_team_id = nba_team['id']
            
            # 获取球队阵容
            roster = commonteamroster.CommonTeamRoster(team_id=nba_team_id)
            roster_data = roster.get_data_frames()[0]
            
            players_list = []
            for idx, player in roster_data.iterrows():
                player_dict = {
                    'player_id': player['PLAYER_ID'],
                    'player_name': player['PLAYER'],
                    'num': player['NUM'],
                    'position': player['POSITION'],
                    'height': player['HEIGHT'],
                    'weight': player['WEIGHT'],
                    'birth_date': player.get('BIRTH_DATE'),
                    'age': player.get('AGE'),
                    'exp': player.get('EXP'),
                    'school': player.get('SCHOOL')
                }
                players_list.append(player_dict)
            
            return {
                'success': True,
                'team_id': team_id,  # 返回ESPN ID
                'nba_team_id': nba_team_id,  # 同时返回NBA API ID
                'team_name': team_name_from_espn,
                'total_count': len(players_list),
                'roster': players_list
            }
            
        except Exception as e:
            self.logger.error(f"获取球队阵容失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_standings(self) -> Dict[str, Any]:
        """
        获取联盟积分榜
        
        Returns:
            积分榜字典
        """
        try:
            if NBA_API_AVAILABLE:
                # 使用NBA_API获取积分榜
                standings = leaguestandings.LeagueStandings()
                standings_data = standings.get_data_frames()[0]
                
                standings_list = []
                for idx, team in standings_data.iterrows():
                    team_dict = {
                        'team_id': team['TeamID'],
                        'team_city': team['TeamCity'],
                        'team_name': f"{team['TeamCity']} {team['TeamName']}",
                        'conference': team['Conference'],
                        'conference_record': team['ConferenceRecord'],
                        'playoff_rank': team['PlayoffRank'],
                        'clinic_rank': team['ClinchIndicator'],
                        'wins': team['WINS'],
                        'losses': team['LOSSES'],
                        'win_percentage': team['WinPCT'],
                        'home_record': team['HOME'],
                        'road_record': team['ROAD']
                    }
                    standings_list.append(team_dict)
                
                return {
                    'success': True,
                    'source': 'NBA_API',
                    'standings': standings_list
                }
            else:
                # 使用ESPN API作为备选
                response = self.espn_api.get('standings')
                
                standings_list = []
                # 处理ESPN API响应
                for conference in response.get('children', []):
                    for team in conference.get('standings', {}).get('entries', []):
                        team_info = team.get('team', {})
                        stats = team.get('stats', [])
                        
                        wins = 0
                        losses = 0
                        win_pct = 0.0
                        
                        for stat in stats:
                            if stat.get('name') == 'wins':
                                wins = stat.get('value', 0)
                            elif stat.get('name') == 'losses':
                                losses = stat.get('value', 0)
                            elif stat.get('name') == 'winPercent':
                                win_pct = stat.get('value', 0.0)
                        
                        team_dict = {
                            'team_id': team_info.get('id'),
                            'team_name': team_info.get('displayName'),
                            'conference': conference.get('name'),
                            'wins': wins,
                            'losses': losses,
                            'win_percentage': win_pct
                        }
                        standings_list.append(team_dict)
                
                return {
                    'success': True,
                    'source': 'ESPN_API',
                    'standings': standings_list
                }
                
        except Exception as e:
            self.logger.error(f"获取积分榜失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_league_standings(self) -> Dict[str, Any]:
        """
        获取联盟积分榜 - 别名方法
        
        Returns:
            积分榜字典
        """
        return self.get_standings()
    
    def get_team_schedule(self, team_id: int) -> Dict[str, Any]:
        """
        获取特定球队的赛程信息（使用ESPN API）
        
        Args:
            team_id: ESPN球队ID
            
        Returns:
            球队赛程字典
        """
        try:
            # 根据ESPN API文档构建URL
            endpoint = f'teams/{team_id}/schedule'
            response = self.espn_api.get(endpoint)
            
            games = []
            for event in response.get('events', []):
                game_dict = {
                    'id': event.get('id'),
                    'date': event.get('date'),
                    'name': event.get('name'),
                    'short_name': event.get('shortName'),
                    'status': {
                        'clock': event.get('status', {}).get('clock'),
                        'display_clock': event.get('status', {}).get('displayClock'),
                        'period': event.get('status', {}).get('period'),
                        'type': event.get('status', {}).get('type', {}).get('name'),
                        'detail': event.get('status', {}).get('type', {}).get('detail'),
                        'completed': event.get('status', {}).get('type', {}).get('completed', False)
                    },
                    'teams': [],
                    'venue': {
                        'name': event.get('competitions', [{}])[0].get('venue', {}).get('fullName'),
                        'city': event.get('competitions', [{}])[0].get('venue', {}).get('address', {}).get('city'),
                        'state': event.get('competitions', [{}])[0].get('venue', {}).get('address', {}).get('state')
                    }
                }
                
                # 获取比赛双方球队信息
                competition = event.get('competitions', [{}])[0]
                for competitor in competition.get('competitors', []):
                    team = competitor.get('team', {})
                    team_dict = {
                        'id': team.get('id'),
                        'name': team.get('displayName'),
                        'abbreviation': team.get('abbreviation'),
                        'logo': team.get('logo'),
                        'score': competitor.get('score'),
                        'home_away': competitor.get('homeAway'),
                        'winner': competitor.get('winner', False),
                        'record': competitor.get('records', [{}])[0].get('summary') if competitor.get('records') else None
                    }
                    game_dict['teams'].append(team_dict)
                
                games.append(game_dict)
            
            # 获取球队信息
            team_info = response.get('team', {})
            
            return {
                'success': True,
                'source': 'ESPN_API',
                'team': {
                    'id': team_info.get('id'),
                    'name': team_info.get('displayName'),
                    'abbreviation': team_info.get('abbreviation'),
                    'logo': team_info.get('logo')
                },
                'total_count': len(games),
                'schedule': games
            }
            
        except Exception as e:
            self.logger.error(f"获取球队赛程失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_schedule(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        获取赛程信息（使用ESPN API）
        
        Args:
            date_str: 日期字符串 (YYYY-MM-DD)，默认为今天
            
        Returns:
            赛程信息字典
        """
        try:
            # 使用ESPN API获取赛程
            params = {}
            if date_str:
                # 将日期转换为ESPN API需要的格式
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                params['dates'] = date_obj.strftime('%Y%m%d')
            
            response = self.espn_api.get('scoreboard', params=params)
            
            games = []
            for event in response.get('events', []):
                game_dict = {
                    'id': event.get('id'),
                    'date': event.get('date'),
                    'name': event.get('name'),
                    'short_name': event.get('shortName'),
                    'status': {
                        'clock': event.get('status', {}).get('clock'),
                        'display_clock': event.get('status', {}).get('displayClock'),
                        'period': event.get('status', {}).get('period'),
                        'type': event.get('status', {}).get('type', {}).get('name'),
                        'detail': event.get('status', {}).get('type', {}).get('detail')
                    },
                    'teams': [],
                    'venue': {
                        'name': event.get('competitions', [{}])[0].get('venue', {}).get('fullName'),
                        'city': event.get('competitions', [{}])[0].get('venue', {}).get('address', {}).get('city'),
                        'state': event.get('competitions', [{}])[0].get('venue', {}).get('address', {}).get('state')
                    }
                }
                
                # 获取比赛双方球队信息
                competition = event.get('competitions', [{}])[0]
                for competitor in competition.get('competitors', []):
                    team = competitor.get('team', {})
                    team_dict = {
                        'id': team.get('id'),
                        'name': team.get('displayName'),
                        'abbreviation': team.get('abbreviation'),
                        'logo': team.get('logo'),
                        'score': competitor.get('score'),
                        'home_away': competitor.get('homeAway'),
                        'winner': competitor.get('winner', False),
                        'record': competitor.get('records', [{}])[0].get('summary') if competitor.get('records') else None
                    }
                    game_dict['teams'].append(team_dict)
                
                games.append(game_dict)
            
            return {
                'success': True,
                'source': 'ESPN_API',
                'date': date_str or datetime.now().strftime('%Y-%m-%d'),
                'total_count': len(games),
                'games': games
            }
            
        except Exception as e:
            self.logger.error(f"获取赛程失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_player_stats(self, player_id: int, season: Optional[str] = None) -> Dict[str, Any]:
        """
        获取球员统计数据
        
        Args:
            player_id: 球员ID
            season: 赛季 (如: '2023-24')
            
        Returns:
            球员统计数据字典
        """
        try:
            if not NBA_API_AVAILABLE:
                return {
                    'success': False,
                    'error': 'NBA_API库未安装，无法获取球员统计'
                }
            
            # 获取球员生涯统计
            career_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
            
            # 获取常规赛统计
            season_totals = career_stats.get_data_frames()[0]
            
            stats_list = []
            for idx, season_stat in season_totals.iterrows():
                if season and season_stat['SEASON_ID'] != season:
                    continue
                
                stat_dict = {
                    'season': season_stat['SEASON_ID'],
                    'team_id': season_stat['TEAM_ID'],
                    'team_abbreviation': season_stat['TEAM_ABBREVIATION'],
                    'player_age': season_stat['PLAYER_AGE'],
                    'games_played': season_stat['GP'],
                    'games_started': season_stat['GS'],
                    'minutes': season_stat['MIN'],
                    'field_goals_made': season_stat['FGM'],
                    'field_goals_attempted': season_stat['FGA'],
                    'field_goal_percentage': season_stat['FG_PCT'],
                    'three_point_made': season_stat['FG3M'],
                    'three_point_attempted': season_stat['FG3A'],
                    'three_point_percentage': season_stat['FG3_PCT'],
                    'free_throws_made': season_stat['FTM'],
                    'free_throws_attempted': season_stat['FTA'],
                    'free_throw_percentage': season_stat['FT_PCT'],
                    'offensive_rebounds': season_stat['OREB'],
                    'defensive_rebounds': season_stat['DREB'],
                    'total_rebounds': season_stat['REB'],
                    'assists': season_stat['AST'],
                    'steals': season_stat['STL'],
                    'blocks': season_stat['BLK'],
                    'turnovers': season_stat['TOV'],
                    'personal_fouls': season_stat['PF'],
                    'points': season_stat['PTS']
                }
                stats_list.append(stat_dict)
            
            return {
                'success': True,
                'player_id': player_id,
                'season': season,
                'stats': stats_list
            }
            
        except Exception as e:
            self.logger.error(f"获取球员统计失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_espn_teams(self) -> Dict[str, Any]:
        """
        获取ESPN NBA球队列表及其ID
        
        Returns:
            ESPN球队信息字典
        """
        try:
            # 使用ESPN API获取所有球队
            response = self.espn_api.get('teams')
            
            teams_list = []
            for team_group in response.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', []):
                team_info = team_group.get('team', {})
                team_dict = {
                    'espn_id': team_info.get('id'),
                    'full_name': team_info.get('displayName'),
                    'abbreviation': team_info.get('abbreviation'),
                    'nickname': team_info.get('name'),
                    'location': team_info.get('location'),
                    'logo': team_info.get('logo'),
                    'color': team_info.get('color'),
                    'alternate_color': team_info.get('alternateColor')
                }
                teams_list.append(team_dict)
            
            return {
                'success': True,
                'source': 'ESPN_API',
                'total_count': len(teams_list),
                'teams': teams_list
            }
            
        except Exception as e:
            self.logger.error(f"获取ESPN球队信息失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_lakers_schedule(self) -> Dict[str, Any]:
        """获取湖人队赛程（示例）"""
        return self.get_team_schedule(13)  # 湖人队的ESPN ID是13
    
    def get_warriors_schedule(self) -> Dict[str, Any]:
        """获取勇士队赛程（示例）"""
        return self.get_team_schedule(9)   # 勇士队的ESPN ID是9
    
    def get_team_schedule_by_name(self, team_name: str) -> Dict[str, Any]:
        """
        根据球队名称获取赛程
        
        Args:
            team_name: 球队名称（支持全名、缩写等多种格式）
            
        Returns:
            球队赛程字典
        """
        try:
            team_id = get_team_id(team_name)
            result = self.get_team_schedule(team_id)
            
            # 添加查询的球队名称信息
            if result.get('success'):
                result['queried_team'] = {
                    'input_name': team_name,
                    'espn_id': team_id,
                    'full_name': get_team_name(team_id)
                }
            
            return result
            
        except ValueError as e:
            self.logger.error(f"球队名称查找失败: {e}")
            return {
                'success': False,
                'error': f"未找到球队: {team_name}。请检查球队名称或使用 get_all_team_ids() 查看可用球队。"
            }
    
    def get_all_team_ids(self) -> Dict[str, Any]:
        """
        获取所有NBA球队的ESPN ID映射
        
        Returns:
            球队ID映射字典
        """
        try:
            teams = list_all_teams()
            
            return {
                'success': True,
                'total_count': len(teams),
                'teams': teams,
                'usage_examples': [
                    "get_team_schedule_by_name('Los Angeles Lakers')",
                    "get_team_schedule_by_name('LAL')",
                    "get_team_schedule_by_name('lakers')"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"获取球队ID映射失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_today_games(self) -> Dict[str, Any]:
        """获取今日比赛"""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.get_schedule(today)
    
    def get_team_games(self, team_id: int, season: Optional[str] = None) -> Dict[str, Any]:
        """
        获取球队比赛记录
        
        Args:
            team_id: 球队ID
            season: 赛季
            
        Returns:
            球队比赛记录字典
        """
        try:
            if not NBA_API_AVAILABLE:
                return {
                    'success': False,
                    'error': 'NBA_API库未安装，无法获取球队比赛记录'
                }
            
            # 获取球队比赛记录
            team_games = teamgamelog.TeamGameLog(team_id=team_id, season=season or '2023-24')
            games_data = team_games.get_data_frames()[0]
            
            games_list = []
            for idx, game in games_data.iterrows():
                game_dict = {
                    'game_id': game['Game_ID'],
                    'game_date': game['GAME_DATE'],
                    'matchup': game['MATCHUP'],
                    'is_win': game['WL'] == 'W',
                    'minutes': game['MIN'],
                    'points': game['PTS'],
                    'field_goals_made': game['FGM'],
                    'field_goals_attempted': game['FGA'],
                    'field_goal_percentage': game['FG_PCT'],
                    'three_point_made': game['FG3M'],
                    'three_point_attempted': game['FG3A'],
                    'free_throws_made': game['FTM'],
                    'free_throws_attempted': game['FTA'],
                    'offensive_rebounds': game['OREB'],
                    'defensive_rebounds': game['DREB'],
                    'total_rebounds': game['REB'],
                    'assists': game['AST'],
                    'steals': game['STL'],
                    'blocks': game['BLK'],
                    'turnovers': game['TOV'],
                    'personal_fouls': game['PF'],
                    'plus_minus': game['PLUS_MINUS']
                }
                games_list.append(game_dict)
            
            return {
                'success': True,
                'team_id': team_id,
                'season': season or '2023-24',
                'total_count': len(games_list),
                'games': games_list
            }
            
        except Exception as e:
            self.logger.error(f"获取球队比赛记录失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_team_players(self, team_name: str) -> Dict[str, Any]:
        """
        根据球队名称获取球员名单
        
        Args:
            team_name: 球队名称
            
        Returns:
            球员名单字典
        """
        try:
            team_id = get_team_id(team_name)
            
            # 尝试多个ESPN API端点
            endpoints = [
                f'teams/{team_id}/roster',
                f'teams/{team_id}',
                f'sports/basketball/nba/teams/{team_id}/roster'
            ]
            
            response = None
            for endpoint in endpoints:
                try:
                    response = self.espn_api.get(endpoint)
                    if response and ('athletes' in response or 'team' in response):
                        break
                except Exception as e:
                    self.logger.warning(f"端点 {endpoint} 失败: {e}")
                    continue
            
            if not response:
                # 如果ESPN API失败，尝试直接HTTP请求
                import requests
                try:
                    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/roster"
                    resp = requests.get(url, timeout=10)
                    if resp.status_code == 200:
                        response = resp.json()
                    else:
                        # 尝试另一个URL
                        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}"
                        resp = requests.get(url, timeout=10)
                        if resp.status_code == 200:
                            response = resp.json()
                except Exception as e:
                    self.logger.error(f"直接HTTP请求也失败: {e}")
            
            if not response:
                # 最后尝试：使用NBA_API库作为备选
                if NBA_API_AVAILABLE:
                    return self._get_team_players_fallback(team_name, team_id)
                else:
                    return {
                        'success': False,
                        'error': f'无法获取 {team_name} 的球员数据，ESPN API不可用且NBA_API库未安装'
                    }
            
            # 处理不同的响应结构
            athletes_data = []
            if 'athletes' in response:
                athletes_data = response['athletes']
            elif 'team' in response and 'athletes' in response['team']:
                athletes_data = response['team']['athletes']
            
            players_list = []
            for athlete in athletes_data:
                # 支持多种数据结构
                if 'athlete' in athlete:
                    player_info = athlete['athlete']
                    roster_info = athlete
                else:
                    player_info = athlete
                    roster_info = athlete
                
                # 处理姓名字段
                full_name = player_info.get('fullName') or player_info.get('displayName') or ''
                display_name = player_info.get('displayName') or player_info.get('name') or ''
                
                # 尝试从fullName中分离first_name和last_name
                first_name = ''
                last_name = ''
                if full_name:
                    name_parts = full_name.split()
                    if len(name_parts) >= 2:
                        first_name = name_parts[0]
                        last_name = ' '.join(name_parts[1:])
                    else:
                        first_name = full_name
                        last_name = ''
                elif display_name:
                    name_parts = display_name.split()
                    if len(name_parts) >= 2:
                        first_name = name_parts[0]
                        last_name = ' '.join(name_parts[1:])
                    else:
                        first_name = display_name
                        last_name = ''
                
                # 如果仍然没有姓名，使用jersey号码
                if not first_name and not last_name:
                    jersey = roster_info.get('jersey') or player_info.get('jersey') or 'Unknown'
                    first_name = f"Player #{jersey}"
                    last_name = ""
                
                # 处理身高和体重
                height_info = player_info.get('height', 0)
                weight_info = player_info.get('weight', 0)
                
                # 将身高转换为英尺和英寸
                height_feet = None
                height_inches = None
                if height_info and height_info > 0:
                    total_inches = height_info
                    height_feet = total_inches // 12
                    height_inches = total_inches % 12
                
                # 体重转换
                weight_pounds = weight_info if weight_info else None
                
                # 处理位置信息
                position = None
                position_name = None
                if 'position' in roster_info:
                    pos_info = roster_info['position']
                    if isinstance(pos_info, dict):
                        position = pos_info.get('abbreviation')
                        position_name = pos_info.get('displayName')
                    else:
                        position = str(pos_info)
                elif 'position' in player_info:
                    pos_info = player_info['position']
                    if isinstance(pos_info, dict):
                        position = pos_info.get('abbreviation')
                        position_name = pos_info.get('displayName')
                    else:
                        position = str(pos_info)
                
                player_dict = {
                    'id': player_info.get('id'),
                    'full_name': full_name or display_name or f"Player #{roster_info.get('jersey', 'Unknown')}",
                    'first_name': first_name,
                    'last_name': last_name,
                    'display_name': display_name,
                    'short_name': player_info.get('shortName'),
                    'jersey': roster_info.get('jersey') or player_info.get('jersey'),
                    'position': position,
                    'position_name': position_name,
                    'height': height_info,
                    'height_feet': height_feet,
                    'height_inches': height_inches,
                    'weight': weight_info,
                    'weight_pounds': weight_pounds,
                    'age': player_info.get('age'),
                    'experience': roster_info.get('experience', {}).get('years') if isinstance(roster_info.get('experience'), dict) else roster_info.get('experience'),
                    'headshot': player_info.get('headshot', {}).get('href') if isinstance(player_info.get('headshot'), dict) else player_info.get('headshot')
                }
                players_list.append(player_dict)
            
            return {
                'success': True,
                'team_name': team_name,
                'espn_team_id': team_id,
                'total_players': len(players_list),
                'players': players_list
            }
            
        except ValueError as e:
            self.logger.error(f"球队名称查找失败: {e}")
            return {
                'success': False,
                'error': f"未找到球队: {team_name}"
            }
        except Exception as e:
            self.logger.error(f"获取球队球员失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_player_stats_by_name(self, player_name: str, season: Optional[str] = None) -> Dict[str, Any]:
        """
        根据球员名称获取统计数据
        
        Args:
            player_name: 球员名称
            season: 赛季 (如: '2023-24')
            
        Returns:
            球员统计数据字典
        """
        try:
            if not NBA_API_AVAILABLE:
                return {
                    'success': False,
                    'error': 'NBA_API库未安装，无法获取球员统计'
                }
            
            # 查找球员ID
            players_data = players.find_players_by_full_name(player_name)
            if not players_data:
                # 尝试模糊匹配
                all_players = players.get_active_players()
                matched_players = [p for p in all_players if player_name.lower() in p['full_name'].lower()]
                if matched_players:
                    players_data = [matched_players[0]]  # 取第一个匹配的
                else:
                    return {
                        'success': False,
                        'error': f'未找到球员: {player_name}'
                    }
            
            player_info = players_data[0]
            player_id = player_info['id']
            
            # 获取球员统计数据
            stats_result = self.get_player_stats(player_id, season)
            
            if stats_result['success']:
                stats_result['player_info'] = {
                    'id': player_id,
                    'full_name': player_info['full_name'],
                    'first_name': player_info.get('first_name'),
                    'last_name': player_info.get('last_name'),
                    'is_active': player_info.get('is_active', True)
                }
            
            return stats_result
            
        except Exception as e:
            self.logger.error(f"根据名称获取球员统计失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_team_players_fallback(self, team_name: str, espn_team_id: int) -> Dict[str, Any]:
        """
        备选方案：使用NBA_API获取球员信息
        
        Args:
            team_name: 球队名称
            espn_team_id: ESPN球队ID
            
        Returns:
            球员列表字典
        """
        try:
            # 将ESPN ID转换为NBA API ID
            nba_teams = teams.get_teams()
            nba_team = None
            
            # 根据球队名称匹配
            for team in nba_teams:
                if (team_name.lower() in team['full_name'].lower() or 
                    team_name.lower() in team['nickname'].lower() or
                    team_name.lower() == team['abbreviation'].lower()):
                    nba_team = team
                    break
            
            if not nba_team:
                return {
                    'success': False,
                    'error': f'无法在NBA_API中找到对应的球队: {team_name}'
                }
            
            nba_team_id = nba_team['id']
            
            # 获取球队阵容
            roster = commonteamroster.CommonTeamRoster(team_id=nba_team_id)
            roster_data = roster.get_data_frames()[0]
            
            players_list = []
            for idx, player in roster_data.iterrows():
                # 处理姓名
                full_name = player['PLAYER']
                name_parts = full_name.split()
                first_name = name_parts[0] if name_parts else ''
                last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                
                # 处理身高
                height_str = str(player.get('HEIGHT', ''))
                height_feet = None
                height_inches = None
                if height_str and '-' in height_str:
                    try:
                        feet, inches = height_str.split('-')
                        height_feet = int(feet)
                        height_inches = int(inches)
                    except:
                        pass
                
                # 处理体重
                weight_str = str(player.get('WEIGHT', ''))
                weight_pounds = None
                if weight_str.isdigit():
                    weight_pounds = int(weight_str)
                
                player_dict = {
                    'id': player['PLAYER_ID'],
                    'full_name': full_name,
                    'first_name': first_name,
                    'last_name': last_name,
                    'display_name': full_name,
                    'short_name': full_name,
                    'jersey': player.get('NUM'),
                    'position': player.get('POSITION'),
                    'position_name': player.get('POSITION'),
                    'height': height_feet * 12 + height_inches if height_feet and height_inches else None,
                    'height_feet': height_feet,
                    'height_inches': height_inches,
                    'weight': weight_pounds,
                    'weight_pounds': weight_pounds,
                    'age': player.get('AGE'),
                    'experience': player.get('EXP'),
                    'headshot': None
                }
                players_list.append(player_dict)
            
            return {
                'success': True,
                'team_name': team_name,
                'espn_team_id': espn_team_id,
                'nba_team_id': nba_team_id,
                'total_players': len(players_list),
                'players': players_list,
                'source': 'NBA_API_fallback'
            }
            
        except Exception as e:
            self.logger.error(f"NBA_API备选方案失败: {e}")
            return {
                'success': False,
                'error': f'NBA_API备选方案也失败: {str(e)}'
            } 