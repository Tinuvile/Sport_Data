#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NBA球队ESPN ID映射表
根据ESPN API文档整理的球队ID对照表
"""

# ESPN NBA球队ID映射
# 数据来源: https://blog.csdn.net/i826056899/article/details/145515149
ESPN_TEAM_IDS = {
    # 东部联盟
    'atlanta_hawks': 1,
    'boston_celtics': 2,
    'brooklyn_nets': 17,
    'charlotte_hornets': 30,
    'chicago_bulls': 4,
    'cleveland_cavaliers': 5,
    'detroit_pistons': 8,
    'indiana_pacers': 11,
    'miami_heat': 14,
    'milwaukee_bucks': 15,
    'new_york_knicks': 18,
    'orlando_magic': 19,
    'philadelphia_76ers': 20,
    'toronto_raptors': 28,
    'washington_wizards': 27,
    
    # 西部联盟
    'denver_nuggets': 7,
    'minnesota_timberwolves': 16,
    'oklahoma_city_thunder': 25,
    'portland_trail_blazers': 22,
    'utah_jazz': 26,
    'golden_state_warriors': 9,
    'los_angeles_clippers': 12,
    'los_angeles_lakers': 13,
    'phoenix_suns': 21,
    'sacramento_kings': 23,
    'dallas_mavericks': 6,
    'houston_rockets': 10,
    'memphis_grizzlies': 29,
    'new_orleans_pelicans': 3,
    'san_antonio_spurs': 24
}

# 反向映射：ID到球队名称
ID_TO_TEAM = {v: k for k, v in ESPN_TEAM_IDS.items()}

# 球队全名映射
TEAM_FULL_NAMES = {
    'atlanta_hawks': 'Atlanta Hawks',
    'boston_celtics': 'Boston Celtics',
    'brooklyn_nets': 'Brooklyn Nets',
    'charlotte_hornets': 'Charlotte Hornets',
    'chicago_bulls': 'Chicago Bulls',
    'cleveland_cavaliers': 'Cleveland Cavaliers',
    'detroit_pistons': 'Detroit Pistons',
    'indiana_pacers': 'Indiana Pacers',
    'miami_heat': 'Miami Heat',
    'milwaukee_bucks': 'Milwaukee Bucks',
    'new_york_knicks': 'New York Knicks',
    'orlando_magic': 'Orlando Magic',
    'philadelphia_76ers': 'Philadelphia 76ers',
    'toronto_raptors': 'Toronto Raptors',
    'washington_wizards': 'Washington Wizards',
    'denver_nuggets': 'Denver Nuggets',
    'minnesota_timberwolves': 'Minnesota Timberwolves',
    'oklahoma_city_thunder': 'Oklahoma City Thunder',
    'portland_trail_blazers': 'Portland Trail Blazers',
    'utah_jazz': 'Utah Jazz',
    'golden_state_warriors': 'Golden State Warriors',
    'los_angeles_clippers': 'Los Angeles Clippers',
    'los_angeles_lakers': 'Los Angeles Lakers',
    'phoenix_suns': 'Phoenix Suns',
    'sacramento_kings': 'Sacramento Kings',
    'dallas_mavericks': 'Dallas Mavericks',
    'houston_rockets': 'Houston Rockets',
    'memphis_grizzlies': 'Memphis Grizzlies',
    'new_orleans_pelicans': 'New Orleans Pelicans',
    'san_antonio_spurs': 'San Antonio Spurs'
}

# 球队缩写映射
TEAM_ABBREVIATIONS = {
    'atlanta_hawks': 'ATL',
    'boston_celtics': 'BOS',
    'brooklyn_nets': 'BKN',
    'charlotte_hornets': 'CHA',
    'chicago_bulls': 'CHI',
    'cleveland_cavaliers': 'CLE',
    'detroit_pistons': 'DET',
    'indiana_pacers': 'IND',
    'miami_heat': 'MIA',
    'milwaukee_bucks': 'MIL',
    'new_york_knicks': 'NYK',
    'orlando_magic': 'ORL',
    'philadelphia_76ers': 'PHI',
    'toronto_raptors': 'TOR',
    'washington_wizards': 'WAS',
    'denver_nuggets': 'DEN',
    'minnesota_timberwolves': 'MIN',
    'oklahoma_city_thunder': 'OKC',
    'portland_trail_blazers': 'POR',
    'utah_jazz': 'UTA',
    'golden_state_warriors': 'GSW',
    'los_angeles_clippers': 'LAC',
    'los_angeles_lakers': 'LAL',
    'phoenix_suns': 'PHX',
    'sacramento_kings': 'SAC',
    'dallas_mavericks': 'DAL',
    'houston_rockets': 'HOU',
    'memphis_grizzlies': 'MEM',
    'new_orleans_pelicans': 'NOP',
    'san_antonio_spurs': 'SAS'
}

# 中文球队名称映射
CHINESE_TEAM_NAMES = {
    # 洛杉矶湖人
    '湖人': 'los_angeles_lakers',
    '湖人队': 'los_angeles_lakers',
    '洛杉矶湖人': 'los_angeles_lakers',
    # 金州勇士
    '勇士': 'golden_state_warriors',
    '勇士队': 'golden_state_warriors',
    '金州勇士': 'golden_state_warriors',
    # 波士顿凯尔特人
    '凯尔特人': 'boston_celtics',
    '凯尔特人队': 'boston_celtics',
    '波士顿凯尔特人': 'boston_celtics',
    # 芝加哥公牛
    '公牛': 'chicago_bulls',
    '公牛队': 'chicago_bulls',
    '芝加哥公牛': 'chicago_bulls',
    # 迈阿密热火
    '热火': 'miami_heat',
    '热火队': 'miami_heat',
    '迈阿密热火': 'miami_heat',
    # 圣安东尼奥马刺
    '马刺': 'san_antonio_spurs',
    '马刺队': 'san_antonio_spurs',
    '圣安东尼奥马刺': 'san_antonio_spurs',
    # 休斯顿火箭
    '火箭': 'houston_rockets',
    '火箭队': 'houston_rockets',
    '休斯顿火箭': 'houston_rockets',
    # 俄克拉荷马雷霆
    '雷霆': 'oklahoma_city_thunder',
    '雷霆队': 'oklahoma_city_thunder',
    '俄克拉荷马雷霆': 'oklahoma_city_thunder',
    # 洛杉矶快船
    '快船': 'los_angeles_clippers',
    '快船队': 'los_angeles_clippers',
    '洛杉矶快船': 'los_angeles_clippers',
    # 纽约尼克斯
    '尼克斯': 'new_york_knicks',
    '尼克斯队': 'new_york_knicks',
    '纽约尼克斯': 'new_york_knicks',
    # 布鲁克林篮网
    '篮网': 'brooklyn_nets',
    '篮网队': 'brooklyn_nets',
    '布鲁克林篮网': 'brooklyn_nets',
    # 费城76人
    '76人': 'philadelphia_76ers',
    '76人队': 'philadelphia_76ers',
    '费城76人': 'philadelphia_76ers',
    # 密尔沃基雄鹿
    '雄鹿': 'milwaukee_bucks',
    '雄鹿队': 'milwaukee_bucks',
    '密尔沃基雄鹿': 'milwaukee_bucks',
    # 其他球队
    '太阳': 'phoenix_suns',
    '太阳队': 'phoenix_suns',
    '菲尼克斯太阳': 'phoenix_suns',
    '国王': 'sacramento_kings',
    '国王队': 'sacramento_kings',
    '萨克拉门托国王': 'sacramento_kings',
    '独行侠': 'dallas_mavericks',
    '独行侠队': 'dallas_mavericks',
    '达拉斯独行侠': 'dallas_mavericks',
    '小牛': 'dallas_mavericks',
    '小牛队': 'dallas_mavericks',
    '达拉斯小牛': 'dallas_mavericks',
    '爵士': 'utah_jazz',
    '爵士队': 'utah_jazz',
    '犹他爵士': 'utah_jazz',
    '掘金': 'denver_nuggets',
    '掘金队': 'denver_nuggets',
    '丹佛掘金': 'denver_nuggets',
    '森林狼': 'minnesota_timberwolves',
    '森林狼队': 'minnesota_timberwolves',
    '明尼苏达森林狼': 'minnesota_timberwolves',
    '开拓者': 'portland_trail_blazers',
    '开拓者队': 'portland_trail_blazers',
    '波特兰开拓者': 'portland_trail_blazers',
    '灰熊': 'memphis_grizzlies',
    '灰熊队': 'memphis_grizzlies',
    '孟菲斯灰熊': 'memphis_grizzlies',
    '鹈鹕': 'new_orleans_pelicans',
    '鹈鹕队': 'new_orleans_pelicans',
    '新奥尔良鹈鹕': 'new_orleans_pelicans',
    '老鹰': 'atlanta_hawks',
    '老鹰队': 'atlanta_hawks',
    '亚特兰大老鹰': 'atlanta_hawks',
    '黄蜂': 'charlotte_hornets',
    '黄蜂队': 'charlotte_hornets',
    '夏洛特黄蜂': 'charlotte_hornets',
    '骑士': 'cleveland_cavaliers',
    '骑士队': 'cleveland_cavaliers',
    '克利夫兰骑士': 'cleveland_cavaliers',
    '活塞': 'detroit_pistons',
    '活塞队': 'detroit_pistons',
    '底特律活塞': 'detroit_pistons',
    '步行者': 'indiana_pacers',
    '步行者队': 'indiana_pacers',
    '印第安纳步行者': 'indiana_pacers',
    '魔术': 'orlando_magic',
    '魔术队': 'orlando_magic',
    '奥兰多魔术': 'orlando_magic',
    '猛龙': 'toronto_raptors',
    '猛龙队': 'toronto_raptors',
    '多伦多猛龙': 'toronto_raptors',
    '奇才': 'washington_wizards',
    '奇才队': 'washington_wizards',
    '华盛顿奇才': 'washington_wizards'
}


def get_team_id(team_name: str) -> int:
    """
    根据球队名称获取ESPN ID
    
    Args:
        team_name: 球队名称（支持中文、英文、缩写等多种格式）
        
    Returns:
        ESPN球队ID
    """
    # 首先检查中文名称
    if team_name in CHINESE_TEAM_NAMES:
        team_key = CHINESE_TEAM_NAMES[team_name]
        return ESPN_TEAM_IDS[team_key]
    
    # 转换为小写并替换空格为下划线
    normalized_name = team_name.lower().replace(' ', '_').replace('-', '_')
    
    # 直接查找
    if normalized_name in ESPN_TEAM_IDS:
        return ESPN_TEAM_IDS[normalized_name]
    
    # 通过缩写查找
    for team_key, abbr in TEAM_ABBREVIATIONS.items():
        if team_name.upper() == abbr:
            return ESPN_TEAM_IDS[team_key]
    
    # 通过全名查找
    for team_key, full_name in TEAM_FULL_NAMES.items():
        if team_name.lower() == full_name.lower():
            return ESPN_TEAM_IDS[team_key]
    
    # 模糊匹配英文名称
    team_name_lower = team_name.lower()
    for team_key, full_name in TEAM_FULL_NAMES.items():
        # 检查是否包含球队名称的关键词
        if 'warriors' in team_name_lower and 'warriors' in full_name.lower():
            return ESPN_TEAM_IDS[team_key]
        elif 'lakers' in team_name_lower and 'lakers' in full_name.lower():
            return ESPN_TEAM_IDS[team_key]
        elif 'celtics' in team_name_lower and 'celtics' in full_name.lower():
            return ESPN_TEAM_IDS[team_key]
        # 通用匹配：检查球队名称的最后一个词
        team_words = full_name.lower().split()
        if len(team_words) > 0 and team_words[-1] in team_name_lower:
            return ESPN_TEAM_IDS[team_key]
    
    # 模糊匹配中文名称
    for chinese_name, team_key in CHINESE_TEAM_NAMES.items():
        if chinese_name in team_name_lower or team_name_lower in chinese_name:
            return ESPN_TEAM_IDS[team_key]
    
    raise ValueError(f"未找到球队: {team_name}")


def get_team_name(team_id: int) -> str:
    """
    根据ESPN ID获取球队名称
    
    Args:
        team_id: ESPN球队ID
        
    Returns:
        球队全名
    """
    if team_id in ID_TO_TEAM:
        team_key = ID_TO_TEAM[team_id]
        return TEAM_FULL_NAMES[team_key]
    
    raise ValueError(f"未找到ID为 {team_id} 的球队")


def list_all_teams() -> dict:
    """
    列出所有球队信息
    
    Returns:
        包含所有球队信息的字典
    """
    teams = {}
    for team_key, team_id in ESPN_TEAM_IDS.items():
        teams[team_key] = {
            'espn_id': team_id,
            'full_name': TEAM_FULL_NAMES[team_key],
            'abbreviation': TEAM_ABBREVIATIONS[team_key]
        }
    
    return teams


if __name__ == "__main__":
    # 测试功能
    print("🏀 NBA球队ESPN ID映射表")
    print("=" * 50)
    
    # 显示所有球队
    all_teams = list_all_teams()
    for team_key, info in all_teams.items():
        print(f"{info['full_name']} ({info['abbreviation']}) - ID: {info['espn_id']}")
    
    print("\n" + "=" * 50)
    
    # 测试查找功能
    test_cases = [
        "Los Angeles Lakers",
        "LAL",
        "lakers",
        "Golden State Warriors",
        "GSW"
    ]
    
    for test_case in test_cases:
        try:
            team_id = get_team_id(test_case)
            team_name = get_team_name(team_id)
            print(f"✅ {test_case} -> ID: {team_id} -> {team_name}")
        except ValueError as e:
            print(f"❌ {test_case} -> {e}") 