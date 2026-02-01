# -*- coding: utf-8 -*-
"""
配置Schema定义 - 数据驱动设计

使用字典定义所有配置参数，格式: 'key': (default_value, '注释')
"""

# ================================================================
# 平台配置（Token、Webhook、Web服务等）
# ================================================================
PLATFORM_SCHEMA = {
    'juejin_token': ('95ead097d57f944ee1415d5a040c578abf9f4dfc', '掘金量化Token'),
    'dingtalk_webhook': ('https://oapi.dingtalk.com/robot/send?access_token=81fba6f35d6e1a22ea45dd881b2ee4c4f9d273d1df168061f2c9502234fc9e81', '钉钉机器人Webhook'),
    'web_host': ('127.0.0.1', 'Web服务地址'),
    'web_port': (8000, 'Web服务端口'),
}

# ================================================================
# 数据库配置
# ================================================================
DATABASE_SCHEMA = {
    'daily_kline': ('./data/duckdb/daily_kline.duckdb', '历史日K线数据库'),
    'stock_meta': ('./data/duckdb/stock_meta.duckdb', '股票元信息数据库'),
    'realtime': ('./data/duckdb/realtime.duckdb', '当日实时数据库'),
    'backtest': ('./data/duckdb/backtest.duckdb', '回测数据库'),
}

# ================================================================
# 股票池配置
# ================================================================
STOCK_POOL_SCHEMA = {
    'markets': (['main', 'gem'], '市场列表 main=主板 gem=创业板'),
    'exclude_st': (True, '排除ST股票'),
    'exclude_suspended': (True, '排除停牌股票'),
}

# ================================================================
# 交易时段配置
# ================================================================
TRADING_HOURS_SCHEMA = {
    'morning_start': ('09:30', '早盘开始'),
    'morning_end': ('11:30', '早盘结束'),
    'afternoon_start': ('13:00', '午盘开始'),
    'afternoon_end': ('15:00', '午盘结束'),
}

# ================================================================
# 技术指标参数
# ================================================================
TECHNICAL_INDICATORS_SCHEMA = {
    'kdj_n': (9, 'KDJ指标N周期'),
    'kdj_m1': (3, 'KDJ指标M1平滑周期'),
    'kdj_m2': (3, 'KDJ指标M2平滑周期'),
    'ma_periods': ([5, 10, 20, 60], '均线周期列表'),
}

# ================================================================
# 特质指标参数（爬虫数据相关）
# ================================================================
SPECIAL_INDICATORS_SCHEMA = {
    'chip_compare_yesterday': (True, '筹码集中度与昨日比较'),
    'main_inflow_rate_min': (0.06, '主力净流入占比最小值 6%'),
}

# ================================================================
# 日常数据阈值
# ================================================================
DAILY_DATA_SCHEMA = {
    'turnover_rate_min': (3.28, '换手率最小值 %'),
    'turnover_rate_max': (25.8, '换手率最大值 %'),
    'turnover_ratio_min': (1.28, '换手率倍数最小值'),
    'turnover_ratio_max': (12.0, '换手率倍数最大值'),
    'turnover_ratio_threshold': (2.5, '隔日换手率阈值'),
    'market_cap_min': (1.6e9, '流通市值最小值 16亿'),
    'market_cap_max': (5.0e10, '流通市值最大值 500亿'),
    'amount_min': (1.68e8, '成交额最小值 1.68亿'),
    'amount_max': (3.668e9, '成交额最大值 36.68亿'),
    'daily_gain_min': (0.04, '当日涨幅最小值 4%'),
    'daily_gain_max': (0.095, '当日涨幅最大值 9.5%'),
    'prev_days_gain_max': (0.11, '前N日涨幅上限 11%'),
    'prev_days_options': ([6, 7], '前N日选项'),
    'big_drop_threshold': (-0.08, '大跌阈值 -8%'),
    'price_vwap_deviation_max': (0.04, '价格偏离均价阈值 4%'),
}

# ================================================================
# 预警条件配置
# ================================================================
CONDITIONS_SCHEMA = {
    'kdj_j_threshold': (98, '条件1: J值上限'),
    'consecutive_j_lt_k_days': (3, '条件2: 连续J<K天数'),
    'consecutive_gain_lt_threshold_days': (5, '条件14: 连续涨幅<阈值天数'),
    'consecutive_gain_threshold': (0.095, '条件14: 涨幅阈值 9.5%'),
    'no_consecutive_yang_days': (4, '条件15: 不能N连阳天数'),
    'big_drop_lookback_days': (10, '条件16: 大跌回溯天数'),
    'upper_shadow_threshold': (0.04, '条件17: 上影线阈值 4%'),
    'upper_shadow_lookback_days': (2, '条件17: 上影线回溯天数'),
    'price_high_lookback_days': (10, '条件12: 价格新高回溯天数'),
}

# ================================================================
# 元信息
# ================================================================
META_SCHEMA = {
    'generated_at': ('', '配置生成时间'),
    'version': ('1.0', '配置版本'),
    'project': ('A股预警系统', '项目名称'),
}

# ================================================================
# 完整Schema（按顺序）
# ================================================================
CONFIG_SCHEMA = {
    'platform': PLATFORM_SCHEMA,
    'database': DATABASE_SCHEMA,
    'stock_pool': STOCK_POOL_SCHEMA,
    'trading_hours': TRADING_HOURS_SCHEMA,
    'technical_indicators': TECHNICAL_INDICATORS_SCHEMA,
    'special_indicators': SPECIAL_INDICATORS_SCHEMA,
    'daily_data': DAILY_DATA_SCHEMA,
    'conditions': CONDITIONS_SCHEMA,
    'meta': META_SCHEMA,
}

# 模块中文名称
SECTION_NAMES = {
    'platform': '平台配置',
    'database': '数据库配置',
    'stock_pool': '股票池配置',
    'trading_hours': '交易时段配置',
    'technical_indicators': '技术指标参数',
    'special_indicators': '特质指标参数',
    'daily_data': '日常数据阈值',
    'conditions': '预警条件配置',
    'meta': '元信息',
}
