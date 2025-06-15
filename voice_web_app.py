#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音集成Web应用
集成语音查询功能的体育数据Web应用
支持WebSocket实时更新和语音交互
"""

import os
import sys
import json
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading

# 导入语音查询系统
from voice_query_system import VoiceQuerySystem, QueryParser

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

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sports_voice_query_2025'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# 初始化SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 全局变量
voice_system = None
query_parser = None
active_sessions = {}


class VoiceWebApp:
    """语音Web应用控制器"""
    
    def __init__(self):
        """初始化语音Web应用"""
        global voice_system, query_parser
        
        logger.info("初始化语音Web应用...")
        
        # 初始化后端API
        self.f1_api = F1DataAPI()
        self.football_api = FootballDataAPI()
        self.nba_api = NBADataAPI()
        
        # 初始化查询解析器
        query_parser = QueryParser()
        
        # 初始化语音系统（在后台线程中）
        self.init_voice_system_async()
        
        logger.info("语音Web应用初始化完成")
    
    def init_voice_system_async(self):
        """异步初始化语音系统"""
        def init_voice():
            global voice_system
            try:
                print("🔄 开始初始化语音系统...")
                print("📥 正在下载语音识别模型（首次使用需要下载，请耐心等待）...")
                
                logger.info("后台初始化语音系统...")
                voice_system = VoiceQuerySystem()
                
                print("✅ 语音系统初始化完成！")
                logger.info("✅ 语音系统初始化完成")
                # 通知所有客户端语音系统已就绪
                socketio.emit('voice_system_ready', {'status': 'ready'})
            except Exception as e:
                print(f"❌ 语音系统初始化失败: {e}")
                logger.error(f"❌ 语音系统初始化失败: {e}")
                socketio.emit('voice_system_error', {'error': str(e)})
        
        thread = threading.Thread(target=init_voice)
        thread.daemon = True
        thread.start()


# 初始化应用
web_app = VoiceWebApp()


# ==================== Web路由 ====================

@app.route('/')
def index():
    """主页"""
    return render_template('voice_index.html')

@app.route('/voice')
def voice_page():
    """语音查询页面"""
    return render_template('voice_query.html')

@app.route('/f1')
def f1_page():
    """F1页面"""
    return render_template('f1.html')

@app.route('/football')
def football_page():
    """足球页面"""
    return render_template('football.html')

@app.route('/nba')
def nba_page():
    """NBA页面"""
    return render_template('nba.html')


# ==================== API路由 ====================

@app.route('/api/voice/status')
def voice_status():
    """获取语音系统状态"""
    global voice_system
    return jsonify({
        'ready': voice_system is not None,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/voice/parse', methods=['POST'])
def parse_query():
    """解析查询文本"""
    global query_parser
    
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'success': False, 'error': '文本不能为空'})
    
    try:
        result = query_parser.parse_query(text)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/voice/query', methods=['POST'])
def execute_voice_query():
    """执行语音查询"""
    data = request.get_json()
    query_info = data.get('query_info')
    
    if not query_info:
        return jsonify({'success': False, 'error': '查询信息不能为空'})
    
    try:
        # 执行查询
        result = execute_query(query_info)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/cache/options/<sport>/<query_type>')
def get_cached_options(sport, query_type):
    """获取缓存的查询选项"""
    try:
        options = query_cache.get_available_options(sport, query_type)
        return jsonify({
            'success': True,
            'sport': sport,
            'query_type': query_type,
            'options': options,
            'count': len(options)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/cache/result/<sport>/<cache_key>')
def get_cached_result(sport, cache_key):
    """获取缓存的查询结果"""
    try:
        result = query_cache.get_query_result(sport, cache_key)
        if result:
            return jsonify({
                'success': True,
                'result': result
            })
        else:
            return jsonify({
                'success': False,
                'error': '未找到缓存结果'
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """清理缓存"""
    try:
        data = request.get_json() or {}
        sport = data.get('sport')  # 可选，指定体育项目
        
        query_cache.clear_cache(sport)
        return jsonify({
            'success': True,
            'message': f'缓存已清理{"（" + sport + "）" if sport else ""}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ==================== F1 API路由 ====================

@app.route('/api/f1/schedule')
def f1_schedule():
    """F1赛程"""
    try:
        data = web_app.f1_api.get_current_season_schedule()
        return jsonify(data)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/f1/driver-standings/<int:year>')
def f1_driver_standings(year):
    """F1车手积分榜"""
    try:
        data = web_app.f1_api.get_driver_standings(year)
        return jsonify(data)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/f1/constructor-standings/<int:year>')
def f1_constructor_standings(year):
    """F1车队积分榜"""
    try:
        data = web_app.f1_api.get_constructor_standings(year)
        return jsonify(data)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ==================== 足球API路由 ====================

@app.route('/api/football/standings/<int:league_id>')
def football_standings(league_id):
    """足球积分榜"""
    try:
        data = web_app.football_api.get_standings(league_id)
        return jsonify(data)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/football/today-matches')
def football_today_matches():
    """今日足球比赛"""
    try:
        data = web_app.football_api.get_today_matches()
        return jsonify(data)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ==================== NBA API路由 ====================

@app.route('/api/nba/teams')
def nba_teams():
    """NBA球队"""
    try:
        data = web_app.nba_api.get_teams()
        return jsonify(data)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/nba/standings')
def nba_standings():
    """NBA积分榜"""
    try:
        data = web_app.nba_api.get_league_standings()
        return jsonify(data)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/nba/team-schedule/<team_name>')
def nba_team_schedule(team_name):
    """NBA球队赛程"""
    try:
        data = web_app.nba_api.get_team_schedule_by_name(team_name)
        return jsonify(data)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/nba/players/<team_name>')
def nba_team_players(team_name):
    """NBA球队球员"""
    try:
        data = web_app.nba_api.get_team_players(team_name)
        return jsonify(data)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ==================== WebSocket事件 ====================

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    session_id = request.sid
    active_sessions[session_id] = {
        'connected_at': datetime.now(),
        'queries': []
    }
    
    logger.info(f"客户端连接: {session_id}")
    
    # 发送语音系统状态
    global voice_system
    emit('voice_system_status', {
        'ready': voice_system is not None,
        'session_id': session_id
    })

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接"""
    session_id = request.sid
    if session_id in active_sessions:
        del active_sessions[session_id]
    
    logger.info(f"客户端断开连接: {session_id}")

