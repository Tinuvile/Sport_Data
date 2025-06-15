#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音查询系统
集成语音录制、识别、关键词提取和体育数据查询
"""

import os
import sys
import time
import json
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import re

# 添加路径以导入模块
sys.path.append(str(Path(__file__).parent / "SpeechRecognition"))
sys.path.append(str(Path(__file__).parent))

# 导入语音相关模块
try:
    # 首先尝试直接导入
    sys.path.append("SpeechRecognition")
    from simple_voice_recorder import SimpleVoiceRecorder
    from speech_recognition import SpeechRecognizer
    import config as speech_config
except ImportError:
    try:
        # 备用导入方式
        from SpeechRecognition.simple_voice_recorder import SimpleVoiceRecorder
        from SpeechRecognition.speech_recognition import SpeechRecognizer
        import SpeechRecognition.config as speech_config
    except ImportError as e:
        print(f"⚠️ 语音模块导入失败: {e}")
        print("💡 语音功能将不可用，但文本查询仍可正常使用")
        SimpleVoiceRecorder = None
        SpeechRecognizer = None
        speech_config = None

# 导入后端API
from backend import F1DataAPI, FootballDataAPI, NBADataAPI

# 导入查询缓存
from query_cache import query_cache

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QueryParser:
    """查询解析器 - 从语音文本中提取查询意图和参数"""
    
    def __init__(self):
        """初始化查询解析器"""
        self.sport_keywords = {
            'f1': ['f1', 'F1', '一级方程式', '赛车', '车手', '车队', '积分榜', '比赛结果', '排位赛'],
            'football': ['足球', '英超', '西甲', '德甲', '意甲', '法甲', '联赛', '积分榜', '比赛', '球队', '射手榜'],
            'nba': ['nba', 'NBA', '篮球', '球队', '球员', '赛程', '湖人', '勇士', '凯尔特人', '库里', '詹姆斯', '杜兰特']
        }
        
        self.query_types = {
            'schedule': ['赛程', '比赛安排', '日程', '时间表'],
            'standings': ['积分榜', '排名', '排行榜', '榜单'],
            'results': ['结果', '比分', '成绩'],
            'teams': ['球队', '队伍', '车队'],
            'players': ['球员', '车手', '选手', '名单', '阵容'],
            'today': ['今天', '今日', '当天'],
            'live': ['实时', '直播', '现场'],
            'top_scorers': ['射手榜', '射手', '进球榜', '得分榜'],
            'player_stats': ['数据', '统计', '表现']
        }
        
        # 球员名称映射
        self.player_names = {
            'nba': {
                '库里': 'Stephen Curry',
                '斯蒂芬库里': 'Stephen Curry',
                '詹姆斯': 'LeBron James',
                '勒布朗詹姆斯': 'LeBron James',
                '杜兰特': 'Kevin Durant',
                '凯文杜兰特': 'Kevin Durant',
                '字母哥': 'Giannis Antetokounmpo',
                '安特托昆博': 'Giannis Antetokounmpo',
                '东契奇': 'Luka Doncic',
                '卢卡东契奇': 'Luka Doncic',
                '塔图姆': 'Jayson Tatum',
                '杰森塔图姆': 'Jayson Tatum',
                '约基奇': 'Nikola Jokic',
                '尼古拉约基奇': 'Nikola Jokic',
                '恩比德': 'Joel Embiid',
                '乔尔恩比德': 'Joel Embiid'
            }
        }
        
        self.team_names = {
            'nba': {
                # 洛杉矶湖人
                '湖人': 'Lakers',
                '湖人队': 'Lakers',
                '洛杉矶湖人': 'Lakers',
                # 金州勇士
                '勇士': 'Warriors',
                '勇士队': 'Warriors', 
                '金州勇士': 'Warriors',
                # 波士顿凯尔特人
                '凯尔特人': 'Celtics',
                '凯尔特人队': 'Celtics',
                '波士顿凯尔特人': 'Celtics',
                # 芝加哥公牛
                '公牛': 'Bulls',
                '公牛队': 'Bulls',
                '芝加哥公牛': 'Bulls',
                # 迈阿密热火
                '热火': 'Heat',
                '热火队': 'Heat',
                '迈阿密热火': 'Heat',
                # 其他热门球队
                '马刺': 'Spurs',
                '马刺队': 'Spurs',
                '圣安东尼奥马刺': 'Spurs',
                '火箭': 'Rockets',
                '火箭队': 'Rockets',
                '休斯顿火箭': 'Rockets',
                '雷霆': 'Thunder',
                '雷霆队': 'Thunder',
                '俄克拉荷马雷霆': 'Thunder',
                '快船': 'Clippers',
                '快船队': 'Clippers',
                '洛杉矶快船': 'Clippers',
                '尼克斯': 'Knicks',
                '尼克斯队': 'Knicks',
                '纽约尼克斯': 'Knicks',
                '篮网': 'Nets',
                '篮网队': 'Nets',
                '布鲁克林篮网': 'Nets',
                '76人': '76ers',
                '76人队': '76ers',
                '费城76人': '76ers',
                '雄鹿': 'Bucks',
                '雄鹿队': 'Bucks',
                '密尔沃基雄鹿': 'Bucks'
            },
            'football': {
                '英超': 2021,
                '西甲': 2014,
                '德甲': 2002,
                '意甲': 2019,
                '法甲': 2015
            }
        }
    
    def parse_query(self, text: str) -> Dict[str, Any]:
        """
        解析查询文本
        
        Args:
            text: 语音识别的文本
            
        Returns:
            解析结果字典
        """
        text = text.lower().strip()
        logger.info(f"解析查询文本: {text}")
        
        result = {
            'sport': None,
            'query_type': None,
            'parameters': {},
            'confidence': 0.0,
            'original_text': text
        }
        
        # 识别体育项目
        sport_scores = {}
        for sport, keywords in self.sport_keywords.items():
            score = sum(1 for keyword in keywords if keyword.lower() in text)
            if score > 0:
                sport_scores[sport] = score
        
        if sport_scores:
            result['sport'] = max(sport_scores, key=sport_scores.get)
            result['confidence'] += 0.3
        
        # 识别查询类型
        query_scores = {}
        for query_type, keywords in self.query_types.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                query_scores[query_type] = score
        
        if query_scores:
            result['query_type'] = max(query_scores, key=query_scores.get)
            result['confidence'] += 0.3
        
        # 特殊处理：如果包含球员名称，优先判断为球员查询
        if result['sport'] in self.player_names:
            for player_cn in self.player_names[result['sport']].keys():
                if player_cn in text:
                    # 更精确的判断：得分、数据、统计等关键词
                    if any(keyword in text for keyword in ['得分', '数据', '统计', '表现', '平均', '场均']):
                        result['query_type'] = 'player_stats'
                    else:
                        result['query_type'] = 'players'
                    result['confidence'] = max(result['confidence'], 0.8)
                    break
        
        # 特殊处理：如果是足球射手榜
        if result['sport'] == 'football' and ('射手' in text or '进球' in text):
            result['query_type'] = 'top_scorers'
            result['confidence'] = max(result['confidence'], 0.7)
        
        # 特殊处理：F1车队积分榜
        if result['sport'] == 'f1' and '车队' in text and '积分榜' in text:
            result['query_type'] = 'teams'
            result['confidence'] = max(result['confidence'], 0.9)
        
        # 特殊处理：F1车手积分榜
        if result['sport'] == 'f1' and '车手' in text and '积分榜' in text:
            result['query_type'] = 'standings'
            result['confidence'] = max(result['confidence'], 0.9)
        
        # 提取参数
        result['parameters'] = self._extract_parameters(text, result['sport'])
        if result['parameters']:
            result['confidence'] += 0.4
        
        logger.info(f"解析结果: {result}")
        return result
    
    def _extract_parameters(self, text: str, sport: str) -> Dict[str, Any]:
        """提取查询参数"""
        params = {}
        
        # 提取年份
        year_match = re.search(r'(\d{4})年?', text)
        if year_match:
            params['year'] = int(year_match.group(1))
        
        # 提取球员名称
        if sport in self.player_names:
            for player_cn, player_en in self.player_names[sport].items():
                if player_cn in text:
                    params['player'] = player_en
                    break
        
        # 提取球队名称或联赛信息
        if sport in self.team_names:
            for team_cn, team_en in self.team_names[sport].items():
                if team_cn in text:
                    if sport == 'football' and isinstance(team_en, int):
                        # 足球联赛ID
                        params['league_id'] = team_en
                    else:
                        # 球队名称
                        params['team'] = team_en
                    break
        
        # 提取轮次
        round_match = re.search(r'第?(\d+)轮', text)
        if round_match:
            params['round'] = int(round_match.group(1))
        
        return params


class VoiceQuerySystem:
    """语音查询系统主控制器"""
    
    def __init__(self):
        """初始化语音查询系统"""
        logger.info("初始化语音查询系统...")
        
        # 初始化组件
        self.recorder = SimpleVoiceRecorder() if SimpleVoiceRecorder else None
        self.speech_recognizer = None
        self.query_parser = QueryParser()
        
        # 初始化后端API
        self.f1_api = None
        self.football_api = None
        self.nba_api = None
        
        self._init_apis()
        if SpeechRecognizer and speech_config:
            self._init_speech_recognizer()
        else:
            logger.warning("语音识别模块不可用，跳过语音识别器初始化")
        
        # 状态管理
        self.is_recording = False
        self.last_query_result = None
        
        logger.info("语音查询系统初始化完成")
    
    def _init_apis(self):
        """初始化后端API"""
        try:
            logger.info("初始化后端API...")
            self.f1_api = F1DataAPI()
            self.football_api = FootballDataAPI()
            self.nba_api = NBADataAPI()
            logger.info("✅ 后端API初始化成功")
        except Exception as e:
            logger.error(f"❌ 后端API初始化失败: {e}")
    
    def _init_speech_recognizer(self):
        """初始化语音识别器"""
        try:
            print("🎤 正在初始化语音识别器...")
            print("📦 加载语音识别模型...")
            print("   - 主识别模型: paraformer-zh")
            print("   - VAD模型: fsmn-vad") 
            print("   - 标点模型: ct-punc")
            print("⏳ 首次使用需要下载模型文件，请稍候...")
            
            logger.info("初始化语音识别器...")
            self.speech_recognizer = SpeechRecognizer(
                model_name=speech_config.DEFAULT_MODEL,
                vad_model=speech_config.VAD_MODEL,
                punc_model=speech_config.PUNC_MODEL,
                device=speech_config.DEVICE
            )
            
            print("✅ 语音识别器初始化成功！")
            logger.info("✅ 语音识别器初始化成功")
        except Exception as e:
            print(f"❌ 语音识别器初始化失败: {e}")
            logger.error(f"❌ 语音识别器初始化失败: {e}")
    
    def get_latest_recording(self) -> Dict[str, Any]:
        """获取最新的录音文件"""
        try:
            from pathlib import Path
            
            recordings_dir = Path("recordings")
            if not recordings_dir.exists():
                return {"success": False, "error": "录音目录不存在，请先使用simple_voice_recorder.py录音"}
            
            # 查找最新的录音文件
            recordings = list(recordings_dir.glob("recording_*.wav"))
            if not recordings:
                return {"success": False, "error": "未找到录音文件，请先使用simple_voice_recorder.py录音"}
            
            latest_recording = max(recordings, key=lambda x: x.stat().st_mtime)
            
            return {
                "success": True,
                "audio_file": str(latest_recording),
                "message": f"找到最新录音: {latest_recording.name}"
            }
            
        except Exception as e:
            logger.error(f"❌ 获取录音文件失败: {e}")
            return {"success": False, "error": str(e)}
    
    def list_recordings(self) -> Dict[str, Any]:
        """列出所有录音文件"""
        try:
            from pathlib import Path
            
            recordings_dir = Path("recordings")
            if not recordings_dir.exists():
                return {"success": False, "error": "录音目录不存在"}
            
            recordings = list(recordings_dir.glob("recording_*.wav"))
            if not recordings:
                return {"success": False, "error": "未找到录音文件"}
            
            # 按时间排序，最新的在前
            recordings.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            recording_list = []
            for recording in recordings[:10]:  # 只返回最新的10个
                stat = recording.stat()
                size_kb = stat.st_size / 1024
                mtime = datetime.fromtimestamp(stat.st_mtime)
                
                recording_list.append({
                    "filename": recording.name,
                    "path": str(recording),
                    "size_kb": round(size_kb, 1),
                    "time": mtime.strftime("%Y-%m-%d %H:%M:%S")
                })
            
            return {
                "success": True,
                "recordings": recording_list,
                "count": len(recording_list)
            }
            
        except Exception as e:
            logger.error(f"❌ 列出录音文件失败: {e}")
            return {"success": False, "error": str(e)}
    
    def recognize_audio_file(self, audio_file_path: str) -> Dict[str, Any]:
        """第二步：识别音频文件 - 调用已验证工作的manual_recognize函数"""
        logger.info(f"🤖 开始识别音频文件: {audio_file_path}")
        
        try:
            import subprocess
            import sys
            import os
            from pathlib import Path
            
            # 处理路径 - 确保文件存在
            # 清理路径字符串，移除可能的控制字符
            clean_path = audio_file_path.replace('\r', '').replace('\n', '').strip()
            audio_path = Path(clean_path)
            
            if not audio_path.exists():
                # 尝试在recordings目录中查找
                if not audio_path.is_absolute():
                    audio_path = Path("recordings") / audio_path.name
                    if not audio_path.exists():
                        return {"success": False, "error": f"音频文件不存在: {clean_path}"}
            
            logger.info(f"📁 使用音频文件: {audio_path}")
            
            # 使用subprocess调用manual_recognize.py，这样可以避免路径和导入问题
            speech_dir = Path(__file__).parent / "SpeechRecognition"
            script_path = speech_dir / "manual_recognize.py"
            
            # 构建命令，使用绝对路径
            cmd = [
                sys.executable,  # Python解释器路径
                str(script_path),  # 脚本路径
                "--file",
                str(audio_path.absolute())  # 音频文件绝对路径
            ]
            
            logger.info(f"🔧 执行命令: {' '.join(cmd)}")
            
            # 执行命令并捕获输出
            # 在Windows上设置正确的编码环境
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            result = subprocess.run(
                cmd,
                cwd=str(speech_dir),  # 在SpeechRecognition目录中执行
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # 替换无法解码的字符
                env=env  # 使用修改后的环境变量
            )
            
            if result.returncode == 0:
                # 解析输出，查找识别文本
                output_lines = result.stdout.split('\n')
                recognized_text = None
                
                # 收集所有可能的识别文本行
                potential_texts = []
                for line in output_lines:
                    if ('识别文本:' in line) or ('ʶı:' in line) or ('ʶ' in line and ':' in line):
                        if ':' in line:
                            text = line.split(':')[-1].strip()
                            if text and not text.endswith('.wav') and 'recording_' not in text:
                                potential_texts.append(text)
                
                # 选择最合适的识别文本（通常是最后一个非空的）
                if potential_texts:
                    recognized_text = potential_texts[-1]
                
                if recognized_text:
                    logger.info(f"📝 识别文本: {recognized_text}")
                    return {
                        "success": True,
                        "text": recognized_text,
                        "recognition_result": {"text": recognized_text}
                    }
                else:
                    # 调试输出
                    logger.warning("未找到识别结果，调试输出前10行:")
                    for i, line in enumerate(output_lines[:10]):
                        logger.warning(f"  行{i}: {line}")
                    return {"success": False, "error": "未找到识别结果，可能是音频质量问题或空白录音，请尝试其他录音文件"}
            else:
                error_msg = result.stderr or result.stdout or "未知错误"
                logger.error(f"❌ 识别进程失败: {error_msg}")
                return {"success": False, "error": f"语音识别进程失败: {error_msg}"}
            
        except Exception as e:
            logger.error(f"❌ 语音识别异常: {e}")
            return {"success": False, "error": f"语音识别系统异常: {str(e)}"}
    
    def process_query_text(self, text: str) -> Dict[str, Any]:
        """第三步：处理查询文本"""
        logger.info(f"🧠 处理查询文本: {text}")
        
        try:
            # 1. 查询解析
            query_info = self.query_parser.parse_query(text)
            
            if query_info['confidence'] < 0.3:
                return {
                    "success": False, 
                    "error": "无法理解查询意图",
                    "text": text,
                    "suggestion": "请尝试说得更清楚，例如：'查询F1积分榜'或'湖人队赛程'"
                }
            
            # 2. 执行查询
            logger.info("🔍 执行数据查询...")
            query_result = self._execute_query(query_info)
            
            # 3. 存储查询结果到缓存
            cache_key = query_cache.store_query_result(
                sport=query_info['sport'],
                query_type=query_info['query_type'],
                parameters=query_info['parameters'],
                result_data=query_result,
                original_text=text
            )
            
            # 4. 返回结果
            result = {
                "success": True,
                "text": text,
                "query_info": query_info,
                "data": query_result,
                "cache_key": cache_key,
                "timestamp": datetime.now().isoformat()
            }
            
            self.last_query_result = result
            return result
            
        except Exception as e:
            logger.error(f"❌ 查询处理失败: {e}")
            return {"success": False, "error": str(e)}
    
    def start_voice_query(self) -> Dict[str, Any]:
        """完整的语音查询流程（分步执行）"""
        logger.info("🎤 开始语音查询流程")
        
        try:
            # 步骤1：录音
            record_result = self.record_audio()
            if not record_result['success']:
                return record_result
            
            audio_file = record_result['audio_file']
            
            # 步骤2：识别
            recognize_result = self.recognize_audio_file(audio_file)
            if not recognize_result['success']:
                return recognize_result
            
            text = recognize_result['text']
            
            # 步骤3：查询
            query_result = self.process_query_text(text)
            return query_result
            
        except Exception as e:
            logger.error(f"❌ 语音查询失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_query(self, query_info: Dict[str, Any]) -> Dict[str, Any]:
        """执行具体的数据查询"""
        sport = query_info['sport']
        query_type = query_info['query_type']
        params = query_info['parameters']
        
        logger.info(f"执行查询: {sport} - {query_type} - {params}")
        
        try:
            if sport == 'f1':
                return self._query_f1_data(query_type, params)
            elif sport == 'football':
                return self._query_football_data(query_type, params)
            elif sport == 'nba':
                return self._query_nba_data(query_type, params)
            else:
                return {"success": False, "error": f"不支持的体育项目: {sport}"}
                
        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _query_f1_data(self, query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """查询F1数据"""
        if not self.f1_api:
            return {"success": False, "error": "F1 API未初始化"}
        
        try:
            if query_type == 'schedule':
                return self.f1_api.get_current_season_schedule()
            elif query_type == 'standings':
                year = params.get('year', 2023)
                return self.f1_api.get_driver_standings(year)
            elif query_type == 'teams':
                year = params.get('year', 2023)
                return self.f1_api.get_constructor_standings(year)
            elif query_type == 'results':
                year = params.get('year', 2023)
                round_num = params.get('round', 1)
                return self.f1_api.get_race_results(year, round_num)
            else:
                return self.f1_api.get_current_season_schedule()
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _query_football_data(self, query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """查询足球数据"""
        if not self.football_api:
            return {"success": False, "error": "足球API未初始化"}
        
        try:
            if query_type == 'schedule' or query_type == 'today':
                return self.football_api.get_today_matches()
            elif query_type == 'standings':
                league_id = params.get('league_id', 2021)  # 默认英超
                season = params.get('year')  # 获取年份参数
                return self.football_api.get_standings(league_id, season=season)
            elif query_type == 'top_scorers':
                league_id = params.get('league_id', 2021)  # 默认英超
                season = params.get('year')  # 获取年份参数
                return self.football_api.get_top_scorers(league_id, season=season)
            elif query_type == 'live':
                return self.football_api.get_live_matches()
            else:
                return self.football_api.get_today_matches()
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _query_nba_data(self, query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """查询NBA数据"""
        if not self.nba_api:
            return {"success": False, "error": "NBA API未初始化"}
        
        try:
            season = params.get('year')  # 获取年份参数
            
            if query_type == 'teams':
                return self.nba_api.get_teams()
            elif query_type == 'standings':
                # NBA API通常使用当前赛季，但可以扩展支持历史赛季
                return self.nba_api.get_league_standings()
            elif query_type == 'schedule':
                team = params.get('team', 'Lakers')
                return self.nba_api.get_team_schedule_by_name(team)
            elif query_type == 'players':
                if 'player' in params:
                    # 查询特定球员信息
                    player_name = params['player']
                    # 这里可以扩展为查询球员详细信息
                    return {"success": True, "player": player_name, "message": f"查询球员: {player_name}"}
                elif 'team' in params:
                    # 查询球队球员名单
                    team = params['team']
                    return self.nba_api.get_team_players(team)
                else:
                    return {"success": False, "error": "请指定球队或球员名称"}
            elif query_type == 'player_stats':
                if 'player' in params:
                    player_name = params['player']
                    # 传递赛季参数给球员统计查询
                    season_str = f"{season}-{str(season+1)[2:]}" if season else None
                    return self.nba_api.get_player_stats_by_name(player_name, season=season_str)
                else:
                    return {"success": False, "error": "请指定球员名称"}
            else:
                return self.nba_api.get_teams()
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_last_result(self) -> Optional[Dict[str, Any]]:
        """获取最后一次查询结果"""
        return self.last_query_result
    
    def test_system(self):
        """测试系统各组件"""
        print("🧪 测试语音查询系统")
        print("=" * 50)
        
        # 测试录音器
        print("1. 测试录音器...")
        try:
            self.recorder.test_microphone(duration=2)
            print("✅ 录音器测试通过")
        except Exception as e:
            print(f"❌ 录音器测试失败: {e}")
        
        # 测试语音识别器
        print("\n2. 测试语音识别器...")
        if self.speech_recognizer:
            print("✅ 语音识别器已初始化")
        else:
            print("❌ 语音识别器未初始化")
        
        # 测试后端API
        print("\n3. 测试后端API...")
        apis = [
            ("F1 API", self.f1_api),
            ("足球API", self.football_api),
            ("NBA API", self.nba_api)
        ]
        
        for name, api in apis:
            if api:
                print(f"✅ {name} 已初始化")
            else:
                print(f"❌ {name} 未初始化")
        
        # 测试查询解析器
        print("\n4. 测试查询解析器...")
        test_queries = [
            "查询F1车手积分榜",
            "湖人队的赛程",
            "英超积分榜",
            "今天的足球比赛"
        ]
        
        for query in test_queries:
            result = self.query_parser.parse_query(query)
            print(f"  '{query}' -> {result['sport']}, {result['query_type']} (置信度: {result['confidence']:.2f})")
        
        print("\n🎯 系统测试完成")


def main():
    """主函数"""
    print("🎤 语音查询体育数据系统")
    print("=" * 60)
    print("功能说明:")
    print("  1. 按回车开始语音查询")
    print("  2. 说出查询需求（如：'查询F1积分榜'）")
    print("  3. 系统自动识别并返回数据")
    print("  4. 输入 'test' 测试系统")
    print("  5. 输入 'quit' 退出")
    print("=" * 60)
    
    # 初始化系统
    try:
        system = VoiceQuerySystem()
    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        return
    
    while True:
        try:
            command = input("\n请按回车开始语音查询，或输入命令: ").strip().lower()
            
            if command == 'quit':
                print("👋 退出系统")
                break
            elif command == 'test':
                system.test_system()
                continue
            elif command == 'last':
                result = system.get_last_result()
                if result:
                    print(f"📋 最后查询结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
                else:
                    print("📋 暂无查询历史")
                continue
            
            # 开始语音查询
            print("\n🚀 开始语音查询...")
            result = system.start_voice_query()
            
            if result['success']:
                print("\n✅ 查询成功!")
                print(f"📝 识别文本: {result['text']}")
                print(f"🎯 查询类型: {result['query_info']['sport']} - {result['query_info']['query_type']}")
                print(f"📊 数据结果: {json.dumps(result['data'], ensure_ascii=False, indent=2)}")
            else:
                print(f"\n❌ 查询失败: {result['error']}")
                if 'suggestion' in result:
                    print(f"💡 建议: {result['suggestion']}")
                
        except KeyboardInterrupt:
            print("\n👋 用户中断，退出系统")
            break
        except Exception as e:
            print(f"\n❌ 系统错误: {e}")


if __name__ == "__main__":
    main() 