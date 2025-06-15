#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
体育数据后端模块
包含F1、足球和NBA三个数据源的API接口
"""

__version__ = "1.0.0"
__author__ = "Sports Backend"

# 导入各个模块
from .f1_api import F1DataAPI
from .football_api import FootballDataAPI
from .nba_api import NBADataAPI

__all__ = [
    'F1DataAPI',
    'FootballDataAPI', 
    'NBADataAPI'
] 