@socketio.on('get_recordings')
def handle_get_recordings():
    """获取录音文件列表"""
    global voice_system
    session_id = request.sid
    
    if not voice_system:
        emit('voice_query_error', {'error': '语音系统未就绪'})
        return
    
    logger.info(f"获取录音列表: {session_id}")
    
    try:
        result = voice_system.list_recordings()
        
        if result['success']:
            emit('recordings_list', {
                'recordings': result['recordings'],
                'count': result['count']
            })
        else:
            emit('voice_query_error', {
                'error': result['error']
            })
            
    except Exception as e:
        logger.error(f"获取录音列表异常: {e}")
        emit('voice_query_error', {
            'error': str(e)
        })

@socketio.on('get_latest_recording')
def handle_get_latest_recording():
    """获取最新录音文件"""
    global voice_system
    session_id = request.sid
    
    if not voice_system:
        emit('voice_query_error', {'error': '语音系统未就绪'})
        return
    
    logger.info(f"获取最新录音: {session_id}")
    
    try:
        result = voice_system.get_latest_recording()
        
        if result['success']:
            emit('recording_complete', {
                'audio_file': result['audio_file'],
                'message': result['message']
            })
        else:
            emit('voice_query_error', {
                'error': result['error']
            })
            
    except Exception as e:
        logger.error(f"获取最新录音异常: {e}")
        emit('voice_query_error', {
            'error': str(e)
        })

@socketio.on('recognize_audio')
def handle_recognize_audio(data):
    """识别音频文件"""
    global voice_system
    session_id = request.sid
    audio_file = data.get('audio_file')
    
    if not voice_system or not voice_system.speech_recognizer:
        emit('voice_query_error', {'error': '语音识别系统未就绪'})
        return
    
    if not audio_file:
        emit('voice_query_error', {'error': '音频文件路径为空'})
        return
    
    # 清理路径用于日志显示
    clean_audio_file = audio_file.replace('\r', '').replace('\n', '').strip()
    logger.info(f"开始识别音频: {session_id} - {clean_audio_file}")
    emit('voice_query_status', {'status': 'recognizing', 'message': '正在识别语音...'})
    
    # 在后台线程中执行识别
    def recognition_thread():
        try:
            result = voice_system.recognize_audio_file(audio_file)
            
            if result['success']:
                # 识别成功
                socketio.emit('recognition_complete', {
                    'text': result['text'],
                    'recognition_result': result['recognition_result']
                }, room=session_id)
            else:
                # 识别失败
                socketio.emit('voice_query_error', {
                    'error': result['error']
                }, room=session_id)
                
        except Exception as e:
            logger.error(f"语音识别异常: {e}")
            socketio.emit('voice_query_error', {
                'error': str(e)
            }, room=session_id)
    
    thread = threading.Thread(target=recognition_thread)
    thread.daemon = True
    thread.start()

@socketio.on('process_query')
def handle_process_query(data):
    """处理查询文本"""
    global voice_system
    session_id = request.sid
    text = data.get('text')
    
    if not voice_system:
        emit('voice_query_error', {'error': '查询系统未就绪'})
        return
    
    if not text:
        emit('voice_query_error', {'error': '查询文本为空'})
        return
    
    logger.info(f"处理查询: {session_id} - {text}")
    emit('voice_query_status', {'status': 'processing', 'message': '正在处理查询...'})
    
    # 在后台线程中执行查询
    def query_thread():
        try:
            result = voice_system.process_query_text(text)
            
            if result['success']:
                # 查询成功，发送结果
                socketio.emit('voice_query_success', {
                    'text': result['text'],
                    'query_info': result['query_info'],
                    'data': result['data'],
                    'timestamp': result['timestamp']
                }, room=session_id)
                
                # 记录查询历史
                if session_id in active_sessions:
                    active_sessions[session_id]['queries'].append(result)
                
            else:
                # 查询失败
                socketio.emit('voice_query_error', {
                    'error': result['error'],
                    'suggestion': result.get('suggestion', '')
                }, room=session_id)
                
        except Exception as e:
            logger.error(f"查询处理异常: {e}")
            socketio.emit('voice_query_error', {
                'error': str(e)
            }, room=session_id)
    
    thread = threading.Thread(target=query_thread)
    thread.daemon = True
    thread.start()

