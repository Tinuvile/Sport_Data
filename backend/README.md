# 🏆 体育数据后端模块

这是一个综合性的体育数据后端系统，支持 F1、足球和 NBA 三大体育项目的数据获取。

## 📊 支持的数据源

### 🏎️ F1 数据 (FastF1)

- **赛程信息**: 当前赛季完整赛程
- **比赛结果**: 正赛、排位赛结果
- **车手数据**: 车手积分榜、个人统计
- **车队数据**: 车队积分榜、车队信息
- **圈速数据**: 详细圈速、分段时间
- **实时数据**: 支持实时遥测数据

**数据来源**: [FastF1 库](https://docs.fastf1.dev/) + Ergast API

### ⚽ 足球数据 (Football-data.org)

- **联赛信息**: 英超、西甲、德甲、意甲、法甲、欧冠等
- **比赛数据**: 实时比分、赛程、历史比赛
- **积分榜**: 各联赛实时积分排名
- **球队信息**: 球队详情、球员名单
- **射手榜**: 各联赛射手排行

**数据来源**: [Football-data.org API](https://docs.football-data.org/general/v4/index.html)

### 🏀 NBA 数据 (NBA API + ESPN)

- **球队信息**: 30 支 NBA 球队完整信息
- **球员数据**: 现役球员、球员统计、生涯数据
- **赛程信息**: 实时赛程、比赛结果
- **积分榜**: 东西部排名
- **比赛统计**: 详细技术统计

**数据来源**: [NBA API](https://github.com/swar/nba_api) + ESPN API

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r backend_requirements.txt
```

### 2. 基础使用

```python
from backend import F1DataAPI, FootballDataAPI, NBADataAPI

# F1 数据
f1_api = F1DataAPI()
schedule = f1_api.get_current_season_schedule()
standings = f1_api.get_driver_standings(2024)

# 足球数据
football_api = FootballDataAPI()
competitions = football_api.get_competitions()
standings = football_api.get_premier_league_standings()

# NBA数据
nba_api = NBADataAPI()
teams = nba_api.get_teams()
standings = nba_api.get_standings()
```

### 3. 运行测试

```bash
python -m backend.test_apis
```

## 📋 API 参考

### F1DataAPI

| 方法                                  | 说明             | 参数                 |
| ------------------------------------- | ---------------- | -------------------- |
| `get_current_season_schedule()`       | 获取当前赛季赛程 | -                    |
| `get_race_results(year, round)`       | 获取比赛结果     | 年份, 轮次           |
| `get_driver_standings(year)`          | 获取车手积分榜   | 年份                 |
| `get_constructor_standings(year)`     | 获取车队积分榜   | 年份                 |
| `get_qualifying_results(year, round)` | 获取排位赛结果   | 年份, 轮次           |
| `get_lap_times(year, round, driver)`  | 获取圈速数据     | 年份, 轮次, 车手代码 |

### FootballDataAPI

| 方法                                           | 说明         | 参数                         |
| ---------------------------------------------- | ------------ | ---------------------------- |
| `get_competitions()`                           | 获取可用联赛 | -                            |
| `get_matches(competition, date_from, date_to)` | 获取比赛列表 | 联赛代码, 开始日期, 结束日期 |
| `get_standings(competition)`                   | 获取积分榜   | 联赛代码                     |
| `get_team_info(team_id)`                       | 获取球队信息 | 球队 ID                      |
| `get_top_scorers(competition)`                 | 获取射手榜   | 联赛代码                     |
| `get_today_matches()`                          | 获取今日比赛 | -                            |

### NBADataAPI

| 方法                                   | 说明                 | 参数                |
| -------------------------------------- | -------------------- | ------------------- |
| `get_teams()`                          | 获取所有球队         | -                   |
| `get_players(team_id, active_only)`    | 获取球员信息         | 球队 ID, 是否仅现役 |
| `get_standings()`                      | 获取积分榜           | -                   |
| `get_schedule(date)`                   | 获取赛程             | 日期                |
| `get_team_schedule(team_id)`           | 获取球队赛程         | ESPN 球队 ID        |
| `get_team_schedule_by_name(team_name)` | 根据名称获取球队赛程 | 球队名称            |
| `get_espn_teams()`                     | 获取 ESPN 球队信息   | -                   |
| `get_all_team_ids()`                   | 获取球队 ID 映射     | -                   |
| `get_player_stats(player_id, season)`  | 获取球员统计         | 球员 ID, 赛季       |
| `get_today_games()`                    | 获取今日比赛         | -                   |

## ⚙️ 配置说明

### API 配置

所有 API 配置都在 `config.py` 中：

```python
API_CONFIG = {
    'FOOTBALL_DATA': {
        'API_TOKEN': 'your_token_here',  # 足球API令牌
        'RATE_LIMIT': 10,  # 每分钟请求限制
    },
    'NBA_API': {
        'RATE_LIMIT': 60,  # 每分钟请求限制
    },
    'F1_API': {
        'CACHE_ENABLED': True,  # 启用缓存
        'CACHE_DIR': 'cache/f1'  # 缓存目录
    }
}
```

### 缓存配置

- **自动缓存**: 所有 GET 请求自动缓存 1 小时
- **智能清理**: 过期缓存自动清理
- **手动控制**: 可手动清空缓存

### 限流配置

- **自动限流**: 根据 API 限制自动控制请求频率
- **智能等待**: 超过限制时自动等待
- **错误重试**: 网络错误自动重试

## 🔧 错误处理

系统内置完善的错误处理机制：

```python
result = api.get_data()
if result['success']:
    data = result['data']
    # 处理数据
else:
    error = result['error']
    # 处理错误
```

## 📝 日志系统

支持详细的日志记录：

```python
import logging
logging.basicConfig(level=logging.INFO)

# 查看详细请求日志
logger = logging.getLogger('backend.football')
logger.setLevel(logging.DEBUG)
```

## 🎯 使用示例

### 获取今日体育赛事

```python
from backend import F1DataAPI, FootballDataAPI, NBADataAPI
from datetime import datetime

def get_today_sports():
    """获取今日所有体育赛事"""
    today = datetime.now().strftime('%Y-%m-%d')

    # F1 赛程
    f1_api = F1DataAPI()
    f1_schedule = f1_api.get_current_season_schedule()

    # 足球比赛
    football_api = FootballDataAPI()
    football_matches = football_api.get_today_matches()

    # NBA比赛
    nba_api = NBADataAPI()
    nba_games = nba_api.get_today_games()

    return {
        'date': today,
        'f1': f1_schedule,
        'football': football_matches,
        'nba': nba_games
    }
```

### 获取积分榜对比

```python
def get_all_standings():
    """获取各项运动积分榜"""

    # F1积分榜
    f1_api = F1DataAPI()
    f1_drivers = f1_api.get_driver_standings(2024)
    f1_constructors = f1_api.get_constructor_standings(2024)

    # 足球积分榜
    football_api = FootballDataAPI()
    premier_league = football_api.get_standings('PL')

    # NBA积分榜
    nba_api = NBADataAPI()
    nba_standings = nba_api.get_standings()

    return {
        'f1': {
            'drivers': f1_drivers,
            'constructors': f1_constructors
        },
        'football': {
            'premier_league': premier_league
        },
        'nba': nba_standings
    }
```

### 获取 NBA 球队赛程

```python
def get_nba_team_schedules():
    """获取NBA球队赛程的多种方式"""

    nba_api = NBADataAPI()

    # 方式1：使用ESPN ID直接查询
    lakers_schedule = nba_api.get_team_schedule(13)  # 湖人队ID是13

    # 方式2：使用球队全名查询
    warriors_schedule = nba_api.get_team_schedule_by_name("Golden State Warriors")

    # 方式3：使用球队缩写查询
    celtics_schedule = nba_api.get_team_schedule_by_name("BOS")

    # 方式4：使用简化名称查询
    heat_schedule = nba_api.get_team_schedule_by_name("heat")

    # 获取所有球队ID映射（用于查找球队ID）
    all_teams = nba_api.get_all_team_ids()

    return {
        'lakers': lakers_schedule,
        'warriors': warriors_schedule,
        'celtics': celtics_schedule,
        'heat': heat_schedule,
        'all_teams': all_teams
    }
```

## 🔍 故障排除

### 常见问题

1. **API 限制超出**

   - 检查 `config.py` 中的限流设置
   - 增加请求间隔时间

2. **缓存问题**

   - 清空缓存: `api.clear_cache()`
   - 禁用缓存: 设置 `use_cache=False`

3. **网络连接问题**

   - 检查网络连接
   - 查看日志中的详细错误信息

4. **依赖包问题**
   - 重新安装: `pip install -r backend_requirements.txt`
   - 检查版本兼容性

### 调试模式

```python
import logging
logging.getLogger('backend').setLevel(logging.DEBUG)

# 查看详细请求信息
api = FootballDataAPI()
result = api.get_competitions()
```

## 📄 许可证

本项目仅供学习和研究使用，请遵守各数据源的使用条款。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