@socketio.on('text_query')
def handle_text_query(data):
    """处理文本查询"""
    global query_parser
    session_id = request.sid
    text = data.get('text', '')
    
    if not text:
        emit('query_error', {'error': '文本不能为空'})
        return
    
    try:
        # 解析查询
        query_info = query_parser.parse_query(text)
        
        if query_info['confidence'] < 0.3:
            emit('query_error', {
                'error': '无法理解查询意图',
                'suggestion': '请尝试说得更清楚，例如：查询F1积分榜'
            })
            return
        
        # 执行查询
        query_result = execute_query(query_info)
        
        # 发送结果
        result = {
            'text': text,
            'query_info': query_info,
            'data': query_result,
            'timestamp': datetime.now().isoformat()
        }
        
        emit('query_success', result)
        
        # 记录查询历史
        if session_id in active_sessions:
            active_sessions[session_id]['queries'].append(result)
            
    except Exception as e:
        logger.error(f"文本查询异常: {e}")
        emit('query_error', {'error': str(e)})

@socketio.on('get_query_history')
def handle_get_query_history():
    """获取查询历史"""
    session_id = request.sid
    
    if session_id in active_sessions:
        queries = active_sessions[session_id]['queries']
        emit('query_history', {'queries': queries[-10:]})  # 最近10条
    else:
        emit('query_history', {'queries': []})


# ==================== 辅助函数 ====================

def execute_query(query_info: Dict[str, Any]) -> Dict[str, Any]:
    """执行查询"""
    sport = query_info['sport']
    query_type = query_info['query_type']
    params = query_info['parameters']
    
    logger.info(f"执行查询: {sport} - {query_type} - {params}")
    
    try:
        if sport == 'f1':
            return query_f1_data(query_type, params)
        elif sport == 'football':
            return query_football_data(query_type, params)
        elif sport == 'nba':
            return query_nba_data(query_type, params)
        else:
            return {"success": False, "error": f"不支持的体育项目: {sport}"}
            
    except Exception as e:
        logger.error(f"查询执行失败: {e}")
        return {"success": False, "error": str(e)}

def query_f1_data(query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """查询F1数据"""
    try:
        if query_type == 'schedule':
            return web_app.f1_api.get_current_season_schedule()
        elif query_type == 'standings':
            year = params.get('year', 2023)
            return web_app.f1_api.get_driver_standings(year)
        elif query_type == 'teams':
            year = params.get('year', 2023)
            return web_app.f1_api.get_constructor_standings(year)
        elif query_type == 'results':
            year = params.get('year', 2023)
            round_num = params.get('round', 1)
            return web_app.f1_api.get_race_results(year, round_num)
        else:
            return web_app.f1_api.get_current_season_schedule()
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def query_football_data(query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """查询足球数据"""
    try:
        if query_type == 'schedule' or query_type == 'today':
            return web_app.football_api.get_today_matches()
        elif query_type == 'standings':
            league_id = params.get('team', 2021)  # 默认英超
            return web_app.football_api.get_standings(league_id)
        elif query_type == 'live':
            return web_app.football_api.get_live_matches()
        else:
            return web_app.football_api.get_today_matches()
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def query_nba_data(query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """查询NBA数据"""
    try:
        if query_type == 'teams':
            return web_app.nba_api.get_teams()
        elif query_type == 'standings':
            return web_app.nba_api.get_league_standings()
        elif query_type == 'schedule':
            team = params.get('team', 'Lakers')
            return web_app.nba_api.get_team_schedule_by_name(team)
        elif query_type == 'players':
            team = params.get('team', 'Lakers')
            return web_app.nba_api.get_team_players(team)
        else:
            return web_app.nba_api.get_teams()
            
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500


if __name__ == '__main__':
    print("🎤 语音集成体育数据Web应用")
    print("=" * 60)
    print("功能特色:")
    print("  🎙️  语音查询 - 说话即可查询体育数据")
    print("  💬 文本查询 - 支持文字输入查询")
    print("  🔄 实时更新 - WebSocket实时数据推送")
    print("  📱 响应式设计 - 支持手机、平板、电脑")
    print("  🏆 多项目支持 - F1、足球、NBA数据")
    print("=" * 60)
    print("访问地址:")
    print("  🏠 主页: http://localhost:5000")
    print("  🎤 语音查询: http://localhost:5000/voice")
    print("  🏎️  F1数据: http://localhost:5000/f1")
    print("  ⚽ 足球数据: http://localhost:5000/football")
    print("  🏀 NBA数据: http://localhost:5000/nba")
    print("=" * 60)
    
    # 启动应用
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True
    ) 